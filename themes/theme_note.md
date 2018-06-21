
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
