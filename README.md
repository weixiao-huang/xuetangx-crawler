# 学堂在线视频及字幕爬虫

## Prerequirements

```
pip3 install requests bs4 lxml
```

## 使用方法

```
cp auth.py.ex auth.py
```

登录学堂在线 http://www.xuetangx.com ，然后在 chrome 的 Network 下面的网络请求中随便找一个请求，�右键选择 copy as cURL，然后在这个网站：https://curl.trillworks.com 把 curl 转换为 requests 代码，把其中的 headers 和 cookies 替换 `auth.py` 中的 headers 和 cookies。

然后将 `main.py` 里的 `url` 替换为你想爬取的课程的 url 即可。运行

```
python3 main.py
```

即可实现爬取。