# movieSearchSystem



## 说明
原本是用作毕设的  
但最后改了题目，只进行到了数据爬取部分  
mongodb数据地址： 8.129.178.143:27017 账号：movie 密码：movie  
数据已经备份，请放心查看（没有比较好的下载下来的方式，所以直接放数据库账号密码  
数据大小1.4gb
数据大概在1000w左右 
演员20w  
评分880w  
用户85w  
电影10w  

<img src="https://ikaros-picture.oss-cn-shenzhen.aliyuncs.com/typora/20210402142821.png">


### 遇到的问题



#### 代理无法访问豆瓣

http/https不行，需要使用socks5的代理
（why？？我还以为是代理有问题换了一天的代理。。

#### requests库请求豆瓣乱码

请求头`Accept-Encoding`不能包含br

[跳转链接](https://blog.csdn.net/u011423145/article/details/92836441)



#### 如何在Scrapy中使用socks5代理
