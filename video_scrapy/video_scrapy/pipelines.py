# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import pymongo
import logging
from scrapy.exceptions import DropItem
class VideoScrapyPipeline(object):
    def process_item(self, item, spider):
        return item

class MongoDBPipeline(object):
    def __init__(self, mongourl, mongoport, mongodb):
        '''
        初始化mongodb数据的url、端口号、数据库名称
        '''
        self.mongourl = mongourl
        self.mongoport = mongoport
        self.mongodb = mongodb

    @classmethod
    def from_crawler(cls, crawler):
        """
        1、读取settings里面的mongodb数据的url、port、DB。
        """
        return cls(
            mongourl=crawler.settings.get("MONGO_URL"),
            mongoport=crawler.settings.get("MONGO_PORT"),
            mongodb=crawler.settings.get("MONGO_DB")
        )

    def open_spider(self, spider):
        '''
        1、连接mongodb数据
        '''
        self.client = pymongo.MongoClient(self.mongourl, self.mongoport)
        self.db = self.client[self.mongodb]

    def process_item(self, item, spider):
        '''
        1、将数据写入数据库
        '''
        data = self.db['movie'].find_one({"id": item['id']})
        # 数据库存在且已经有投票人数，说明已经爬取
        if data and 'votePeopleNum' in data:
            raise DropItem("数据库存在%s" % (item['id']))
        if not data:
            # 不存在插入
            logging.debug('插入数据%s' % (item['title']))
            self.db['movie'].insert(dict(item))
        else:
            # 存在更新
            logging.debug('更新数据%s' % (item['title']))
            self.db['movie'].update_one({"id": item['id']}, {"$set":dict(item)})
        return item  
         
    def close_spider(self, spider):
        #关闭数据库
        self.client.close()
