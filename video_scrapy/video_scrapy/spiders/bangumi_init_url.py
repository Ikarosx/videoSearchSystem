# -*- coding: utf-8 -*-
import scrapy


class BangumiInitUrlSpider(scrapy.Spider):
    name = 'bangumi_init_url'
    allowed_domains = ['bgm.tv']
    start_urls = ['http://http://bgm.tv/anime/browser/?page=1/']

    def parse(self, response):
        
        pass
