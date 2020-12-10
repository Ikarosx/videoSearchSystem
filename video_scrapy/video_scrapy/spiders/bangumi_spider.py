# -*- coding: utf-8 -*-
import scrapy
import pymongo
from scrapy import Request, Spider
from video_scrapy.items import BangumiItem, BangumiPersonItem
import json
import logging
import urllib.parse as urlparse
import urllib
import re


class BangumiSpiderSpider(scrapy.Spider):
    name = 'bangumi_spider'
    allowed_domains = ['bgm.tv']
    start_urls = ['http://bgm.tv/']

    client = pymongo.MongoClient('mongodb://%s:%s@%s:%s/?authSource=%s' %
                                 ('movie', 'newLife2016', '127.0.0.1', '27017', 'movie_system'))
    db = client['movie_system']

    # 阶段一通过更多链接
    def start_requests(self):
        for item in self.db.bangumi_video.find({"rate":{"$exists":False}}):
            yield Request(url=item['url'], callback=self.parse_detail, meta={"id":item['id']})

    def parse_detail(self, response):
        item = BangumiItem()
        item['id'] = response.meta['id']
        # 评论人数
        votes = response.css("span[property='v:votes']::text").get()
        item['votes'] = votes
        # 评分
        rate = response.css("span[property='v:average']::text").get()
        item['rate'] = rate
        infobox = response.css("#infobox")
        # 话数
        episode = infobox.xpath("//li[contains(span/text(),'话数')]")
        if episode:
            episode = episode.css("::text")[1].get()
            item['episode'] = episode
        # 排名
        rank = response.css("#panelInterestWrapper .alarm::text").get()
        if rank:
            # 去掉开头的#
            rank = rank[1:]
            item['rank'] = rank
        # 标签
        tags = response.css(".subject_tag_section .inner span[class!='grey']::text").getall()
        item['tags'] = tags
        # 制作人员
        yield Request(url='http://bgm.tv/subject/%s/persons' % (item['id']), callback=self.parse_staff, meta={"item":item})
    
    # 
    def parse_staff(self, response):
        item = response.meta['item']
        persons = response.css("#columnInSubjectA>div")
        staffs = []
        for person in persons:
            personItem = BangumiPersonItem()
            # 头像
            avatar = urllib.parse.urljoin(response.url, person.css("img::attr(src)").get())
            staffId = re.search(re.compile(r'.*(\d+)'),person.css("h2 a::attr(href)").get()).group(1)
            staff = {
                "id": int(staffId)
            }
            personItem['avatar'] = avatar
            personItem['id'] = staffId
            # 名字
            names = person.css("h2 ::text").getall()
            if len(names) == 2:
                name = names[1]
                japanName = names[0].split(" ")[0]
                personItem['name'] = name
                personItem['japanName'] = japanName
                staff['name'] = name
            else:
                name = names[0]
                personItem['name'] = name
                staff['name'] = name
            roles = person.css(".badge_job::text").getall()
            staff['role'] = roles
            staffs.append(staff)
            yield personItem
        item['staffs'] = staffs
        # 角色
        yield Request(url='http://bgm.tv/subject/%s/characters' % (item['id']), callback=self.parse_character, meta={"item":item})
    
    def parse_character(self, response):
        item = response.meta['item']
        characters = response.css("#columnInSubjectA>div")
        charactersArray = []
        for character in characters:
            japanName = character.css(".clearit h2 a::text").get()
            name = character.css(".clearit h2 .tip::text").get()
            cv = character.css(".actorBadge")
            cvId = cvChineseName = cvJapanName = None
            if cv:
                cv = cv[0]
                avatar = cv.css("img::attr(src)").get()
                if avatar:
                    avatar = urllib.parse.urljoin(response.url, avatar)
                cvUrl = urllib.parse.urljoin(response.url, cv.css("p a::attr(href)").get())
                cvId = re.search(re.compile(r'person/(\d+)'), cvUrl).group(1)
                cvChineseName = cv.css("p small::text").get()
                cvJapanName = cv.css("p a::text").get()
                personItem = BangumiPersonItem()
                personItem['id'] = cvId
                personItem['name'] = cvChineseName
                personItem['japanName'] = cvJapanName
                personItem['avatar'] = avatar
                yield personItem
            data = {
                "name": name,
                "japanName": japanName,
                "cvId":cvId,
                "cvName": cvChineseName,
                "cvJapanName": cvJapanName
            }
            charactersArray.append(data)
        item['characters'] = charactersArray
        yield item