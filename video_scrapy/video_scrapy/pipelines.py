# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import pymongo
import logging
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
        self.db['movie'].insert(dict(item))
        logging.debug('Item written to MongoDB database %s/%s：%s' % (self.db, 'movie', item['title']))
        return item  
         
    def close_spider(self, spider):
        #关闭数据库
        self.client.close()
