# -*- coding: utf-8 -*-
import scrapy
import pymongo
from scrapy import Request, Spider
from video_scrapy.items import MovieItem
import json
import logging
import urllib.parse as urlparse
import urllib

class InitUrlStageOneSpider(scrapy.Spider):
    name = 'init_url_stage_one'
    allowed_domains = ['douban.com']
    start_urls = ['http://douban.com/']
    movieLimit = 100
    startUrl = 'https://movie.douban.com/explore'
    tags = ['热门',
            '最新',
            '经典',
            '可播放',
            '豆瓣高分',
            '冷门佳片',
            '华语',
            '欧美',
            '韩国',
            '日本',
            '动作',
            '喜剧',
            '爱情',
            '科幻',
            '悬疑',
            '恐怖',
            '文艺',
            '美剧', '英剧', '韩剧', '日剧', '国产剧', '港剧', '日本动画',
            '综艺', '纪录片', '短片', '电影', '电视剧', '动漫']
    # 从2000到2021每一年单独一个标签
    yearTags = [str(x) + ',' + str(x) for x in range(2000, 2022)]
    # 从1900到2000每10年一个标签
    tenYearTags = [str(x * 10) + ',' + str(x * 10 + 10)
                   for x in range(190, 200)]
    client = pymongo.MongoClient('mongodb://%s:%s@%s:%s/?authSource=%s' %
                                 ('movie', 'newLife2016', '8.129.178.143', '27017', 'movie_system'))
    db = client['movie_system']

    # 阶段一通过更多链接
    def start_requests(self):
        # 通过普通标签
        for tag in self.tags:
            movieUrl = 'https://movie.douban.com/j/new_search_subjects?tags=%s&sort=&limit=%s&start=0' % (
                tag, self.movieLimit)
            yield Request(url=movieUrl, callback=self.parse_movie_url)
        # 通过年份标签
        for tag in self.yearTags + self.tenYearTags:
            movieUrl = 'https://movie.douban.com/j/new_search_subjects?limit=%s&start=0&year_range=%s' % (
                 self.movieLimit,tag)
            yield Request(url=movieUrl, callback=self.parse_movie_url)

    # 通过加载更多进入
    def parse_movie_url(self, response):
        # 加载成dict格式
        data = json.loads(response.text)
        if "data" not in data:
            logging.debug("data不存在")
            logging.debug(data)
        # 获取subjects
        subjects = data["data"]
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
            item['id'] = subject['id']
            count = self.db['movie'].count_documents({"id": int(item['id'])})
            # 数据库存在进行下一条
            if count != 0:
                logging.debug("数据库存在%s" % (item['id']))
                continue
            yield item

        # 已经最后一页了
        if len(subjects) == self.movieLimit:
            # 更新pageStart
            parseResult = urlparse.urlparse(response.url)
            querys = urlparse.parse_qs(parseResult.query)
            querys['start'] = [
                str(int(querys['start'][0]) + self.movieLimit)]
            querys = {k: v[0] for k, v in querys.items()}
            querys = urllib.parse.urlencode(querys)
            requestUrl = parseResult.scheme + "://" + \
                parseResult.netloc + parseResult.path + "?" + querys
            yield Request(url=requestUrl, callback=self.parse_movie_url)
