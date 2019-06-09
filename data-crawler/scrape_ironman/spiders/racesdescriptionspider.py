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

fileSources = [
    'data/races/races.jl',
    './../data/races/ironMan-active-races.json'
]

def get_races_urls(fileSources, selection=None):
    # read file created by racespider
    urls = set()
    races = []
    for file in fileSources:
        with open(file, 'r') as f:
            data = [json.loads(line.strip()) for line in f.readlines()]
        for race in data:
            if race:
                if selection:
                    if not any(race_id.lower() in race['id'].lower() for race_id in map(lambda x: x['id'], selection)):
                        continue
                race_url = race.get('website', False)
                if not race_url:
                    race_url = race.get('url', False)
                if race_url and race_url not in urls:
                    race_id = race.get('id', "TBD")
                    race_region = race.get('region', "TBD")
                    races.append({'id': race_id, 'name': race['name'], 'location': race['location'], 'url': race_url, 'region': race_region})
                    urls.add(race_url)
    return races

  
class RacesDescriptionSpider(scrapy.Spider):
    name = 'racesdescriptionspider'

    custom_settings = {
        'ITEM_PIPELINES' : {
          'scrape_ironman.pipelines.RaceResultsExportPipeline': 300
        }
    }

    @staticmethod
    def get_description_from_page(response):
        container = response.xpath("//div[contains(@class, 'eventDescription')]")
        all_text = container.xpath('.//text()').getall()
        description = re.sub("\s+", " ", " ".join(all_text).strip())
        return description

    def start_requests(self):
        ''' 
        From race name, infer url for race results page and navigate there
        '''
        races = get_races_urls(fileSources, race_selection)

        # construct request for each race results page
        all_race_requests = []
        for race in races:
            result_page_request = scrapy.Request(race["url"], callback=self.parse_results,
                                                              errback=self.errback_httpbin)
            result_page_request.meta.update({
                'race_id': race['id'],
                'race_name': race['name'],
                'race_region': race['region'],
                'race_location': race['location']
            })
            all_race_requests.append(result_page_request)
        return all_race_requests


    def parse_results(self, response):
        ''' 
        Parse all the years (results) available for this specific race.
        Create a request for each year available.
        '''
        race_id = response.meta['race_id']
        race_name = response.meta['race_name']
        race_region = response.meta['race_region']
        race_location = response.meta['race_location']

        description = self.get_description_from_page(response)

        yield {
            'item_category': 'race_description',
            'race_id': race_id,
            'race_name': race_name,
            'race_region': race_region,
            'race_location': race_location,
            'description': description
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


              
            
            




