# -*- coding: utf-8 -*-
import scrapy


class MovieSpiderSpider(scrapy.Spider):
    name = 'movie_spider'
    allowed_domains = ['movie.douban.com']
    start_urls = ['http://movie.douban.com/']

    def parse(self, response):
        pass
