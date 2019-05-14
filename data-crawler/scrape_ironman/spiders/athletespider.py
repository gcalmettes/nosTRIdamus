# -*- coding: utf-8 -*-
import re
import scrapy

from .athletescountspider import AthletesCountSpider

  
class AthleteSpider(AthletesCountSpider):
    name = 'athletespider'

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
            ################################################
            # ADDITION TO AthletesCountSpider 
            # => go on with parsing athletes details
            ################################################
            details_bib1_request = scrapy.Request(details_bib1_url, callback=self.parse_athlete_details,
                                                                    errback=self.errback_httpbin)
            details_bib1_request.meta.update({
                'race_id': race_id,
                'race_date': race_date,
                'n_athletes_total': athletes_count,
                'n_athletes_scraped': 0,
                'current_bib': 1,
                'blanks_count': 0
            })
            yield details_bib1_request


    def parse_athlete_details(self, response):
        race_id = response.meta['race_id']
        race_date = response.meta['race_date']
        current_bib = response.meta['current_bib']
        blanks_count = response.meta['blanks_count']
        n_athletes_total = response.meta['n_athletes_total']
        n_athletes_scraped = response.meta['n_athletes_scraped']

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
            # safeguard if n_athletes_count is wrong:
            # stop if no info for bibs for more than 5000 bibs in a row
            if blanks_count >= 3500:
                yield {
                    'item_category': 'crawl_end',
                    'race_id': race_id,
                    'race_date': race_date,
                    'current_bib': current_bib,
                    'status': 'REACHED BLANKS LIMIT'
                }
            else:
                # try next bib
                next_bib = current_bib + 1
                details_next_bib_url = re.sub('id=[0-9]+&detail', f'id={next_bib}&detail', response.url)
                details_next_bib_request = scrapy.Request( details_next_bib_url, 
                                                           callback=self.parse_athlete_details,
                                                           errback=self.errback_httpbin)

                details_next_bib_request.meta.update({
                    'race_id': race_id,
                    'race_date': race_date,
                    'n_athletes_total': n_athletes_total,
                    'n_athletes_scraped': n_athletes_scraped,
                    'current_bib': next_bib,
                    'blanks_count': blanks_count
                })
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

            # Update number of athletes scraped
            n_athletes_scraped += 1  

            if n_athletes_scraped >= n_athletes_total:
                yield {
                    'item_category': 'crawl_end',
                    'race_id': race_id,
                    'race_date': race_date,
                    'current_bib': current_bib,
                    'status': 'FINISHED'
                }
            else:
                # go to next athlete
                next_bib = int(athlete['bib']) + 1
                details_next_bib_url = re.sub('id=[0-9]+&detail', f'id={next_bib}&detail', response.url)
                details_next_bib_request = scrapy.Request(details_next_bib_url, callback=self.parse_athlete_details,
                                                                                errback=self.errback_httpbin)
                details_next_bib_request.meta.update({
                    'race_id': race_id,
                    'race_date': race_date,
                    'n_athletes_total': n_athletes_total,
                    'n_athletes_scraped': n_athletes_scraped,
                    'current_bib': next_bib,
                    'blanks_count': blanks_count
                })
                yield details_next_bib_request
            
            




