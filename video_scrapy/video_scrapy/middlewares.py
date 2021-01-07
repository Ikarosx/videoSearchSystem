# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
import random
import string
import time
import urllib
import requests
from twisted.web.client import Agent
from scrapy.core.downloader.tls import openssl_methods
from scrapy.utils.misc import create_instance, load_object
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.settings.default_settings import DOWNLOADER_CLIENTCONTEXTFACTORY, DOWNLOADER_CLIENT_TLS_METHOD
from scrapy.settings import default_settings as settings
import logging
import scrapy.core.downloader.handlers.http11 as handler
from twisted.internet import reactor
from txsocksx.http import SOCKS5Agent
from twisted.internet.endpoints import TCP4ClientEndpoint
from scrapy.core.downloader.webclient import _parse
from scrapy.spidermiddlewares.httperror import HttpErrorMiddleware
from scrapy.exceptions import IgnoreRequest
from fake_useragent import UserAgent


logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)


class VideoScrapySpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class RandomUserAgent(object):
    def __init__(self):
        self.ua = UserAgent()

    """
    换User-Agent
    """
    def process_request(self, request, spider):
        request.headers['User-Agent'] = self.ua.random


class MyRetry(RetryMiddleware):
    """
    保存重试失败url
    """

    def process_exception(self, request, exception, spider):
        if 'proxy' in request.meta:
            self.delete_proxy(request.meta['proxy'].split("://")[1])
            logging.debug("重试删除代理" + request.meta['proxy'])
        if (
            isinstance(exception, self.EXCEPTIONS_TO_RETRY)
            and not request.meta.get('dont_retry', False)
        ):
            return self._retry(request, exception, spider)

    def delete_proxy(self, proxy):
        requests.get("http://127.0.0.1:5010/delete/?proxy={}".format(proxy))


class VideoScrapyDownloaderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.
        # Must either:
        if request.url.startswith("https://www.douban.com/accounts/login") or request.url.startswith("https://accounts.douban.com"):
            self.delete_proxy(request.meta['proxy'].split("://")[1])
            logging.debug("跳转登陆，删除代理" + request.meta['proxy'])
            return request
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.
        # Must either;
        if response.status == 403:
            self.delete_proxy(request.meta['proxy'].split("://")[1])
            logging.debug("403删除代理，" + request.meta['proxy'])
            logging.debug(request.headers)
            logging.debug(response.headers)
            url = request.url
            if request.url.startswith('https://sec.douban.com/b?r='):
                url = url.replace('https://sec.douban.com/b?r=','')
                url = urllib.parse.unquote(url)
            request._set_url(url)
            logging.debug("新的url：" + url)
            # 关键，不然会由于请求一样被过滤掉
            return request.replace(dont_filter=True)
            # raise IgnoreRequest("未知403")
            # 继续请求
        if "检测到有异常请求" in response.text:
            self.delete_proxy(request.meta['proxy'].split("://")[1])
            logging.debug("检测到有异常请求从IP发出，请求："+request.url+"，删除代理，" + request.meta['proxy'])
            return request.replace(dont_filter=True)
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def delete_proxy(self, proxy):
        requests.get("http://127.0.0.1:5010/delete/?proxy={}".format(proxy))

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.
        logging.debug(exception)
        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class TorScrapyAgent(handler.ScrapyAgent):
    def _get_agent(self, request, timeout):
        bindaddress = request.meta.get('bindaddress') or self._bindAddress
        proxy = request.meta.get('proxy')
        if proxy:
            _, _, proxyHost, proxyPort, proxyParams = _parse(proxy)
            scheme = _parse(request.url)[0]
            omitConnectTunnel = b'noconnect' in proxyParams
            if scheme == 'https' and not omitConnectTunnel:
                proxyConf = (proxyHost, proxyPort,
                             request.headers.get('Proxy-Authorization', None))
                return self._TunnelingAgent(reactor, proxyConf,
                                            contextFactory=self._contextFactory, connectTimeout=timeout,
                                            bindAddress=bindaddress, pool=self._pool)
            else:
                proxyEndpoint = TCP4ClientEndpoint(reactor, proxyHost, proxyPort,
                                                   timeout=timeout, bindAddress=bindaddress)
                agent = SOCKS5Agent(reactor, proxyEndpoint=proxyEndpoint,
                                    contextFactory=self._contextFactory, pool=self._pool, bindAddress=bindaddress, connectTimeout=timeout)
                return agent

        return self._Agent(reactor, contextFactory=self._contextFactory,
                           connectTimeout=timeout, bindAddress=bindaddress, pool=self._pool)


class ProxyMiddleWares(object):
    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.
        while True:
            proxy = self.get_proxy().get("proxy")
            if proxy == None:
                # 如果没有代理休眠5s
                time.sleep(5)
                continue
                # spider.crawler.engine.close_spider(spider, "代理不足，关闭爬虫")
            request.meta['proxy'] = "socks5://" + proxy
            break
        request.cookie = self.getCookie()
        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def getCookie(self):
        bid = ''.join(
            random.choice(string.ascii_letters + string.digits)
            for x in range(11))
        cookies = {
            'bid': bid
        }
        return cookies

    def get_proxy(self):
        return requests.get("http://127.0.0.1:5010/get/").json()


class TorHTTPDownloadHandler(handler.HTTP11DownloadHandler):
    def download_request(self, request, spider):
        agent = TorScrapyAgent(contextFactory=self._contextFactory, pool=self._pool,
                               maxsize=getattr(
                                   spider, 'download_maxsize', self._default_maxsize),
                               warnsize=getattr(
                                   spider, 'download_warnsize', self._default_warnsize),
                               fail_on_dataloss=self._fail_on_dataloss)
        return agent.download_request(request)
