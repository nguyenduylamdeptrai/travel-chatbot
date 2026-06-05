# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class TravelItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class TourismItem(scrapy.Item):
    name = scrapy.Field(default=None)
    address = scrapy.Field(default=None)
    content = scrapy.Field(default=None)
    url = scrapy.Field(default=None)