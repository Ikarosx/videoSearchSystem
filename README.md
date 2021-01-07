# movieSearchSystem







### 遇到的问题



#### 代理无法访问豆瓣

http/https不行，需要使用socks5的代理
（why？？我还以为是代理有问题换了一天的代理。。



#### requests库请求豆瓣乱码

请求头`Accept-Encoding`不能包含br

[跳转链接](https://blog.csdn.net/u011423145/article/details/92836441)



#### 如何在Scrapy中使用socks5代理

实现自己的downloader，采用

https://github.com/habnabit/txsocksx

但该库仅支持Python2

所以使用其他人修改的库

https://github.com/unk2k/txsocksx



#### redis密码校验失败

redis校验用户名，默认为default



#### Request.url is not modifiable, use Request.replace() instead

不能直接在process_response中修改url

即`request.url = newUrl`

需要调用方法__set_url

`request._set_url(url)`



#### 爬虫预期应该一次爬完，但每次都有剩余

在遇到403错误时重新请求，但由于请求一样导致被过滤

使用`request.replace(dont_filter=True)`



#### 代理没问题，但爬取评论时一直超时重试 + 403

原因①

程序在爬取评论和评分时里有如下判断：

取出所有电影ID，**判断该电影目前已经爬取的评论数量是否小于一定数量**，小于的话就重新爬取该电影的评论

然后在执行mongodb操作时数据库数量大，导致操作缓慢，一直超时

**解决：给movieId加上索引**



原因②

403报错是评论超过200条需要登录。。上面的原因1感觉也不知道是不是正确的

**解决：判断start是否大于200**



#### 爬取评论时有时候会一直卡住不动

在获取mongodb数据经常卡住

原因：find的时候不加batch_size每次获取默认101个文档，虽然是这样，但不知道为什么不加就会卡住

加了batch_szie = 200也可以正常获取，就是每次要等挺久的

**解决：改成batch_size = 20**



#### 爬取评论时不能一次性爬取完

find的时候每次请求最多16mb的数据

