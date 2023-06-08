from urllib import parse
from lxml import etree
import requests
import csv
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import jieba
import matplotlib.font_manager as fm
import urllib3

# 禁用安全请求警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Wangyiyun(object):
    def __init__(self, types, years, pages):
        # 初始化函数，设置初始参数
        self.types = types  # 歌单类型
        self.years = years  # 歌单排序方式
        self.pages = pages  # 需要爬取的页面数量
        self.limit = 35  # 每页显示的歌单数量
        self.offset = 0  # 偏移量，用于分页
        self.url = "https://music.163.com/discover/playlist/?"  # 网易云音乐歌单页面URL

    def set_header(self):
        # 设置请求头
        self.header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36",
            "Referer": "https://music.163.com/",
            "Upgrade-Insecure-Requests": '1',
        }
        return self.header

    def set_params(self, page):
        # 设置请求参数，包括歌单类型、排序方式、每页数量和偏移量
        self.offset = self.limit * (page - 1)
        self.params = {
            "cat": self.types,
            "order": self.years,
            "limit": self.limit,
            "offset": self.offset,
        }
        return self.params

    def parsing_codes(self):
        # 解析网页代码，提取歌单标题、作者、播放量和链接信息
        page = etree.HTML(self.code)
        self.title = page.xpath('//div[@class="u-cover u-cover-1"]/a[@title]/@title')
        self.author = page.xpath('//p/a[@class="nm nm-icn f-thide s-fc3"]/text()')
        self.listen = page.xpath('//span[@class="nb"]/text()')
        self.link = page.xpath('//div[@class="u-cover u-cover-1"]/a[@href]/@href')

    def get_code(self):
        # 发送GET请求，获取网页代码
        self.new_url = self.url + parse.urlencode(self.params)
        self.code = requests.get(
            url=self.new_url,
            headers=self.header,
            data=self.params,
            verify=False,
        ).text

    def crawl_pages(self):
        # 爬取多个页面的歌单信息，并将结果保存到CSV文件中
        with open('yinyue.csv', 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            for i in range(self.pages):
                page = i + 1
                self.set_params(page)
                self.set_header()
                self.get_code()
                self.parsing_codes()
                data = list(zip(self.title, self.author, self.listen, self.link))
                writer.writerows(data)

        extracted_data = self.extract_data()
        self.generate_wordcloud(extracted_data)
        self.visualize_data(extracted_data)
        self.save_data(extracted_data, 'wangyiyun.csv')

    def extract_data(self):
        # 提取数据并进行预处理
        data = pd.read_csv('yinyue.csv', encoding='utf-8-sig', names=['title', 'author', 'listen_num', 'link'], skiprows=1)
        data_extracted = data.copy()
        data_extracted['listen_num'] = data_extracted['listen_num'].str.strip('万').astype(float)  # 将播放量中的万去掉并转换为浮点型
        data_extracted = data_extracted[['title', 'listen_num', 'link', 'author']]  # 保留标题、播放量、链接和作者列

        # 只保留每一页播放量最高的歌单，取前10个
        data_extracted = data_extracted.groupby('listen_num').first().reset_index()
        data_extracted = data_extracted.sort_values('listen_num', ascending=False).head(10)

        return data_extracted

    def generate_wordcloud(self, data_extracted):
        # 生成词云图
        titles = data_extracted['title']
        text = ' '.join(jieba.cut(' '.join(titles), cut_all=False))  # 使用jieba进行分词并拼接为一个字符串
        font_path = 'SimHei.ttf'  # 字体文件路径
        wordcloud = WordCloud(width=800, height=400, background_color='white', font_path=font_path).generate(text)  # 创建词云对象
        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.savefig('词云图.png')  # 保存词云图
        plt.show()

    def visualize_data(self, data_extracted):
        # 可视化数据，绘制柱状图
        font_path = 'SimHei.ttf'  # 字体文件路径
        plt.rcParams['font.family'] = fm.FontProperties(fname=font_path).get_name()

        plt.figure(figsize=(10, 6))
        plt.bar(data_extracted['title'], data_extracted['listen_num'])
        plt.xticks(rotation=90)
        plt.xlabel('歌单名称')
        plt.ylabel('播放数量')
        plt.title('播放量最高的前10个歌单')
        plt.tight_layout()
        plt.savefig('柱状图.png')  # 保存柱状图
        plt.show()

    def save_data(self, data_extracted, filename):
        # 将提取的数据保存到CSV文件中
        data_extracted.rename(
            columns={"title": "歌单名称", "listen_num": "歌单播放量", "link": "歌单链接", "author": "用户名称"},
            inplace=True)
        data_extracted.to_csv(filename, index=False, encoding='utf-8-sig')


if __name__ == '__main__':
    types = "摇滚"  # 歌单类型
    years = "hot"  # 歌单排序方式
    pages = 5  # 需要爬取的页面数量
    music = Wangyiyun(types, years, pages)
    music.crawl_pages()
