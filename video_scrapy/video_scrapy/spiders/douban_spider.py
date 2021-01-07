# -*- coding: utf-8 -*-
from scrapy import Request, Spider
from video_scrapy.items import MovieItem
import json
import re
import logging
import urllib.parse as urlparse
import urllib
import pymongo
from scrapy.utils.project import get_project_settings

class DoubanSpiderSpider(Spider):
    name = 'douban_spider'
    allowed_domains = ['movie.douban.com']
    startUrl = 'https://movie.douban.com/explore'
    settings = get_project_settings()
    client = pymongo.MongoClient('mongodb://%s:%s@%s:%s/?authSource=%s' %
                                 (settings.get('MONGO_USER'), settings.get('MONGO_PASSWORD'), settings.get('MONGO_URL'), settings.get('MONGO_PORT'), settings.get('MONGO_DB')))
    db = client[settings.get('MONGO_DB')]
    # 最新爬虫方案：
    # ①找出所有url
    # ②判断数据库中该id是否有评论人数，如果没有跳3，如果有跳4，
    # ③解析该id对应链接的数据到数据库
    # ④递归 "喜欢这部电影的人也喜欢"

    def start_requests(self):
        for item in self.db['movie'].find({"votePeopleNum": {"$exists": False}}):
            yield Request(url=item['url'], callback=self.parse_movie_detail)

    # 遍历整个页面a链接
    def parse_url(self, response):
        urls = response.css("a::attr(href)").getall()
        for url in urls:
            # 验证url有效性
            if not self.verifyUrl(url):
                # logging.debug("url无效%s" % (url))
                continue
            if url.startswith("/"):
                url = "https://movie.douban.com" + url
            if url.startswith('https://movie.douban.com/subject/'):
                yield Request(url=url, callback=self.parse_movie_detail)
            else:
                yield Request(url=url, callback=self.parse_url)

    # 校验url有效
    def verifyUrl(self, url):

        if url.startswith("javascript"):
            return False
        if url.startswith("#"):
            return False
        if url.startswith("https://help.douban"):
            return False
        if url.startswith("/accounts/register"):
            return False
        if url.startswith("//www.douban.com/gallery"):
            return False
        if url.startswith("comments"):
            return False
        if url.startswith("/help/opinion"):
            return False
        if url.startswith("./"):
            return False
        return True

    # 解析具体的页面
    # 最新爬虫方案：
    # ①找出所有url
    # ②判断数据库中该id是否有评论人数，如果没有跳3，如果有跳4，
    # ③解析该id对应链接的数据到数据库
    # ④递归 "喜欢这部电影的人也喜欢"
    def parse_movie_detail(self, response):
        info = response.css("#info").get()
        if not info:
            # 如果没有info
            # 说明是其他页面
            # yield Request(url=response.url, callback=self.parse_url)
            return
        item = MovieItem()
        item['title'] = response.css(
            "span[property='v:itemreviewed']::text").get()
        item['cover'] = response.css("img[rel='v:image']::attr(src)").get()
        item['rate'] = response.css("strong[property='v:average']::text").get()
        item['url'] = response.url.split('?')[0]
        item['id'] = re.match(re.compile(
            r".*subject/(\d+)/"), item['url']).group(1)
        data = self.db['movie'].find_one({"id": int(item['id'])})
        # 数据库存在且已经有投票人数，说明已经爬取
        if data and 'votePeopleNum' in data:
            # 数据库存在进行下一条
            logging.debug("数据库存在%s" % (item['id']))
            return
        # 评论人数
        votePeopleNum = response.css(
            ".rating_people span[property='v:votes']::text").get()
        if votePeopleNum == None or votePeopleNum.strip() == '':
            votePeopleNum = 0
        item['votePeopleNum'] = votePeopleNum
        # 发布日期
        releaseYear = response.css(".year::text").get()
        if releaseYear:
            releaseYear = re.search(re.compile(r'.*?(\d+).*?'), releaseYear)
            if releaseYear:
                item['releaseYear'] = releaseYear.group(1)
        # 上映日期
        releaseDate = response.css(
            "#info span[property='v:initialReleaseDate']::text").get()
        if releaseDate:
            # 2020-11-27(韩国网络)
            item['releaseDate'] = releaseDate.split('/')
        # 片长，单位分钟
        runtime = response.css(
            "#info span[property='v:runtime']::text").get()
        if runtime:
            runtime = runtime.strip()
            runtimeMatchResult = re.match(re.compile(r'(\d+)(.*)'), runtime)
            if runtimeMatchResult:
                runtime = runtimeMatchResult.group(1)
                item['runtime'] = runtime
                runtimeUnit = runtimeMatchResult.group(2)
                item['runtimeUnit'] = runtimeUnit
        # 官方网站
        site = response.xpath(
            "//span[contains(text(),'官方网站')]/following-sibling::a[1]//@href").get()
        item['site'] = site
        # IMDb
        imdbId = response.xpath(
            "//span[contains(text(),'IMDb')]/following-sibling::a[1]//text()").get()
        imdbUrl = response.xpath(
            "//span[contains(text(),'IMDb')]/following-sibling::a[1]//@href").get()
        item['imdbId'] = imdbId
        item['imdbUrl'] = imdbUrl
        # 标签
        tags = response.css(".tags-body a::text").getall()
        item['tags'] = tags
        # 好评占比,54321星
        rateOnWeight = response.css(
            ".ratings-on-weight .rating_per::text").getall()
        item['rateOnWeight'] = rateOnWeight
        # # 导演
        # director = response.xpath(
        #     "//span[contains(span/text(),'导演')]//span[@class='attrs']//a//text()").getall()
        # item['director'] = director
        # # 编剧
        # scriptWriter = response.xpath(
        #     "//span[contains(span/text(),'编剧')]//span[@class='attrs']//a//text()").getall()
        # item['scriptWriter'] = scriptWriter
        # 类型
        types = response.css("#info span[property='v:genre']::text").getall()
        item['types'] = types
        # 集数
        episode = re.search(re.compile(
            '集数.*?</span>(\d+).*?<br>'), info)
        if episode:
            item['episode'] = episode.group(1).strip()
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
        if languagePatternResult:
            language = languagePatternResult.group(1).strip()
            # 语言去空格
            # language = list(map(lambda name: name.strip(), language))
            item['language'] = language

        # 剧集观看地点
        if response.xpath("//div[@class='gray_ad' and contains(h2/text(), '剧集')]").get() != None:
            aas = response.css(".gray_ad .bs a")
            watchEP = []
            for aa in aas:
                dataSource = aa.attrib['data-source']
                dataCn = aa.attrib['data-cn']

                data = {
                    "dataCn": dataCn
                }
                result = re.search(re.compile(
                    r"sources\["+dataSource+r"\].*?\[.*?\]", re.S), response.text)
                if not result:
                    # 如果只有一个数据源，对应的数据源放在了一个js文件里
                    logging.warn("视频获取不到对应的观看地址数据源" + response.url)
                    watchEP.append(data)
                    continue
                result = result.group()
                # 找到形如{play_link: "https://www.douban.com/link2/?url=http%3A%2F%2Fv.youku.com%2Fv_show%2Fid_XNDQ5OTE2MTc3Ng%3D%3D.html%3Ftpa%3DdW5pb25faWQ9MzAwMDA4XzEwMDAwMl8wMl8wMQ%26refer%3Desfhz_operation.xuka.xj_00003036_000000_FNZfau_19010900&amp;subtype=3&amp;type=online-video", ep: "1"}
                eps = re.findall(re.compile(r"\{.*?\}", re.S), result)
                epArray = []
                for ep in eps:
                    # 将其变为dict
                    ep = eval(ep, type('Dummy', (dict,), dict(
                        __getitem__=lambda s, n: n))())
                    # 集数
                    epNum = ep['ep']
                    # 链接
                    playLink = ep['play_link'].split('url=')[1]
                    # 转码
                    playLink = urllib.parse.unquote(playLink)
                    epArray.append({"ep": epNum, "url": playLink})
                data['srouce'] = epArray
                watchEP.append(data)
            item['watchEP'] = watchEP
        # 电影观看地点
        if response.xpath("//div[@class='gray_ad' and contains(h2/text(), '电影')]").get() != None:
            sourceMap = {
                "腾讯视频": "1",
                "爱奇艺视频": "9",
                "优酷视频": "3",
                "哔哩哔哩": "8",
                "1905电影网": "13",
                "咪咕视频": "15",
                "欢喜首映": "16",
                "西瓜视频": "17",
            }
            watchMovie = []
            aas = response.css(".gray_ad .bs a")
            for aa in aas:
                dataCn = aa.attrib['data-cn']
                href = aa.attrib['href']
                data = {
                    "dataCn": dataCn
                }
                if not href:
                    result = re.search(re.compile(
                        r"sources\["+sourceMap[dataCn]+r"\].*?\[.*?\]", re.S), response.text)
                    # 获取不到对应的数据源
                    if not result:
                        # 如果只有一个数据源，对应的数据源放在了一个js文件里
                        logging.warn("视频获取不到对应的观看地址数据源" + response.url)
                        watchMovie.append(data)
                        continue
                    result = result.group()
                    movies = re.findall(re.compile(r"\{.*?\}", re.S), result)
                    movieArray = []
                    for movie in movies:
                        # 将其变为dict
                        movie = eval(movie, type('Dummy', (dict,), dict(
                            __getitem__=lambda s, n: n))())
                        # 集数
                        movieNum = movie['ep']
                        # 链接
                        playLink = movie['play_link'].split('url=')[1]
                        # 转码
                        playLink = urllib.parse.unquote(playLink)
                        movieArray.append({"ep": movieNum, "url": playLink})
                    data['source'] = movieArray
                else:
                    searchResult = re.search(re.compile(
                        r"link2/\?url=(.*)", re.S), href)
                    if searchResult:
                        href = searchResult.group(1)
                        href = urllib.parse.unquote(href)
                    data['url'] = href
                watchMovie.append(data)
            item['watchMovie'] = watchMovie
        yield item
        # 解析演员表
        # yield Request(url=urllib.parse.urljoin(item['url'], "celebrities"), callback=self.parse_movie_celebrities, meta={"item": item})
        # 遍历推荐
        recommendations = response.css(
            "#recommendations a::attr(href)").getall()
        for recommendation in recommendations:
            # ----------  很快就过滤没了   -------
            # recommendId = re.search(re.compile("subject/(\d+?)/"), recommendation).group(1)
            # data = self.db['movie'].find_one({"id": recommendId})
            # # 数据库存在且已经有投票人数，说明已经爬取
            # if data and 'votePeopleNum' in data:
            #     # 数据库存在进行下一条
            #     logging.debug("数据库存在%s" % (recommendId))
            #     continue
            yield Request(url=recommendation, callback=self.parse_movie_detail)

    # 解析演员饰演角色
    def parse_movie_celebrities(self, response):
        item = response.meta['item']
        listWrapper = response.xpath(
            "//div[@class='list-wrapper' and contains(h2/text(), '演员')]")
        names = listWrapper.css(
            ".celebrity .name a::text").getall()
        roles = listWrapper.css(
            ".celebrity .role::text").getall()
        nameRole = [{names[index].replace(
            '.', '-'):roles[index].replace('.', '-')} for index in range(len(names))]
        item['actors'] = nameRole
        yield item
