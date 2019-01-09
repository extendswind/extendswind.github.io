#!/bin/python3

import xmlrpc.client
import re
import time

from bs4 import BeautifulSoup


# 读取用户名和密码，也可以直接赋值
# 此处为了上传git仓库做的保密
keyFile = open("cnblogkey", "r")
username = keyFile.readline().strip("\n")
passwd = keyFile.readline().strip("\n")

title = "helloWorld"
content = "<p> test <p>"
tags = "tag1, tag2"

url = 'http://www.cnblogs.com/' + username + '/services/metaweblog.aspx'
# url = 'http://write.blog.csdn.net/xmlrpc/index'

blogProxy = xmlrpc.client.ServerProxy(url)


# get all blog titles
allBlogs = blogProxy.metaWeblog.getRecentPosts('', username, passwd, 10000)
allTitles = set()
for blog in allBlogs:
    allTitles.add(blog["title"])


# 博客园30s内只能发布一篇博客
isPublishWaiting = False

# sitemap中包含了所有post的地址
sitemapfile = open("public/sitemap.xml", "r")
for line in sitemapfile:
    if re.match(".*<loc>.*posts/.*/.*</loc>.*", line) != None:

        # 博客网址
        loc = re.findall("<loc>(.*)</loc>", line)[0].strip("/")

        # 本地路径
        path = "public/posts/" + re.findall("<loc>.*posts/(.*)</loc>", line)[0] + "index.html"

        # 打开博客文件
        file = open(path)
        content = file.read()
        soup = BeautifulSoup(content, features="html5lib")

        # 读取文章名
        title = soup.find("h1",attrs={'class':'title'}).get_text()

        # 读取标签
        tagList = [i.get_text() for i in soup.findAll("a",attrs={'class':'tag'})]
        commaStr = ","
        tags = commaStr.join(tagList)

        # 读取文章内容
        blogContent = str(soup.find("div", attrs={"class":'container entry-content'}))

        # 加转载说明
        blogContent = "<font size='0.9em' color='#009966'>本文通过MetaWeblog自动发布，原文及更新链接：" + "<a href=" + loc +">" + loc + "</a>" + "</font>" + blogContent

        blogProxy.metaWeblog.newPost('', username, passwd, dict(title="test", description="test", mt_keywords="testtag"), True)
 
        if not (title in allTitles):
            print()
            print("//////////")
            print("publish to cnblogs  " + "username:" + username + "   title:" + title)
            if(isPublishWaiting == True):
                # 博客园30s内只能发布一篇博客
                print("waiting 30s for previous publishing")
                time.sleep(31)
                isPublishWaiting = False
            blogProxy.metaWeblog.newPost('', username, passwd, dict(title=title, description=blogContent, mt_keywords=tags), True)
            isPublishWaiting = True
            print("Done")
            print("//////////")






# print(blogProxy.metaWeblog.getRecentPosts('', username, passwd, 1))

# blogProxy.metaWeblog.newPost('', username, passwd, dict(title=title, description=content, mt_keywords=tags), True)


# def publish_html(filename):
#     """Publish a HTML-format post
#     """
#     html_file = codecs.open(filename, 'r', encoding='utf-8')
#     content = html_file.read()

#     title, description = post.parse_html(content)
#     post.new(title, description)


# def newPost(self, title, description, mt_keywords, publish, **kwargs):
#     return self.proxy.metaWeblog.newPost('', self.user, self.passwd, 
#       dict(title=title, description=description, mt_keywords=mt_keywords, **kwargs), publish)

