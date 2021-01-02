# -*- coding: utf-8 -*-
import scrapy
import pymongo
import logging
from scrapy.utils.project import get_project_settings
from video_scrapy.items import MovieItem, DoubanCelebrityItem
from scrapy import Request, Spider
from urllib import parse
import re

class DoubanParseCelebritiesSpider(scrapy.Spider):
    name = 'douban_parse_celebrities'
    allowed_domains = ['douban.com']
    client = pymongo.MongoClient('mongodb://%s:%s@%s:%s/?authSource=%s' %
                                 ('movie', 'newLife2016', '8.129.178.143', '27017', 'movie_system'))
    db = client['movie_system']

    def start_requests(self):
        for item in self.db['movie'].find({"actors": {"$exists": False}}):
            yield Request(url=parse.urljoin(item['url'], "celebrities"), callback=self.parse_movie_celebrities, meta={"id": item['id']})



    # 解析演员饰演角色
    def parse_movie_celebrities(self, response):
        id = response.meta['id']
        lis = response.css("#celebrities li.celebrity")
        actors = []
        for li in lis:
            style = li.css(".avatar::attr(style)").get()
            avatar = re.search(re.compile(r'url\((.*)\)'), style).group(1)
            namea = li.css(".info a.name")
            name = namea.attrib['title']
            name = name.replace('.', '-')
            url = namea.attrib['href']
            cid = re.search(re.compile(r'celebrity/(\d+).*'), url).group(1)
            doubanCelebrityItem = DoubanCelebrityItem()
            doubanCelebrityItem['avatar'] = avatar
            doubanCelebrityItem['name'] = name
            doubanCelebrityItem['url'] = url
            doubanCelebrityItem['id'] = cid
            # 存储演员
            yield doubanCelebrityItem
            role = li.css(".role::text").get()
            if role:
                role = role.replace('.', '-')
            actors.append({
                "id": cid,
                "name": name,
                "role": role
            })
        item = MovieItem()
        item['id'] = id
        item['actors'] = actors
        yield item
