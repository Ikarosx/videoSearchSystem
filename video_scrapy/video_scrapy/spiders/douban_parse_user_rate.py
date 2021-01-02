# -*- coding: utf-8 -*-
import scrapy
import pymongo
import logging
from video_scrapy.items import DoubanUserItem, DoubanRateRelationItem
from scrapy import Request, Spider
from urllib import parse
import re
import json
from scrapy.utils.project import get_project_settings
from scrapy.selector import Selector
import datetime
import urllib.parse as urlparse
import urllib

class DoubanParseUserRateSpider(scrapy.Spider):
    name = 'douban_parse_user_rate'
    allowed_domains = ['movie.douban.com']
    start_urls = ['http://movie.douban.com/']
    settings = get_project_settings()
    client = pymongo.MongoClient('mongodb://%s:%s@%s:%s/?authSource=%s' %
                                 (settings.get('MONGO_USER'), settings.get('MONGO_PASSWORD'), settings.get('MONGO_URL'), settings.get('MONGO_PORT'), settings.get('MONGO_DB')))
    db = client[settings.get('MONGO_DB')]


    def start_requests(self):
        for item in self.db['movie'].find({}):
            url = 'https://movie.douban.com/subject/%s/comments?start=0&sort=new_score&comments_only=1' % (item['id'])
            yield Request(url=url, callback=self.parse_user_rate, meta={"movieId": item['id']})
    
    def parse_user_rate(self, response):
        movieId = response.meta['movieId']
        datas = json.loads(response.text)
        selector = Selector(text=datas['html'])
        if '还没有人写过短评' in selector.css(".comment-item").get():
            logging.debug("已经没有评论了"  + response.url)
            return
        comments = selector.css(".comment-item")
        for comment in comments:
            userItem = DoubanUserItem()
            userRateItem = DoubanRateRelationItem()
            userRateItem['movieId'] = movieId
            # 昵称
            nickname = comment.css(".comment-info a::text").get()
            userItem['nickname'] = nickname
            # 用户链接
            userUrl = comment.css(".comment-info a::attr(href)").get()
            # 获取用户username
            result = re.compile('people/(.*)/').search(userUrl)
            if result:
                username = result.group(1)
                userItem['username'] = username
                userRateItem['username'] = username
                # 处理用户item
                yield userItem
            # 觉得有用
            voteComment = comment.css(".vote-count::text").get()
            userRateItem['voteComment'] = voteComment
            # 评分时间
            commentTime = comment.css(".comment-info .comment-time::attr(title)").get()
            commentTime = datetime.datetime.strptime(commentTime,'%Y-%m-%d %H:%M:%S')
            userRateItem['commentTime'] = commentTime
            rating = comment.css(".comment-info .rating").get()
            # 可能没有评分
            if rating:
                result = re.compile(r'allstar(\d)').search(rating)
                if result:
                    rate = result.group(1)
                    # 评分，5星则为5分
                    userRateItem['rate'] = rate
            comment = comment.css(".comment-content .short::text").get()
            userRateItem['comment'] = comment
            yield userRateItem
            # 已经最后一页了
        # 更新pageStart
        # 持续翻页
        parseResult = urlparse.urlparse(response.url)
        querys = urlparse.parse_qs(parseResult.query)
        querys['start'] = [
            str(int(querys['start'][0]) + self.movieLimit)]
        querys = {k: v[0] for k, v in querys.items()}
        querys = urllib.parse.urlencode(querys)
        requestUrl = parseResult.scheme + "://" + \
            parseResult.netloc + parseResult.path + "?" + querys
        yield Request(url=requestUrl, callback=self.parse_user_rate)
    
