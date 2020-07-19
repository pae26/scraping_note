# -*- coding: utf-8 -*-

import os
import requests
import math
import time
import datetime
from collections import Counter
import re
import sqlite3
import numpy as np
from selenium.webdriver import Chrome,ChromeOptions,Remote
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
import MeCab
import matplotlib.pyplot as plt



tagger=MeCab.Tagger('')
tagger.parse('')

pre_url='https://note.com'
base_url='https://note.com/search?context=note&mode=search&q={}&sort={}'
options=ChromeOptions()
options.headless=True
driver=Chrome('/Users/paesongju/Desktop/chromedriver',options=options)


def main():
    keyword='休校'
    body_all=[]
    title_all=[]
    articles_all=[]
    word_count_all=Counter()

    word_count_in_article=[]

    frequency_all_popular=Counter()
    scraping_category(articles_all,keyword,'popular',frequency_all_popular,body_all,title_all,word_count_in_article)
    word_count_all+=frequency_all_popular

    frequency_all_hot=Counter()
    scraping_category(articles_all,keyword,'hot',frequency_all_hot,body_all,title_all,word_count_in_article)
    word_count_all+=frequency_all_hot

    frequency_all_new=Counter()
    scraping_category(articles_all,keyword,'new',frequency_all_new,body_all,title_all,word_count_in_article)
    word_count_all+=frequency_all_new

    frequency_all_like=Counter()
    scraping_category(articles_all,keyword,'like',frequency_all_like,body_all,title_all,word_count_in_article)
    word_count_all+=frequency_all_like

    with open('count_words.txt','w') as file:
        for word,count in word_count_all.most_common(30):
            file.write(word+'\t'+str(count)+'\n')

        
    x=range(1,31)
    y_popular_list=[]
    y_hot_list=[]
    y_new_list=[]
    y_like_list=[]

    for word_count in word_count_all.most_common(30):
        if word_count[0] in frequency_all_popular.keys():
            y_popular_list.append(frequency_all_popular[word_count[0]])
        else:
            y_popular_list.append(0)
        
        if word_count[0] in frequency_all_hot.keys():
            y_hot_list.append(frequency_all_hot[word_count[0]])
        else:
            y_hot_list.append(0)
        
        if word_count[0] in frequency_all_new.keys():
            y_new_list.append(frequency_all_new[word_count[0]])
        else:
            y_new_list.append(0)
        
        if word_count[0] in frequency_all_like.keys():
            y_like_list.append(frequency_all_like[word_count[0]])
        else:
            y_like_list.append(0)
    
    y_popular_count=np.array(y_popular_list)
    y_hot_count=np.array(y_hot_list)
    y_new_count=np.array(y_new_list)
    y_like_count=np.array(y_like_list)
    y_total_count=np.array(y_popular_count+y_hot_count+y_new_count+y_like_count)
    y_max_count=y_total_count[np.argmax(y_total_count)]

    
    #plt.grid(True)
    p_like=plt.bar(x,y_like_count,color="green")
    p_popular=plt.bar(x,y_popular_count,bottom=y_like_count,color="yellow")
    p_hot=plt.bar(x,y_hot_count,bottom=y_like_count+y_popular_count,color="red")
    p_new=plt.bar(x,y_new_count,bottom=y_like_count+y_popular_count+y_hot_count,color="blue")
    plt.ylim(0,y_max_count+100)
    plt.title("frequency_words")
    plt.xlabel("words")
    plt.ylabel("counts")
    plt.legend((p_like,p_popular,p_hot,p_new),("like","popular","hot","new"))
    plt.savefig("static/words_count.png")
    plt.gca().clear()
    


    #総頻出単語
    frequency_all=Counter()
    count_total_frequency(frequency_all,frequency_all_popular,'popular')
    count_total_frequency(frequency_all,frequency_all_hot,'hot')
    count_total_frequency(frequency_all,frequency_all_new,'new')
    count_total_frequency(frequency_all,frequency_all_like,'like')


    #evaluate_all=Counter()
    sum_all=sum(sorted(list(frequency_all.values()),reverse=True)[0:30])
    for word,count in frequency_all.items():
        frequency_all[word]=count/sum_all

    print()
    print('ー最終単語評価値上位10件ー')
    print(frequency_all.most_common(10))

    
    top_words=[]
    for word,count in frequency_all.most_common(100):
        top_words.append(word)
    
    x=range(1,31)
    y_evaluate=[]

    for word_evaluate in frequency_all.most_common(30):
        y_evaluate.append(word_evaluate[1])

    plt.bar(x,y_evaluate)
    plt.title("evaluate_words")
    plt.xlabel("words")
    plt.ylabel("evaluates")
    plt.savefig("static/frequency_words.png")

    
    evaluate_articles(articles_all,top_words,frequency_all,body_all,word_count_in_article)

    
    try:
        conn=sqlite3.connect('recommend.sqlite3')
        c=conn.cursor()
        c.execute('DROP TABLE IF EXISTS articles')
        c.execute('CREATE TABLE articles(id INTEGER PRIMARY KEY AUTOINCREMENT,title char(200),category char(20),like INTEGER,point INTEGER,url char(100),description char(500));')

        for i in range(10):
            title_=articles_all[i]['title']
            category_=''
            if articles_all[i]['category']=='popular':
                category_='人気'
            elif articles_all[i]['category']=='hot':
                category_='急上昇'
            elif articles_all[i]['category']=='new':
                category_='新着'
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
            file.write(word+'\t'+str(count)+'\n')
    
    driver.close()
    driver.quit()


