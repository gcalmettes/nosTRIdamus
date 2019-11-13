# -*- coding: utf-8 -*-
import re
import json
import scrapy

from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError, TCPTimedOutError

# use to select only specific races.
# if no selection, still declare the global variable as it is used for conditional filtering in parse_results.
race_selection = None
# race_selection = [
#   { "id": "monterrey70.3", "years": ["2018"] },
#   { "id": "austria70.3", "years": ["2018"] },
#   { "id": "australia", "years": ["2015", "2016", "2017", "2018", "2019"] },
#   { "id": "coquimbo70.3", "years": ["2017"] },
#   { "id": "uk", "years": ["2013"] },
#   { "id": "monttremblant70.3", "years": ["2018"] },
#   { "id": "lakeplacid", "years": ["2005"] },
#   { "id": "branson70.3", "years": ["2010"] },
#   { "id": "branson70.3", "years": ["2010"] },
#   { "id": "regensburg", "years": ["2012"] },
#   { "id": "austria70.3", "years": ["2018"] },
#   { "id": "canada70.3", "years": ["2018"] },
# ]
    
def get_races_urls(file, selection=None):
    # read file created by racespider
    urls = set()
    races = []
    with open(file, 'r') as f:
        data = [json.loads(line.strip()) for line in f.readlines()]
    for race in data:
        if race:
            if selection:
                if not any(race_id.lower() in race['id'].lower() for race_id in map(lambda x: x['id'], selection)):
                    continue
            root = re.match('(.*).asp', race['website']).group(1)
            race_results_url = f"{root}/results.aspx"
            if race_results_url not in urls:
                races.append({'id': race['id'], 'url': race_results_url, 'region': race['region']})
                urls.add(race_results_url)
    if not selection:
        # add world championship 70.3 (to also get female results)
        races.append({'id': 'worldchampionship70.3', 'region': 'americas' , 'url': 'http://www.ironman.com/triathlon/events/americas/ironman-70.3/70.3-world-championship-womens-race/results.aspx'})
    return races

  
class AthletesCountSpider(scrapy.Spider):
    name = 'athletescountspider'

    custom_settings = {
        'ITEM_PIPELINES' : {
          'scrape_ironman.pipelines.RaceResultsExportPipeline': 300
        }
    }

    @staticmethod
    def _get_details_url_for_bib(i, root_url=None, race_id=None):
        return f"{root_url}&race={race_id}&bidid={i}&detail=1"

    @staticmethod
    def get_athletes_count_from_page(response):
        # check if number of athletes is present
        athletes_count = response.xpath(
            "//div[@class='results-athletes-table']/h2/span/text()").get()
        n = None
        if athletes_count:
            count = re.match("\(([\d,]+)", athletes_count)
            n = int(count.groups()[0].replace(',',''))
        return n


    def start_requests(self):
        ''' 
        From race name, infer url for race results page and navigate there
        '''
        races = get_races_urls('data/races/races.jl', race_selection)

        # construct request for each race results page
        all_race_requests = []
        for race in races:
            result_page_request = scrapy.Request(race["url"], callback=self.parse_results,
                                                              errback=self.errback_httpbin)
            result_page_request.meta.update({
                'race_id': race['id'],
                'race_region': race['region']
            })
            all_race_requests.append(result_page_request)
        return all_race_requests


    def parse_results(self, response):
        ''' 
        Parse all the years (results) available for this specific race.
        Create a request for each year available.
        '''
        race_id = response.meta['race_id']
        race_region = response.meta['race_region']

        available_results = response.xpath(
          "//nav[@class='rResultswWrap']//ul[@id='raceResults']//a/@href").getall()

        if len(available_results) > 0 :
            for result_url in available_results:
                # create request to parse athlete count
                request_results = scrapy.Request(result_url, callback=self.parse_athletes_count,
                                                             errback=self.errback_httpbin)
                # infer url for details request of bib 1
                race_date = re.match('.*rd=([0-9]+)', result_url).group(1)

                # if we work only on selection of races
                if race_selection:
                    race_selected = list(filter(lambda x: x["id"].lower() == race_id.lower() , race_selection))
                    # make sure there is actually some data
                    if not len(race_selected)>0:
                        continue
                    selected_years = race_selected[0]["years"]
                    # filter by year if years selection is given
                    if len(selected_years) != 0:
                        if not any(year in race_date for year in selected_years):
                            continue

                root_url = result_url.split("#")[0] # in case there is a hash identifier
                details_bib1_url = self._get_details_url_for_bib(0, root_url, race_id)

                request_results.meta.update({
                    'race_id': race_id,
                    'race_region': race_region,
                    'race_date': race_date,
                    'details_bib1_url': details_bib1_url
                })
                yield request_results
      
        else:
          # if only 1 year of results, then there probably won't be a race listing and we are
          # already on a page result. 
          # Check if there is a table results with rows, and if so then get number of
          # athletes and start scraping by infering result_url from first row
          result_table = response.xpath(
              "//div[@class='results-athletes-table']/table[@id='eventResults']")
          if result_table:
              rows = result_table.xpath(".//tbody/tr")
              if len(rows)>5: # could be >0 here, but >5 won't hurt since page can get up to 15 results
                  # get race date and id from link of first finisher
                  url = rows[0].xpath(".//td/a/@href").get()
                  result_url = f"{response.url}{url.split('&race')[0]}"
                  race_date = re.match('.*rd=([0-9]+)', result_url).group(1)
                  details_bib1_url = self._get_details_url_for_bib(0, result_url, race_id)
                  request_results = scrapy.Request(result_url, callback=self.parse_athletes_count,
                                                               errback=self.errback_httpbin)
                  request_results.meta.update({
                      'race_id': race_id,
                      'race_region': race_region,
                      'race_date': race_date,
                      'details_bib1_url': details_bib1_url
                  })
                  yield request_results

    def parse_athletes_count(self, response):
        race_id = response.meta['race_id']
        race_date = response.meta['race_date']
        race_region = response.meta['race_region']
        details_bib1_url = response.meta['details_bib1_url']

        # check if number of athletes is present
        athletes_count = self.get_athletes_count_from_page(response)
        if athletes_count:
            yield {
                'item_category': 'athletes_count',
                'race_id': race_id,
                'race_region': race_region,
                'race_date': race_date,
                'count': athletes_count
            }

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


              
            
            




