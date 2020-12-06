# -*- coding: utf-8 -*-
from scrapy import Request, Spider
from video_scrapy.items import MovieItem
import json
import re
import logging
import urllib.parse as urlparse
import urllib
import pymongo


class MovieSpiderSpider(Spider):
    name = 'movie_spider'
    allowed_domains = ['movie.douban.com']
    movieStart = 0
    movieLimit = 100
    # tvStart = 0
    # tvLimit = 20
    startUrl = 'https://movie.douban.com/explore'
    movieTags = ['热门',
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
                 '文艺']
    tvTags = ['热门', '美剧', '英剧', '韩剧', '日剧', '国产剧', '港剧', '日本动画', '综艺', '纪录片']

    # 最新爬虫方案：
    # ①找出所有url
    # ②判断数据库中该id是否有评论人数，如果没有跳3，如果有跳4，
    # ③解析该id对应链接的数据到数据库
    # ④递归 "喜欢这部电影的人也喜欢" 
    def start_requests(self):
        for item in self.db['movie'].find({"votePeopleNum": {"$exists": False}}):
            yield Request(url=item['url'], callback=self.parse_movie_detail)

    # 通过更多链接
    # def start_requests(self):
    #     # yield Request(url=self.startUrl, callback=self.parse_url)
    #     for tag in self.movieTags:
    #         movieUrl = 'https://movie.douban.com/j/search_subjects?type=movie&tag=%s&sort=recommend&page_limit=%s&page_start=0' % (
    #             tag, self.movieLimit)
    #         yield Request(url=movieUrl, callback=self.parse_movie_url)
    #     for tag in self.tvTags:
    #         movieUrl = 'https://movie.douban.com/j/search_subjects?type=tv&tag=%s&sort=recommend&page_limit=%s&page_start=0' % (
    #             tag, self.movieLimit)
    #         yield Request(url=movieUrl, callback=self.parse_movie_url)

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

    # 通过加载更多进入
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
            count = self.db['movie'].count_documents({"id": item['id']})
            # 数据库存在进行下一条
            if count != 0:
                logging.debug("数据库存在%s" % (item['id']))
                continue
            yield item
        # if item['url']:
        #     # 如果url有数据 进一步解析
        #     yield Request(url=item['url'], callback=self.parse_movie_detail, meta={'item': item})
        # else:
        #     # 没有数据直接返回
        #     yield item

        # 已经最后一页了
        if len(subjects) == self.movieLimit:
            self.movieStart += self.movieLimit
            # 更新pageStart
            parseResult = urlparse.urlparse(response.url)
            querys = urlparse.parse_qs(parseResult.query)
            querys['page_start'] = [
                str(int(querys['page_start'][0]) + self.movieLimit)]
            querys = {k: v[0] for k, v in querys.items()}
            querys = urllib.parse.urlencode(querys)
            requestUrl = parseResult.scheme + "://" + \
                parseResult.netloc + parseResult.path + "?" + querys
            yield Request(url=requestUrl, callback=self.parse_movie_url)

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
        
        # if not info:
        #     logging.debug("无法读取到info数据")
        #     yield item
        # 评论人数
        votePeopleNum = response.css(
            ".rating_people span[property='v:votes']::text").get()
        item['votePeopleNum'] = votePeopleNum
        # 上映日期
        releaseDate = response.css(
            "#info span[property='v:initialReleaseDate']::text").get()
        if releaseDate:
            # 2020-11-27(韩国网络)
            pattern = re.compile(r'(.*)\((.*)\)')
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
            runtimeMatchResult = re.match(re.compile(r'(\d+).*'), runtime)
            if runtimeMatchResult:
                runtime = runtimeMatchResult.group(1)
        item['runtime'] = runtime
        # 官方网站
        site = response.xpath("//span[contains(text(),'官方网站')]/following-sibling::a[1]//@href").get()
        item['site'] = site
        # IMDb
        imdbId = response.xpath("//span[contains(text(),'IMDb')]/following-sibling::a[1]//text()").get()
        imdbUrl = response.xpath("//span[contains(text(),'IMDb')]/following-sibling::a[1]//@href").get()
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
        # 集数
        episode = re.search(re.compile(
            '集数.*?</span>(.*?)<br>'), info)
        if episode:
            item['episode'] = episode.group().strip()
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
                    logging.debug("视频获取不到对应的观看地址数据源" + response.url)
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
                        logging.debug("视频获取不到对应的观看地址数据源" + response.url)
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
                    searchResult = re.search(re.compile(r"link2/\?url=(.*)", re.S), href)
                    if searchResult:
                        href = searchResult.group(1)
                        href = urllib.parse.unquote(href)
                    data['url'] = href
                watchMovie.append(data)
            item['watchMovie'] = watchMovie
        yield item
        # 遍历推荐
        recommendations = response.css("#recommendations a::attr(href)").getall()
        for recommenddation in recommendations:
            yield Request(url=recommenddation, callback=self.parse_movie_detail)

    # 解析演员饰演角色
    def parse_movie_celebrities(self, response):
        item = response.meta['item']
        names = response.css(
            ".list-wrapper:nth-child(2) .celebrity .name a::text").getall()
        roles = response.css(
            ".list-wrapper:nth-child(2) .celebrity .role::text").getall()
        nameRole = [{names[index].replace(
            '.', '-'):roles[index].replace('.', '-')} for index in range(len(names))]
        item['actors'] = nameRole
        yield item
