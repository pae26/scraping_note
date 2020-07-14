# -*- coding: utf-8 -*-

import os
import requests
import time
import datetime
from selenium.webdriver import Chrome,ChromeOptions,Remote
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
import MeCab
from collections import Counter
import re
import sqlite3
import math


tagger=MeCab.Tagger('')
tagger.parse('')

base_url='https://note.com/search?context=note&mode=search&q={}&sort={}'
options=ChromeOptions()
driver=Chrome('/Users/paesongju/Desktop/chromedriver',options=options)


def main():
    #options.headless=True
    keyword='休校'
    body_all=[]
    title_all=[]
    articles_all=[]

    frequency_all_popular=Counter()
    scraping_category(articles_all,keyword,'popular',frequency_all_popular,body_all,title_all)

    frequency_all_hot=Counter()
    scraping_category(articles_all,keyword,'hot',frequency_all_hot,body_all,title_all)

    frequency_all_new=Counter()
    scraping_category(articles_all,keyword,'new',frequency_all_new,body_all,title_all)

    frequency_all_like=Counter()
    scraping_category(articles_all,keyword,'like',frequency_all_like,body_all,title_all)


    #総頻出単語
    frequency_all=Counter()
    count_total_frequency(frequency_all,frequency_all_popular,'popular')
    count_total_frequency(frequency_all,frequency_all_hot,'hot')
    count_total_frequency(frequency_all,frequency_all_new,'new')
    count_total_frequency(frequency_all,frequency_all_like,'like')


    sum_all=sum(sorted(list(frequency_all.values()),reverse=True)[0:30])
    for word,count in frequency_all.items():
        frequency_all[word]=count/sum_all

    print()
    print('ー最終単語評価値上位10件ー')
    print(frequency_all.most_common(10))

    
    top_words=[]
    for word,count in frequency_all.most_common(100):
        top_words.append(word)
    
    evaluate_articles(articles_all,top_words,frequency_all,body_all)

    
    try:
        conn=sqlite3.connect('recommend.sqlite3')
        c=conn.cursor()
        c.execute('DROP TABLE IF EXISTS articles')
        c.execute('CREATE TABLE articles(id INTEGER PRIMARY KEY AUTOINCREMENT,title char(200),category char(20),like INTEGER,point INTEGER,url char(100),description char(500));')

        for i in range(3):
            title_=articles_all[i]['title']
            category_=articles_all[i]['category']
            like_=articles_all[i]['like']
            point_=articles_all[i]['point']
            url_=articles_all[i]['url']
            description_=articles_all[i]['description']

            print('title    :'+title_)
            print('category :'+category_)
            print('point    :'+str(point_))
            print('url      :'+url_)
            print()

            c.execute('INSERT INTO articles(title,category,like,point,url,description) VALUES(?,?,?,?,?,?)',(title_,category_,like_,point_,url_,description_))

            conn.commit()
    except sqlite3.Error as e:
        print('接続エラー!:')
        print(e)
    finally:
        c.close()
        conn.close()

        
    with open('analysis.txt','w') as file:
        for word,count in frequency_all.most_common(30):
            file.write(word+':'+str(count)+'\n')
    
    driver.quit()



#カテゴリー別記事取得
def scraping_category(articles_all,keyword,category,frequency_all,body_all,title_all):
    url=base_url.format(keyword,category)
    articles_category=get_articles(url,frequency_all,category,title_all,30,100)
    analysis_articles(articles_category,frequency_all,body_all,category)

    if category=='like':
        return

    for article in articles_category:
        articles_all.append(article)


#総合単語カウント
def count_total_frequency(frequency_all,frequency_category,category):
    mag=0.0
    if category=='popular':
        mag=0.3
    elif category=='hot':
        mag=0.2
    elif category=='new':
        mag=0.1
    else:
        mag=0.4
    
    for word,count in frequency_category.items():
        count=round(count*mag)
        frequency_category[word]=count

    frequency_all+=frequency_category



