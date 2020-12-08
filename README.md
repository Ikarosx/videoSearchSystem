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