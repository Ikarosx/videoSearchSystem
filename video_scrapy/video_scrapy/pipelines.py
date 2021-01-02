# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import pymongo
import logging
from scrapy.exceptions import DropItem
from video_scrapy.items import MovieItem, DoubanCelebrityItem, BangumiItem, BangumiPersonItem, DoubanUserItem, DoubanRateRelationItem
import time
import datetime

class MongoDBPipeline(object):
    def __init__(self, mongourl, mongoport, mongodb, username, password):
        '''
        初始化mongodb数据的url、端口号、数据库名称
        '''
        self.mongourl = mongourl
        self.mongoport = mongoport
        self.mongodb = mongodb
        self.username = username
        self.password = password

    @classmethod
    def from_crawler(cls, crawler):
        """
        1、读取settings里面的mongodb数据的url、port、DB。
        """
        return cls(
            mongourl=crawler.settings.get("MONGO_URL"),
            mongoport=crawler.settings.get("MONGO_PORT"),
            mongodb=crawler.settings.get("MONGO_DB"),
            username=crawler.settings.get("MONGO_USER"),
            password=crawler.settings.get("MONGO_PASSWORD")
        )

    def open_spider(self, spider):
        '''
        1、连接mongodb数据
        '''
        self.client = pymongo.MongoClient('mongodb://%s:%s@%s:%s/?authSource=%s' % (
            self.username, self.password, self.mongourl, self.mongoport, self.mongodb))
        self.db = self.client[self.mongodb]
        # self.db.authenticate(self.username, self.password)

    def process_item(self, item, spider):
        # 豆瓣电影
        if isinstance(item, MovieItem):
            self.preProcess(item)
            self.processMovieItem(item)
        # 豆瓣演员
        if isinstance(item, DoubanCelebrityItem):
            self.preProcess(item)
            self.processDoubanCelebrityItem(item)
        # 豆瓣用户
        if isinstance(item, DoubanUserItem):
            self.preProcess(item)
            self.processDoubanUser(item)
        # 豆瓣评分
        if isinstance(item, DoubanRateRelationItem):
            self.preProcess(item)
            self.processDoubanRateRelationItem(item)
        if isinstance(item, BangumiPersonItem):
            self.preProcess(item)
            self.processBangumiPersonItem(item)
        if isinstance(item, BangumiItem):
            self.preProcess(item)
            self.processBangumiItem(item)
        
        return item

    def convertTypeItem(self, item):
        # 需要转成int的字段
        ints = ['id', 'votePeopleNum', 'releaseYear',
                'runtime', 'episode', 'rank', 'votes', 'movieId']
        # 需要转成float的字段
        floats = ['rate']
        for intStr in ints:
            if intStr in item:
                item[intStr] = int(item[intStr])
        for floatStr in floats:
            if floatStr in item:
                item[floatStr] = float(item[floatStr])

    def preProcess(self, item):
        # 去掉为空的
        item = dict(filter(lambda x: x[1] !=
                           '' and x[1] != None and x[1] != 'null', item.items()))
        # 类型转换，转成int和float
        self.convertTypeItem(item)
        # 创建时间
        if 'createTime' in item:
            item['createTime'] = datetime.datetime.fromtimestamp(time.time())
        return item

    # 豆瓣电影评分关系
    def processDoubanRateRelationItem(self, item):
        data = self.db.douban_rate.find_one({"username": item['username'], "movieId": item['movieId']})
        if not data:
            # 不存在插入
            logging.debug('插入豆瓣评分数据：%s' % (item['username'] + ':' + str(item['movieId'])))
            self.db.douban_rate.insert(dict(item))
        else:
            # 存在更新
            logging.debug('豆瓣评分数据%s存在：' % (item['username'] + ':' + str(item['movieId'])))

    def processBangumiItem(self, item):
        data = self.db.bangumi_video.find_one({"id": item['id']})
        if not data:
            # 不存在插入
            logging.debug('插入bangumi数据%s' % (item['id']))
            self.db.bangumi_video.insert(dict(item))
        else:
            logging.debug('bangumi数据%s存在' % (item['id']))
            self.db.bangumi_video.update_one(
                {"id": item['id']}, {"$set": dict(item)})


    def processBangumiPersonItem(self, item):
        data = self.db.bangumi_person.find_one({"id": item['id']})
        if not data:
            # 不存在插入
            logging.debug('插入bangumiPerson数据%s' % (item['id']))
            self.db.bangumi_person.insert(dict(item))
        else:
            # logging.debug('bangumiPerson数据%s存在，更新数据' % (item['id']))
            self.db.bangumi_person.update_one(
            {"id": item['id']}, {"$set": dict(item)})

    # 处理豆瓣电影
    def processMovieItem(self, item):
        data = self.db['movie'].find_one({"id": item['id']})
        if not data:
            # 不存在插入
            logging.debug('插入数据%s' % (item['id']))
            self.db['movie'].insert(dict(item))
        else:
            # 存在更新
            logging.debug('更新数据%s' % (item['id']))
            self.db['movie'].update_one(
                {"id": item['id']}, {"$set": dict(item)})

    # 处理豆瓣用户item
    def processDoubanUser(self, item):
        data = self.db.douban_user.find_one({"username": item['username']})
        if not data:
            # 不存在插入
            logging.debug('插入豆瓣用户数据：%s' % (item['username']))
            self.db.douban_user.insert(dict(item))
        else:
            # 存在更新
            logging.debug('豆瓣用户数据%s存在：' % (item['username']))

    # 处理豆瓣演员item

    def processDoubanCelebrityItem(self, item):
        data = self.db.douban_celebrity.find_one({"id": item['id']})
        if not data:
            # 不存在插入
            logging.debug('插入演员数据%s' % (item['name']))
            self.db.douban_celebrity.insert(dict(item))
        else:
            # 存在更新
            logging.debug('演员数据%s存在' % (item['name']))
            # self.db.douban_celebrity.update_one(
            # {"id": item['id']}, {"$set": dict(item)})

    def close_spider(self, spider):
        # 关闭数据库
        self.client.close()

class BangumiItemMongoDBPipeline(object):
    def __init__(self, mongourl, mongoport, mongodb, username, password):
        '''
        初始化mongodb数据的url、端口号、数据库名称
        '''
        self.mongourl = mongourl
        self.mongoport = mongoport
        self.mongodb = mongodb
        self.username = username
        self.password = password

    @classmethod
    def from_crawler(cls, crawler):
        """
        1、读取settings里面的mongodb数据的url、port、DB。
        """
        return cls(
            mongourl=crawler.settings.get("MONGO_URL"),
            mongoport=crawler.settings.get("MONGO_PORT"),
            mongodb=crawler.settings.get("MONGO_DB"),
            username=crawler.settings.get("MONGO_USER"),
            password=crawler.settings.get("MONGO_PASSWORD")
        )

    def open_spider(self, spider):
        '''
        1、连接mongodb数据
        '''
        self.client = pymongo.MongoClient('mongodb://%s:%s@%s:%s/?authSource=%s' % (
            self.username, self.password, self.mongourl, self.mongoport, self.mongodb))
        self.db = self.client[self.mongodb]

    def process_item(self, item, spider):
        
        return item

    def close_spider(self, spider):
        # 关闭数据库
        self.client.close()