#記事取得
def get_articles(url,frequency_all,category,title_all,scroll_page,max_articles):
    driver.get(url)
    assert 'note' in driver.title

    print('カテゴリー:'+category)
    print('ページを読み込んでいます...')
    for i in range(scroll_page):
        driver.implicitly_wait(20)
        driver.execute_script('scroll(0,document.body.scrollHeight)')
        time.sleep(10)

    articles=[]
    article_count=0

    #記事取得
    print('URLを取得しています...')
    for d in driver.find_elements_by_css_selector('.o-timelineNoteItem'):
        title=d.find_element_by_css_selector('h3').text
        if title in title_all:
            continue
        
        title_all.append(title)
        article_count+=1
        url=d.find_element_by_css_selector('a').get_attribute('href')
        like=int(d.find_element_by_css_selector('.o-noteStatus__label').text)
        try:
            description=d.find_element_by_css_selector('.o-textNote__description').text
        except NoSuchElementException:
            description=''
        articles.append({
            'title':title,
            'category':category,
            'like':like,
            'point':0,
            'url':url,
            'description':description,
        })
        time.sleep(2)

        if article_count==max_articles:
            break
    
    return articles



#形態素解析
def analysis_articles(articles,frequency_all,body,category):
    article_count=len(articles)
    print('記事数:'+str(article_count))
    article_count=0

    for article in articles:
        s=''
        url=article['url']
        print(str(article_count+1)+'番目の記事を解析しています...')
        driver.get(url)
        driver.implicitly_wait(20)
        time.sleep(2)
        article_count+=1
        try:
            for p in driver.find_elements_by_css_selector('.o-noteContentText__body p'):
                driver.implicitly_wait(20)
                s+=p.text

            words=get_words(s)
            ng_words=['人','月','自分','相手']
            for ng in ng_words:
                while ng in words:
                    words.remove(ng) 
            check_counter=Counter()
            check_counter.update(words)
            for word,count in check_counter.items():
                if count>20:
                    check_counter[word]=20
            
            frequency_all+=check_counter
            body.append(s)
            driver.implicitly_wait(20)
        except StaleElementReferenceException as e:
            print('エラー！')
        

    print('処理が完了しました！')

    #top_words=[]
    with open('analysis_'+category+'.txt','w') as file:
        for word,count in frequency_all.most_common(30):
            #top_words.append(word)
            file.write(word+':'+str(count)+'\n')
    
    print(frequency_all.most_common(10))
    


#記事評価
def evaluate_articles(articles_all,top_words,frequency_all,body):
    words_count_all=[]
    words_total_all=[]
    frequency_one=Counter()
    for i in range(len(articles_all)):
        words_count_one=[]
        words=get_words(body[i])
        frequency_one.update(words)
        for top_word in top_words:
            if top_word in list(frequency_one.keys()):
                if frequency_one[top_word]>20:
                    frequency_one[top_word]=20

                words_count_one.append(math.log10(frequency_one[top_word]))
            else:
                words_count_one.append(0)
        
        words_total_one=len(words)+1
        words_total_all.append(words_total_one)
        words_count_all.append(words_count_one)
        frequency_one.clear()

    point_all=0
    sum_like=0
    sum_point=0
    for i in range(len(articles_all)):
        point=0
        for j in range(len(top_words)):
            point+=(frequency_all[top_words[j]] * words_count_all[i][j]) / words_total_all[i]
        
        articles_all[i]['point']=point
        point_all+=point
        if(articles_all[i]['category']=='new'):
            sum_like+=1.2**articles_all[i]['like']
        else:
            sum_like+=articles_all[i]['like']
    
    i_=0
    for article in articles_all:
        if(article['category']=='new'):
            article_like=1.2**article['like'] / words_total_all[i_]
        else:
            article_like=article['like'] / words_total_all[i_]

        article['point']=(article['point'] / point_all) + (article_like / sum_like)
        sum_point+=article['point']

        i_+=1

    for article in articles_all:
        article['point']=article['point'] / sum_point

    articles_all.sort(key=lambda x:x['point'],reverse=True)



#形態素解析
def get_words(content):

    words = []
    p = re.compile('[a-zA-Z]+')

    node = tagger.parseToNode(content)
    while node:
        pos, pos_sub1 = node.feature.split(',')[:2]
        #固有名詞または一般名詞の場合のみwordsに追加する。
        if (pos == '名詞' and pos_sub1 in ('固有名詞', '一般')) and not p.fullmatch(node.surface):
            words.append(node.surface)
        node = node.next

    return words



if __name__=='__main__':
    main()