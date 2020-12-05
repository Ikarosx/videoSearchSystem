# -*- coding: utf-8 -*-
import scrapy
from scrapy import Request, Spider
import logging
class TestSpider(scrapy.Spider):
    name = 'test'
    allowed_domains = ['baidu.com']
    start_urls = ['https://www.baidu.com']

    def parse(self, response):
        aas = response.css("a::attr(href)").getall()
        for aa in aas:
            if  aa.startswith("http"):
                yield Request(url=aa, callback=self.parse)
