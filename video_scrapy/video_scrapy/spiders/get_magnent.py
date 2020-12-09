# -*- coding: utf-8 -*-
import scrapy
import pymongo
import logging
from video_scrapy.items import MovieItem
from scrapy import Request, Spider
from urllib import parse

# 获取磁力链接
class GetMagnentSpider(scrapy.Spider):
    name = 'get_magnent'
    allowed_domains = ['cn.torrentkitty.app']
    start_urls = ['http://cn.torrentkitty.app/']
    torrentUrl = 'https://zooqle.com/search?q='
    client = pymongo.MongoClient('mongodb://%s:%s@%s:%s/?authSource=%s' %
                                 ('movie', 'newLife2016', '127.0.0.1', '27017', 'movie_system'))
    db = client['movie_system']

    def start_requests(self):
        for item in self.db['movie'].find({"magnent": {"$exists": False}}):
            index = item['title'].find(' ')
            if index == -1:
                searchKey = item['title']
            else:
                searchKey = item['title'][0:index]
            yield Request(url=self.torrentUrl + searchKey, callback=self.parse_movie_magnent, meta={"id": item['id']})

    def parse_movie_magnent(self, response):
        id = response.meta['id']
        trs = response.css(".table-torrents tr:not(:first-child)")
        magnents = []
        for tr in trs:
            title = ''.join(tr.css(".small *::text").getall())
            magnent = tr.css("a[title='Magnet link']::attr(href)").get()
            data = {'title': title,'magnent':magnent}
            magnents.append(data)
        item = MovieItem()
        item['id'] = id
        item['magnent'] = magnents
        yield item