"""
def login_and_get_search_history():
    mailaddress='songju19990426@gmail.com'
    password='zebura0426'
    driver.get(pre_url)
    login_page=driver.find_element_by_css_selector('div.o-navbarTop__navItem.o-navbarTop__navItem--login > a')
    login_page.click()

    time.sleep(5)

    address_box=driver.find_element_by_css_selector('body > main > login > div > section > div > div > form > div > div:nth-child(1) > input')
    password_box=driver.find_element_by_css_selector('body > main > login > div > section > div > div > form > div > div:nth-child(2) > input')

    time.sleep(5)

    address_box.send_keys(mailaddress)
    password_box.send_keys(password)

    login_button=driver.find_element_by_css_selector('body > main > login > div > section > div > div > form > button')
    login_button.click()
"""

#カテゴリー別記事取得
def scraping_category(articles_all,keyword,category,frequency_all,body_all,title_all,word_count_in_article):
    url=base_url.format(keyword,category)
    articles_category=get_articles(url,frequency_all,category,title_all,20,100)
    analysis_articles(articles_category,frequency_all,body_all,category,word_count_in_article)

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
    
    frequency_category_sub=Counter()
    for word,count in frequency_category.items():
        frequency_category_sub[word]=round(count*mag)
    

    frequency_all+=frequency_category_sub



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
        try:
            like=int(d.find_element_by_css_selector('.o-noteStatus__label').text)
        except NoSuchElementException:
            like=0
        
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
def analysis_articles(articles,frequency_all,body,category,word_count_in_article):
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
            word_count_in_article.append(len(words))
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

    with open('analysis_'+category+'.txt','w') as file:
        for word,count in frequency_all.most_common(30):
            file.write(word+':'+str(count)+'\n')
    
    print(frequency_all.most_common(10))



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
    


#総合記事評価
def evaluate_articles(articles_all,top_words,frequency_all,body,word_count_in_article):
    words_count_all=[]
    words_total_all=[]
    frequency_one=Counter()

    #記事単語評価
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
    
    #短文制限
    word_count_in_article_avg=sum(word_count_in_article) / len(word_count_in_article)
    penalty_line=word_count_in_article_avg / 5
    short_articles=[]
    for count in word_count_in_article:
        if count-penalty_line <0:
            short_articles.append(abs(count-penalty_line))
        else:
            short_articles.append(0)
    
    short_articles_sum=sum(short_articles)

    for i in range(len(short_articles)):
        if short_articles[i]==0:
            continue
        relative_count=short_articles[i] / short_articles_sum
        short_articles[i]=short_articles_sum - relative_count


    #記事評価
    point_all=0
    sum_like=0
    sum_point=0
    #単語編
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
    
    #いいね編
    i_=0
    for article in articles_all:
        if(article['category']=='new'):
            article_like=1.2**article['like'] / words_total_all[i_]
        else:
            article_like=article['like'] / words_total_all[i_]

        article['point']=(article['point'] / point_all) + (article_like / sum_like)
        article['point']-=short_articles[i_]
        sum_point+=article['point']

        i_+=1

    

    for article in articles_all:
        article['point']=article['point'] / sum_point

    articles_all.sort(key=lambda x:x['point'],reverse=True)



if __name__=='__main__':
    main()