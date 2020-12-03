# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
from video_scrapy.settings import USER_AGENTS
import random
import string
import requests
from scrapy.core.downloader.tls import openssl_methods
from scrapy.utils.misc import create_instance, load_object
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.settings.default_settings import  DOWNLOADER_CLIENTCONTEXTFACTORY,DOWNLOADER_CLIENT_TLS_METHOD
from scrapy.settings import default_settings as settings
import logging
import scrapy.core.downloader.handlers.http11 as handler
from twisted.internet import reactor
from txsocksx.http import SOCKS5Agent
from twisted.internet.endpoints import TCP4ClientEndpoint
from scrapy.core.downloader.webclient import _parse

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
    """
    换User-Agent
    """
    def process_request(self, request, spider):
        request.headers['User-Agent'] = random.choice(USER_AGENTS)

class MyRetry(RetryMiddleware):
    """
    保存重试失败url
    """
    def process_exception(self, request, exception, spider):
        logging.debug("重试process_exception%s" % (request.meta['proxy'][9:]))
        self.delete_proxy(request.meta['proxy'][9:])
        logging.debug("删除代理" + request.meta['proxy'])
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
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None
    
    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.
        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.
        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass
    
    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)

    


class TorScrapyAgent(handler.ScrapyAgent):
    _Agent = SOCKS5Agent

    def _get_agent(self, request, timeout):
        proxy = request.meta['proxy']
        if proxy:
            proxy_scheme, _, proxy_host, proxy_port, _ = _parse(proxy)
            proxy_scheme = str(proxy_scheme, 'utf-8')
            if proxy_scheme == 'socks5':
                endpoint = TCP4ClientEndpoint(reactor, proxy_host, proxy_port)
                self._sslMethod = openssl_methods[DOWNLOADER_CLIENT_TLS_METHOD]
                self._contextFactoryClass = load_object(DOWNLOADER_CLIENTCONTEXTFACTORY)
                self._contextFactory = create_instance(
                    objcls=self._contextFactoryClass,
                    settings=settings,
                    crawler=None,
                    method=self._sslMethod,
                )
                return self._Agent(reactor, proxyEndpoint=endpoint, contextFactory = self._contextFactory)

        return super(TorScrapyAgent, self)._get_agent(request, timeout)

class ProxyMiddleWares(object):
    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.
        proxy = self.get_proxy().get("proxy")
        request.meta['proxy'] = "socks5://" + proxy
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
            'bid': bid,
            'dont_redirect': True,
            'handle_httpstatus_list': [302],
        }
        return cookies
    def get_proxy(self):
        return requests.get("http://127.0.0.1:5010/get/").json()

class TorHTTPDownloadHandler(handler.HTTP11DownloadHandler):
    def download_request(self, request, spider):
        agent = TorScrapyAgent(contextFactory=self._contextFactory, pool=self._pool,
                               maxsize=getattr(spider, 'download_maxsize', self._default_maxsize),
                               warnsize=getattr(spider, 'download_warnsize', self._default_warnsize))

        return agent.download_request(request)