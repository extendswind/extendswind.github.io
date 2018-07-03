
# 修改主题中的配置

一般不建议直接修改主题文件夹下的文件（避免主题更新一类的问题），可以将主题文件夹下的文件复制到博客根目录下对应文件夹内进行覆盖。

如对文章目录（toc）进行修改时，将主题目录下(针对minimo主题) layouts/partials/entry/toc.html复制到hugo根目录下的layouts/partitial/entry/toc.html，然后修改。此时编译时会对主题内文件覆盖。

修改css时，minimo主题能够在config.toml文件中指定覆盖的custom.css文件位置，默认在/static/css/custom.css。

# layout directory

{{  }} 一种写函数的方式，貌似感觉和lisp的方式有点像，前面是函数后面是参数，函数可以作为参数。

## index.html

主页相关

## layouts/_default/single.html

每一篇博客的页面


## layouts/partials

可以作为一部分嵌入到其他的网页

如在index.html文件中加入下面的代码后，会将header.html中的内容复制到相应的位置
{{ partial "header.html" . }}


# params

读取config.toml文件中的参数时，一般使用

读取markdown文件上方的头(front matter)中的参数时，使用.Params.参数名访问。
