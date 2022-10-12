用于Github Page网页的仓库

此文档记录一下中间对Hugo的一些操作。

# 图片的处理

TODO 

# 公式的处理

很多主题自带公式的输入功能，但是为了避免更换主题导致原来的markdown无法编译，直接利用Hugo提供的short code功能嵌入Mathjax的代码。

在使用时直接在文档中插入 `{{<mathjax>}}` ，此时会将 `/layouts/shortcodes/mathjax.html` 文件中的代码复制到当前文档。



# 配置方式

## css修改

PS：firefox会自动缓存css文件，刷新时要使用ctrl+F5强制清除缓存。

css所在的文件夹：`static/css/custom.css` 。

