# -*- coding: utf-8 -*-
import re
import json
import scrapy

from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError, TCPTimedOutError
    
def get_races_urls(file):
    # read file created by racespider
    urls = set()
    races = []
    with open(file, 'r') as f:
        data = [json.loads(line.strip()) for line in f.readlines()]
    for race in data:
        if race:
            root = re.match('(.*).asp', race['website']).group(1)
            race_results_url = f"{root}/results.aspx"
            if race_results_url not in urls:
                races.append({'id': race['id'], 'url': race_results_url})
                urls.add(race_results_url)
    return races

  
class AthleteSpider(scrapy.Spider):
    name = 'athletespider'
    # allowed_domains = ['http://www.ironman.com/events/triathlon-races.aspx']

    custom_settings = {
        'ITEM_PIPELINES' : {
          'scrape_ironman.pipelines.RaceResultsExportPipeline': 300
        }
    }

    @staticmethod
    def _get_details_url_for_bib(i, root_url=None, race_id=None):
        return f"{root_url}&race={race_id}&bidid={i}&detail=1"


    def start_requests(self):
        races = get_races_urls('data/races/races.jl')
        # construct request for each race results page
        all_race_requests = []
        for race in races:
            result_page_request = scrapy.Request(race["url"], callback=self.parse_results,
                                                              errback=self.errback_httpbin)
            result_page_request.meta['race_id'] = race['id']
            all_race_requests.append(result_page_request)
        return all_race_requests


    def parse_results(self, response):
        race_id = response.meta['race_id']

        available_results = response.xpath(
          "//nav[@class='rResultswWrap']//ul[@id='raceResults']//a/@href").getall()
        for result_url in available_results:
            # construct details url for bib=1
            race_date = re.match('.*rd=([0-9]+)', result_url).group(1)
            root_url = result_url.split("#")[0] # in case there is a hash identifier
            details_bib1_url = self._get_details_url_for_bib(1, root_url, race_id)
            details_bib1_request = scrapy.Request(details_bib1_url, callback=self.parse_athlete_details,
                                                                    errback=self.errback_httpbin)
            details_bib1_request.meta['race_id'] = race_id
            details_bib1_request.meta['race_date'] = race_date
            details_bib1_request.meta['current_bib'] = 1
            details_bib1_request.meta['blanks_count'] = 0

            yield details_bib1_request

    def parse_athlete_details(self, response):
        race_id = response.meta['race_id']
        race_date = response.meta['race_date']
        current_bib = response.meta['current_bib']
        blanks_count = response.meta['blanks_count']

        athlete = {
          'item_category': 'result_entry',
          'race_id': race_id,
          'race_date': race_date
        }
        
        result_content = response.xpath("//div[contains(@class, 'resultsListingDetails')]")
        
        # name
        name = result_content.xpath(".//header/h1/text()").get()
        athlete['name'] = name

        # continue only if there is a name
        if not name or name == '':
            # increase blank count
            blanks_count += 1
            # stop if no info for bibs for more than 120 bibs in a row
            if blanks_count >= 120:
                return {
                    'item_category': 'crawl_end',
                    'race_id': race_id,
                    'race_date': race_date,
                    'current_bib': current_bib
                }
            else:
                # try next bib
                next_bib = current_bib + 1
                details_next_bib_url = re.sub('id=[0-9]+&detail', f'id={next_bib}&detail', response.url)
                details_next_bib_request = scrapy.Request( details_next_bib_url, 
                                                           callback=self.parse_athlete_details,
                                                           errback=self.errback_httpbin)
                details_next_bib_request.meta['race_id'] = race_id
                details_next_bib_request.meta['race_date'] = race_date
                details_next_bib_request.meta['current_bib'] = next_bib
                details_next_bib_request.meta['blanks_count'] = blanks_count
                yield details_next_bib_request
        else:
            # reset blanks count
            blanks_count = 0

            ranks = result_content.xpath(".//header/div/descendant::*/text()").getall()
            for i in range(int(len(ranks)/2)):
                athlete[ranks[i*2].lower().replace(' ', '')] = ranks[i*2+1] if ranks[i*2+1] and '---' not in ranks[i*2+1] else None

            # race summary
            summary = result_content.xpath(".//table[@id='athelete-details']")
            times = summary.xpath('.//tbody/tr/descendant::*/text()').getall()
            for i in range(int(len(times)/2)):
                athlete[f"time_{times[i*2].lower()}"] = times[i*2+1] if times[i*2+1] and '---' not in times[i*2+1] else None

            # add general info
            general_info_table_rows = result_content.xpath(".//table[@id='general-info']/tbody/tr")
            for row in general_info_table_rows:
                # bib / division / age / state / country / profession / points
                [key, val] = row.xpath("./descendant::*/text()").getall()
                val = val if val and '---' not in val else None
                athlete[key.lower()] = val

            # add splits details
            detail_tables = result_content.xpath(".//div[@class='athlete-table-details']/table")
            swim_table, bike_table, run_table, transition_table = detail_tables
            for sport,table in zip( ['swim', 'bike', 'run'], 
                                    [swim_table, bike_table, run_table]):
                columns = map( lambda x: x.lower().replace(" ", "_"), 
                               table.xpath('.//thead//tr/descendant::*/text()').getall())
                # ['Split Name', 'Distance', 'Split Time', 'Pace', 'Division Rank', 'Gender Rank', 'Overall Rank']
                values = map( lambda x: x if x and '---' not in x else None, 
                              table.xpath('.//tfoot//td/descendant::*/text()').getall())
                #['Total', '1.9 km', '00:28:35', '00:28:35', '01:28/100m', '62', '364', '364']
                athlete[f"{sport}_details"] = {
                  key: val if val and '---' not in val else None for key,val in zip(columns, values)
                }

            athlete["transition_details"] = {}
            for row in transition_table.xpath(".//tr"):
                key,val = row.xpath("./descendant::*/text()").getall()
                # ['T1: Swim-to-bike', '00:03:03']
                # ['T2: Bike-to-run', '00:02:52']
                athlete["transition_details"][key] = val if val and '---' not in val else None

            yield athlete   

            # go to next athlete
            next_bib = int(athlete['bib']) + 1
            details_next_bib_url = re.sub('id=[0-9]+&detail', f'id={next_bib}&detail', response.url)
            details_next_bib_request = scrapy.Request(details_next_bib_url, callback=self.parse_athlete_details,
                                                                            errback=self.errback_httpbin)
            details_next_bib_request.meta['race_id'] = race_id
            details_next_bib_request.meta['race_date'] = race_date
            details_next_bib_request.meta['current_bib'] = next_bib
            details_next_bib_request.meta['blanks_count'] = blanks_count

            yield details_next_bib_request

    def errback_httpbin(self, failure):
        # log all failures
        filename = 'errors.txt'
        with open(filename, 'w') as f:
            f.write("------------------")
            f.write(f'Error : {repr(failure)}\n')

        # in case you want to do something special for some errors,
        # you may need the failure's type:

        if failure.check(HttpError):
            # these exceptions come from HttpError spider middleware
            # you can get the non-200 response
            response = failure.value.response
            with open(filename, 'w') as f:
                f.write(f'HttpError on : {response.url}\n')

        elif failure.check(DNSLookupError):
            # this is the original request
            request = failure.request
            with open(filename, 'w') as f:
                f.write(f'DNSLookupError on : {request.url}\n')

        elif failure.check(TimeoutError, TCPTimedOutError):
            request = failure.request
            with open(filename, 'w') as f:
                f.write(f'TimeoutError on : {request.url}\n')       


              
            
            




