# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
import csv
from multiprocessing import Queue
import threading
import random
from time import sleep
import pymysql

User_Agent = [
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.106 Safari/537.36",
    "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_8; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50",
    "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:2.0.1) Gecko/20100101 Firefox/4.0.1",
    "Mozilla/5.0 (Windows NT 6.1; rv:2.0.1) Gecko/20100101 Firefox/4.0.1"]

HEADERS = {
    'User-Agent': User_Agent[random.randint(0, 4)],
    # 'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:55.0) Gecko/201002201 Firefox/55.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate, br',
    'Cookie': '',
    'Connection': 'keep-alive',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache'
}
csvfile = open('去哪儿景点.csv', 'w', encoding='utf-8', newline='')
writer = csv.writer(csvfile)
writer.writerow(["区域", "名称", "景点id", "类型", "级别", "热度", "地址", "特色", "经纬度"])


def create():
    db = pymysql.connect(host='localhost', user='root', password='825365', port=3306, db='spiders')
    cursor = db.cursor()
    cursor.execute("DROP TABLE IF EXISTS info")
    sql = 'CREATE TABLE IF NOT EXISTS info(name VARCHAR(255) NOT NULL, addr VARCHAR(255) NOT NULL, satisfy VARCHAR(255) NOT NULL, comments VARCHAR(255) NOT NULL, price VARCHAR(255) NOT NULL)'
    cursor.execute(sql)
    db.close()


def insert(value):
    db = pymysql.connect("localhost", "root", "825365", "spiders")
    cursor = db.cursor()
    sql = "INSERT INTO info(name,addr,satisfy,comments,price) VALUES (%s, %s,  %s, %s, %s)"
    try:
        cursor.execute(sql, value)
        db.commit()
        print('插入数据成功')
    except:
        db.rollback()
        print("插入数据失败")
    db.close()


def download_page(url):  # 下载页面
    try:
        data = requests.get(url, headers=HEADERS, allow_redirects=True).content  # 请求页面，获取要爬取的页面内容
        return data
    except:
        pass


# 下载页面 如果没法下载就 等待1秒 再下载
def download_soup_waitting(url):
    try:
        response = requests.get(url, headers=HEADERS, allow_redirects=True, timeout=5)
        # print(response.status_code)
        if response.status_code == 200:
            html = response.content
            html = html.decode("utf-8")
            soup = BeautifulSoup(html, "html.parser")
            return soup
        else:
            sleep(1)
            print("等待ing")
            return download_soup_waitting(url)
    except:
        return ""


def getTypes():
    types = ["浪漫圣诞", "温泉", "滑雪", "名胜风光", "境外精选", "电话WIFI", "赏花田园", "古镇园林", "主题乐园", "家庭亲子", "演出表演", "城市生活", "拜佛祈福", "元旦", "节假日旅游胜地", "万圣狂欢"]
    for type in types:
        url = "http://menpiao.tuniu.com/s_" + type
        print(url)
        getType(type, url)


def getType(type, url):
    soup = download_soup_waitting(url)
    sleep(1)
    print("*"*100)
    # print("soup:", soup)
    try:
        list_items = soup.findAll('li', attrs={'class': 'list_item'})
        # print("list_items", list_items)
        for list_item in list_items:
            addr = list_item.find('p', attrs={'class': 'mp_addr'})  # 地址
            name = list_item.find('h3')
            name = name.find('a')  # 景点名称
            satisfys = list_item.find('p', attrs={'class': 'ticket'})
            satisfy = satisfys.find('strong', attrs={'class': 't_ticket'})
            comment = satisfys.find('span', attrs={'class': 'f_4e9700'})
            price = list_item.find('span', attrs={'class': 'price f_yh'})
            if name and addr and satisfy and comment and price:
                value = [name.text, addr.text.replace('[查看地图]', '').strip().replace('景点地址：', ''), satisfy.text, comment.text.replace('，', ''), price.text]
            else:
                value = [None, None, None, None, None]
            print(value)
            insert(value)
        page_bottom = soup.find('div', attrs={'class': 'page-bottom'})
        pages = page_bottom.findAll('a')
        for page in pages:
            if page.text == "下一页":
                nextpage = page_bottom.find('span', attrs={'class': 'page-cur'})
                next_url = "http://menpiao.tuniu.com/s_" + type + '/page' + str(int(nextpage.text)+1)
                print("下一页:", next_url)
                getType(type, next_url)
    except:
        pass


if __name__ == '__main__':
    create()
    getTypes()


