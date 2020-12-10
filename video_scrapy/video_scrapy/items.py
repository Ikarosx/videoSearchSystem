# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

from scrapy import Field,Item

class BangumiItem(Item):
    # id
    id = Field()
    # 链接
    url = Field()
    # 标题
    title = Field()
    japanTitle = Field()
    # 封面
    cover = Field()
    # 排名
    rank = Field()
    # 评分
    rate = Field()
    # 标签
    tags = Field()
    staffs = Field()
    characters = Field()
    votes = Field()
    episode = Field()

class BangumiPersonItem(Item):
    # id
    id = Field()
    # 头像
    avatar = Field()
    # 名称
    name = Field()
    japanName = Field()
    

class DoubanCelebrityItem(Item):
    id = Field()
    url = Field()
    avatar = Field()
    name = Field()

class MovieItem(Item):
    # 标题
    title = Field()
    # 封面
    cover  = Field()
    # 评分
    rate = Field()
    # 详情url
    url = Field()
    # id
    id = Field()
    # 评论人数
    votePeopleNum = Field()
    # 发布年份
    releaseYear = Field()
    # 上映日期
    releaseDate = Field()
    # 片长
    runtime = Field()
    # 片长单位
    runtimeUnit = Field()
    # 语言
    language = Field()
    # imdbId
    imdbId = Field()
    imdbUrl = Field()
    # 标签
    tags = Field()
    # 好评占比
    rateOnWeight = Field()
    # # 导演
    # director = Field()
    # # 编剧
    # scriptWriter = Field()
    # 类型
    types = Field()
    # 又名
    alias = Field()
    # 语言
    language = Field()
    # 演员
    actors = Field()
    # 集数
    episode = Field()
    # 观看剧集地址
    watchEP = Field()
    # 观看电影的地址
    watchMovie = Field()
    # 官方网站
    site = Field()
    # 磁力种子
    magnent = Field()
