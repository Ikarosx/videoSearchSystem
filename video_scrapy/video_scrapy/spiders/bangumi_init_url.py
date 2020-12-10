# -*- coding: utf-8 -*-
import scrapy
import pymongo
from scrapy import Request, Spider
from video_scrapy.items import BangumiItem
import json
import logging
import urllib.parse as urlparse
import urllib
import re
class BangumiInitUrlSpider(scrapy.Spider):
    name = 'bangumi_init_url'
    allowed_domains = ['bgm.tv']
    start_urls = ['http://bgm.tv/anime/browser/?page=1']

    # 阶段一通过更多链接
    def start_requests(self):
        for index in range(1,724):
            url = "http://bgm.tv/anime/browser/?page=%s" %(index)
            yield Request(url=url, callback=self.parse_index)

    def parse_index(self, response):
        lis = response.css("#browserItemList li")
        for li in lis:
            cover = li.css(".image .cover::attr(src)").get()
            if cover:
                cover = 'http' + cover
            title = li.css(".inner .l::text").get()
            href = li.css(".inner .l::attr(href)").get()
            japanTitle = li.css('.grey::text').get()
            id = re.search(re.compile(r'subject/(\d+).*'), href).group(1)
            if not japanTitle:
                # 如果grey类找不到，说明title为日文标题，那么japan等于他即可，
                japanTitle = title
            url = urllib.parse.urljoin(response.url, href)
            
            item = BangumiItem()
            item['url'] = url
            item['rate'] = li.css(".rateInfo .fade::text").get()
            item['id'] = id
            item['japanTitle'] = japanTitle
            item['title'] = title
            item['cover'] = cover
            yield item
        


    
