# -*- coding: utf-8 -*-
from scrapy import Request, Spider
from video_scrapy.items import MovieItem
import json
import re
import logging

class MovieSpiderSpider(Spider):
    name = 'movie_spider'
    allowed_domains = ['movie.douban.com']
    movieStart = 0
    movieLimit = 100
    # tvStart = 0
    # tvLimit = 20
    movieUrl = 'https://movie.douban.com/j/search_subjects?type=movie&tag=热门&sort=recommend&page_limit=%s&page_start=' % (
        movieLimit)
    # tvUrl = 'https://movie.douban.com/j/new_search_subjects?sort=U&tags=%E7%94%B5%E8%A7%86%E5%89%A7&start='
    # start_urls = [movieUrl + movieStart, tvUrl + tvStart]

    def start_requests(self):
        yield Request(url=self.movieUrl + str(self.movieStart), callback=self.parse_movie_url)

    def parse_movie_url(self, response):
        
        # 加载成dict格式
        data = json.loads(response.text)
        # 获取subjects
        subjects = data["subjects"]
        # 遍历
        for subject in subjects:
            # 构建item
            item = MovieItem()
            item['title'] = subject['title']
            item['cover'] = subject['cover']
            item['rate'] = subject['rate']
            item['url'] = subject['url']
            item['id'] = subject['id']

            if item['url']:
                # 如果url有数据 进一步解析
                yield Request(url=item['url'], callback=self.parse_movie_detail, meta={'item': item})
            else:
                # 没有数据直接返回
                yield item
        # 已经最后一页了
        if len(subjects) == self.movieLimit:
            self.movieStart += self.movieLimit
            yield Request(url=self.movieUrl + str(self.movieStart), callback=self.parse_movie_url)

    def parse_movie_detail(self, response):
        # 取出之前的item
        item = response.meta['item']

        # 评论人数
        votePeopleNum = response.css(
            ".rating_people span[property='v:votes']::text").get()
        item['votePeopleNum'] = votePeopleNum
        # 上映日期
        releaseDate = response.css(
            "#info span[property='v:initialReleaseDate']::text").get()
        # 2020-11-27(韩国网络)
        pattern = re.compile('(.*)\((.*)\)')
        patternResult = re.match(pattern, releaseDate)
        if patternResult:
            # 2020-11-27
            releaseDate = patternResult.group(1)
        item['releaseDate'] = releaseDate
        # 片长，单位分钟
        runtime = response.css(
            "#info span[property='v:runtime']::text").get()
        if runtime:
            runtime = runtime[:-2]
            runtimeMatchResult = re.match(re.compile('(\d+).*'), runtime)
            if runtimeMatchResult:
                runtime = runtimeMatchResult.group(1)
        item['runtime'] = runtime
        # IMDb
        imdbId = response.css("#info a[rel='nofollow']::text").get()
        imdbUrl = response.css("#info a[rel='nofollow']::attr(href)").get()
        item['imdbId'] = imdbId
        item['imdbUrl'] = imdbUrl
        # 标签
        tags = response.css(".tags-body a::text").getall()
        item['tags'] = tags
        # 好评占比,54321星
        rateOnWeight = response.css(
            ".ratings-on-weight .rating_per::text").getall()
        item['rateOnWeight'] = rateOnWeight
        # 导演
        director = response.xpath(
            "//span[contains(span/text(),'导演')]//span[@class='attrs']//a//text()").getall()
        item['director'] = director
        # 编剧
        scriptWriter = response.xpath(
            "//span[contains(span/text(),'编剧')]//span[@class='attrs']//a//text()").getall()
        item['scriptWriter'] = scriptWriter
        # 类型
        types = response.css("#info span[property='v:genre']::text").getall()
        item['types'] = types
        info = response.css("#info").get()
        # 又名
        aliasPatternResult = re.search(
            re.compile('又名.*?</span>(.*?)<br>'), info)
        if aliasPatternResult:
            alias = aliasPatternResult.group(1).split('/')
            # 又名去空格
            alias = list(map(lambda name: name.strip(), alias))
            item['alias'] = alias
        # 语言
        languagePatternResult = re.search(
            re.compile('语言.*?</span>(.*?)<br>'), info)
        if aliasPatternResult:
            language = languagePatternResult.group(1).strip()
            # 语言去空格
            # language = list(map(lambda name: name.strip(), language))
            item['language'] = language
        yield Request(url=response.url + "celebrities", callback=self.parse_movie_celebrities, meta={'item': item})

    # 解析演员饰演角色
    def parse_movie_celebrities(self, response):
        item = response.meta['item']
        names = response.css(
            ".list-wrapper:nth-child(2) .celebrity .name a::text").getall()
        roles = response.css(
            ".list-wrapper:nth-child(2) .celebrity .role::text").getall()
        nameRole = [{names[index].replace('.','-'):roles[index].replace('.','-')} for index in range(len(names))]
        item['actors'] = nameRole
        yield item
