#!/bin/python3

import xmlrpc.client
import re


username = 'fly2wind'
passwd = '1111111111l_'

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


# 获取hugo生成的所有blog
sitemapfile = open("public/sitemap.xml", "r")
for line in sitemapfile:
    if re.match(".*<loc>.*post.*</loc>.*", line) != None:
        path = "public/posts/" + re.findall("<loc>.*posts/(.*)</loc>", line)[0] + "index.html"
        print(path)

        file = open(path)
        content = file.read()
        title = re.findall("<h1 class='title'>(.*)</h1>", content)[0]
        print(title)

        tag = re.findall("<a class='tag'.*>(.*)</a>", content)
        commaStr = ","
        tags = commaStr.join(tag)
        print(tags)

        if not (title in allTitles):
            print("publish to cnblogs  " + "username:" + username + "   title:" + title)
            blogProxy.metaWeblog.newPost('', username, passwd, dict(title=title, description=content, mt_keywords=tags), True)

        break




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

