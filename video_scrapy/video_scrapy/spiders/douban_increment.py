# -*- coding: utf-8 -*-
import scrapy
import pymongo
from scrapy import Request, Spider
from video_scrapy.items import MovieItem, DoubanCelebrityItem
import json
import logging
import urllib.parse as urlparse
import urllib
import re

# 豆瓣增量爬取
class DoubanIncrementSpider(scrapy.Spider):
    name = 'douban_increment'
    allowed_domains = ['douban.com']
    movieLimit = 100
    startUrl = 'https://movie.douban.com/explore'
    tags = [
        '最新']
    client = pymongo.MongoClient('mongodb://%s:%s@%s:%s/?authSource=%s' %
                                 ('movie', 'newLife2016', '8.129.178.143', '27017', 'movie_system'))
    db = client['movie_system']

    def start_requests(self):
        # 通过 最新 标签
        for tag in self.tags:
            movieUrl = 'https://movie.douban.com/j/search_subjects?type=movie&tag=%s&page_limit=%s&page_start=0' % (
                tag, self.movieLimit)
            yield Request(url=movieUrl, callback=self.parse_movie_url)

    def parse_movie_url(self, response):
        # 加载成dict格式
        data = json.loads(response.text)
        if "subjects" not in data:
            logging.debug("data不存在")
            logging.debug(data)
        # 获取subjects
        subjects = data["subjects"]
        # 遍历
        for subject in subjects:
            # 过滤掉空值
            subject = dict(filter(lambda x: x[1]!='', subject.items()))
            # 构建item
            item = MovieItem()
            item['title'] = subject['title']
            item['cover'] = subject['cover']
            item['rate'] = subject.get('rate', 0)
            item['url'] = subject['url']
            item['id'] = int(subject['id'])
            count = self.db['movie'].count_documents({"id": int(item['id'])})
            # 数据库存在进行下一条
            if count != 0:
                logging.debug("数据库存在%s" % (item['id']))
                continue
            yield item
            # 获取演员表
            yield Request(url=urllib.parse.urljoin(item['url'] + '/', "celebrities"), callback=self.parse_movie_celebrities, meta={"id": item['id']})
            # 简单选择关键字
            index = item['title'].find(' ')
            if index == -1:
                searchKey = item['title']
            else:
                searchKey = item['title'][0:index]
            torrentUrl = 'https://zooqle.com/search?q='
            # 获取种子
            yield Request(url=torrentUrl + searchKey, callback=self.parse_movie_magnent, meta={"id": item['id']})

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

    # 获取种子
    def parse_movie_magnent(self, response):
        id = response.meta['id']
        trs = response.css(".table-torrents tr:not(:first-child)")
        magnents = []
        if trs:
            trs = trs[0:10]
            for tr in trs:
                title = ''.join(tr.css(".small *::text").getall())
                magnent = tr.css("a[title='Magnet link']::attr(href)").get()
                data = {'title': title,'magnent':magnent}
                magnents.append(data)
        item = MovieItem()
        item['id'] = id
        item['magnent'] = magnents
        yield item
