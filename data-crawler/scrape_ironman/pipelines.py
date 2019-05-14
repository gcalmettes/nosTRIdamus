# -*- coding: utf-8 -*-
import os
import re
from scrapy.exporters import JsonLinesItemExporter

# folders where to save
config = {
    "race_folder": "data/races",
    "result_folder": "data/results" 
}

# create folders if they don't exist
for folder in config.values():
    os.makedirs(folder, exist_ok=True)

class RaceResultsExportPipeline(object):
    """Distribute items across multiple json files according to their 'category' field"""

    def open_spider(self, spider):
        # keep track of all the files created
        self.all_exporters = {}

    def close_spider(self, spider):
        for exporter in self.all_exporters.values():
            exporter.finish_exporting()
            exporter.file.close()

    @staticmethod
    def get_exporter_key_for_item(item):
        category = item['item_category']
        if category == 'race_info':
            file = f'{config["race_folder"]}/races.jl'
        elif category == 'athletes_count':
            file = f'{config["race_folder"]}/races-athletes-count.jl'
        elif category == 'result_entry':
            race_id = item['race_id']
            race_date = item['race_date']
            file = f'{config["result_folder"]}/{race_id}_{race_date}.jl'
        else:
            raise Error("The received item doesn't have a valid category")
        return file

    def get_exporter_for_item(self, item, hasDate=False):
        file = self.get_exporter_key_for_item(item)
        if file not in self.all_exporters:
            f = open(file, 'wb')
            exporter = JsonLinesItemExporter(f)
            exporter.start_exporting()
            self.all_exporters[file] = exporter
            if hasDate:
                print(f'----- Starting crawling process for {item["race_id"]} ({item["race_date"]})')
        return self.all_exporters[file]

    def format_item(self, item):
      category = item['item_category']
      if category == 'race_info':
          try:
              month,day,year = item['date'].split(' ')
              day = re.search('(\d+)', day).group(1)
          except:
              month = day = year = None
          try:
              if 'inactive' not in item['website']:
                  root,region,race_type,iron_name = re.match(
                      '(.*)/(.*)/(.*)/(.*).asp', item['website']).groups()
              else:
                  root,region,race_type,iron_name = re.match(
                      '(.*)/(.*)/(.*)/inactive/(.*).asp', item['website']).groups()
          except:
              race_type = region = None
          formatted_item = {
              'id': item['race_id'],
              'name': item['name'],
              'type': race_type,
              'region': region,
              'date': item['date'],
              'day': day,
              'month': month,
              'year': year,
              'location': item['location'],
              'website': item['website'],
              'img_url': item['images'][0]['url'],
              'img_path': item['images'][0]['path']
          }

      elif category == 'result_entry':
          formatted_item = {
              key: val for key,val in item.items() 
                  if key not in ['item_category', 'race_id', 'race_date']
          }
      elif category == 'athletes_count':
          race_id = item['race_id']
          race_date = item['race_date']
          count = item['count']
          race_region = item['race_region']
          formatted_item = {
            'id': race_id,
            'date': race_date,
            'region': race_region,
            'count': count
          }

      return formatted_item

    def process_item(self, item, spider):

        if item and item.get('item_category') == 'crawl_end':
            file = self.get_exporter_key_for_item({
              'item_category': 'result_entry',
              'race_id': item['race_id'],
              'race_date': item['race_date']
              })
            # close associated exporter
            exporter_to_close = self.all_exporters.get(file)
            if exporter_to_close:
                exporter_to_close.finish_exporting()
                exporter_to_close.file.close()
                # remove exporter from active exporters
                del self.all_exporters[file]
                print(f'===> Crawling for {item["race_id"]} stopped at bib {item["current_bib"]} ({item["status"]}).')
                print(f'==========> File {file} was closed.')
            else:
                print(f'===> Crawling for {item["race_id"]} stopped at bib {item["current_bib"]} ({item["status"]}).')

        else:
            if item.get('item_category') == 'result_entry':
                exporter= self.get_exporter_for_item(item, hasDate=True)
            else:
                exporter= self.get_exporter_for_item(item, hasDate=False)
            formatted_item = self.format_item(item)
            exporter.export_item(formatted_item)

        return #item

