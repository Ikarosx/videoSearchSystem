# -*- coding: utf-8 -*-

# Scrapy settings for video_scrapy project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://doc.scrapy.org/en/latest/topics/settings.html
#     https://doc.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://doc.scrapy.org/en/latest/topics/spider-middleware.html

# 分布式
# Enables scheduling storing requests queue in redis.
SCHEDULER = "scrapy_redis.scheduler.Scheduler"

# Ensure all spiders share same duplicates filter through redis.
DUPEFILTER_CLASS = "scrapy_redis.dupefilter.RFPDupeFilter"

REDIS_URL = 'redis://default:newLife2016@8.129.178.143:6379'

BOT_NAME = 'video_scrapy'

SPIDER_MODULES = ['video_scrapy.spiders']
NEWSPIDER_MODULE = 'video_scrapy.spiders'
RETRY_TIMES = 15
# 持久化
# SCHEDULER_PERSIST = True
DUPEFILTER_DEBUG = True
# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'video_scrapy (+http://www.yourdomain.com)'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False
# LOG_LEVEL = 'WARNING'
# Configure maximum concurrent requests performed by Scrapy (default: 16)
# REACTOR_THREADPOOL_MAXSIZE = 128
CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 100000
CONCURRENT_REQUESTS_PER_IP = 0
DOWNLOAD_TIMEOUT = 10
# DOWNLOAD_DELAY = 0
# RANDOMIZE_DOWNLOAD_DELAY = True

# AUTOTHROTTLE_ENABLED = True
# AUTOTHROTTLE_START_DELAY = 1
# AUTOTHROTTLE_MAX_DELAY = 0.25
# AUTOTHROTTLE_TARGET_CONCURRENCY = 32
# AUTOTHROTTLE_DEBUG = True
# Configure a delay for requests for the same website (default: 0)
# See https://doc.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
# DOWNLOAD_DELAY = 1
# The download delay setting will honor only one of:
# CONCURRENT_REQUESTS_PER_IP = 1

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
DEFAULT_REQUEST_HEADERS = {
    # 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36'
    # 'Host': 'movie.douban.com'
    'sec-ch-ua': '"Google Chrome";v="87", " Not;A Brand";v="99", "Chromium";v="87"',
}

# Enable or disable spider middlewares
# See https://doc.scrapy.org/en/latest/topics/spider-middleware.html
SPIDER_MIDDLEWARES = {
    #    'video_scrapy.middlewares.VideoScrapySpiderMiddleware': 543,



}
# DEPTH_LIMIT = 20
# LOG_ENABLED = False
HTTPERROR_ALLOWED_CODES = [403]
# Enable or disable downloader middlewares
# See https://doc.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    'video_scrapy.middlewares.RandomUserAgent': 541,
    'video_scrapy.middlewares.ProxyMiddleWares': 542,
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': None,
    'video_scrapy.middlewares.MyRetry': 543,
    'video_scrapy.middlewares.VideoScrapyDownloaderMiddleware': 544,
}
DOWNLOAD_HANDLERS = {
    'http': 'video_scrapy.middlewares.TorHTTPDownloadHandler',
    'https': 'video_scrapy.middlewares.TorHTTPDownloadHandler'
}
# Enable or disable extensions
# See https://doc.scrapy.org/en/latest/topics/extensions.html
# EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
# }

# Configure item pipelines
# See https://doc.scrapy.org/en/latest/topics/item-pipeline.html

MONGO_URL = '8.129.178.143'
# MONGO_URL = '127.0.0.1'
MONGO_PORT = 27017
MONGO_DB = 'movie_system'
MONGO_USER = 'movie'
MONGO_PASSWORD = 'newLife2016'
ITEM_PIPELINES = {
    'video_scrapy.pipelines.MongoDBPipeline': 300
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://doc.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://doc.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = 'httpcache'
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'
