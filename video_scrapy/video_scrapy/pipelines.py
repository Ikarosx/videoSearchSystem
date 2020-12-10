# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import pymongo
import logging
from scrapy.exceptions import DropItem
from video_scrapy.items import MovieItem, DoubanCelebrityItem, BangumiItem, BangumiPersonItem


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

    def convertTypeItem(self, item):
        # 需要转成int的字段
        ints = ['id', 'votePeopleNum', 'releaseYear', 'runtime', 'episode']
        # 需要转成float的字段
        floats = ['rate']
        for intStr in ints:
            if intStr in item:
                item[intStr] = int(item[intStr])
        for floatStr in floats:
            if floatStr in item:
                item[floatStr] = float(item[floatStr])

    def process_item(self, item, spider):
        if not isinstance(item, MovieItem):
            return item
        # 去掉为空的
        item = dict(filter(lambda x: x[1] !=
                           '' and x[1] != None, item.items()))
        # 类型转换，转成int和float
        self.convertTypeItem(item)
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
        return item

    def close_spider(self, spider):
        # 关闭数据库
        self.client.close()


class DoubanCelebrityItemMongoDBPipeline(object):
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

    def convertTypeItem(self, item):
        # 需要转成int的字段
        ints = ['id']
        # 需要转成float的字段
        floats = []
        for intStr in ints:
            if intStr in item:
                item[intStr] = int(item[intStr])
        for floatStr in floats:
            if floatStr in item:
                item[floatStr] = float(item[floatStr])

    def process_item(self, item, spider):
        if not isinstance(item, DoubanCelebrityItem):
            return item
        # 去掉为空的
        item = dict(filter(lambda x: x[1] !=
                           '' and x[1] != None, item.items()))
        # 类型转换，转成int和float
        self.convertTypeItem(item)
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
        return item

    def close_spider(self, spider):
        # 关闭数据库
        self.client.close()

class BangumiPersonItemMongoDBPipeline(object):
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

    def convertTypeItem(self, item):
        # 需要转成int的字段
        ints = ['id']
        # 需要转成float的字段
        floats = []
        for intStr in ints:
            if intStr in item:
                item[intStr] = int(item[intStr])
        for floatStr in floats:
            if floatStr in item:
                item[floatStr] = float(item[floatStr])

    def process_item(self, item, spider):
        if not isinstance(item, BangumiPersonItem):
            return item
        # 去掉为空的
        item = dict(filter(lambda x: x[1] !=
                           '' and x[1] != None, item.items()))
        # 类型转换，转成int和float
        self.convertTypeItem(item)
        data = self.db.bangumi_person.find_one({"id": item['id']})
        if not data:
            # 不存在插入
            logging.debug('插入bangumiPerson数据%s' % (item['id']))
            self.db.bangumi_person.insert(dict(item))
        else:
            # logging.debug('bangumiPerson数据%s存在，更新数据' % (item['id']))
            self.db.bangumi_person.update_one(
            {"id": item['id']}, {"$set": dict(item)})
        return item

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

    def convertTypeItem(self, item):
        # 需要转成int的字段
        ints = ['id', 'rank','votes','episode']
        # 需要转成float的字段
        floats = ['rate']
        for intStr in ints:
            if intStr in item:
                item[intStr] = int(item[intStr])
        for floatStr in floats:
            if floatStr in item:
                item[floatStr] = float(item[floatStr])

    def process_item(self, item, spider):
        if not isinstance(item, BangumiItem):
            return item
        # 去掉为空的
        item = dict(filter(lambda x: x[1] !=
                           '' and x[1] != None, item.items()))
        # 类型转换，转成int和float
        self.convertTypeItem(item)
        data = self.db.bangumi_video.find_one({"id": item['id']})
        if not data:
            # 不存在插入
            logging.debug('插入bangumi数据%s' % (item['id']))
            self.db.bangumi_video.insert(dict(item))
        else:
            logging.debug('bangumi数据%s存在' % (item['id']))
            self.db.bangumi_video.update_one(
            {"id": item['id']}, {"$set": dict(item)})
        return item

    def close_spider(self, spider):
        # 关闭数据库
        self.client.close()
