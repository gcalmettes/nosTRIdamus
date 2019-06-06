# -*- coding: utf-8 -*-
import scrapy

class RacesSpider(scrapy.Spider):
    name = 'racespider'
    
    # allowed_domains = ['http://www.ironman.com/events/triathlon-races.aspx']
    start_urls = ['http://www.ironman.com/triathlon/coverage/past.aspx']

    custom_settings = {
        'ITEM_PIPELINES' : {
          'scrapy.pipelines.images.ImagesPipeline': 1,
          'scrape_ironman.pipelines.RaceResultsExportPipeline': 300
        },
        'IMAGES_STORE' : 'data/races/images/'
    }

    def parse(self, response):
        # parse all races
        all_races = response.xpath("//article")
        for race in all_races:
            race_title = race.xpath(".//header/a/h3/text()").get()
            
            # make sure this is an ironman or 70.3 race
            if 'IRONMAN' not in race_title:
                continue

            race_id = race.xpath(".//header/a/@href").re('race=(.+)&y=')
            race_id = race_id[0] if len(race_id)>0 else race_title.lower().replace(' ', '')

            # Exceptions:
            # Cozumel: race id is different than name!
            if race_id == 'cozumel70.3':
                race_id = 'cancun70.3'
            # Jönköping: race id is different than name!
            if race_id =='J\u00f6nk\u00f6ping':
                race_id = 'joenkoeping70.3'

            # extract some features
            cal,date,loc,city = race.xpath(".//ul/li/descendant::*/text()").getall()

            race_info = {
              'item_category': 'race_info',
              'race_id': race_id,
              'name': race_title,
              'date': date,
              'location': city,
              'website': race.xpath(".//a[@class='siteLink']/@href").get(),
              'image_urls': [race.xpath('.//img/@src').get(' ? ').split('?')[0]]
            }

            yield race_info

            next_page = response.xpath("//a[@class='nextPage' and @title='Next']/@href").get()
            if next_page is not None:
                yield response.follow(next_page, self.parse)
