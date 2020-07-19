from bottle import route,run,template,static_file
import sqlite3


@route('/recommend')
def recommend():
    elements=[]

    try:
        conn=sqlite3.connect('recommend.sqlite3')
        c=conn.cursor()
        c.execute('SELECT * FROM articles')
        top_articles=c.fetchall()
    except sqlite3.Error as e:
        print('エラー!')
        print(e)
    finally:
        c.close()
        conn.close()
    
    count_words=[]
    with open('count_words.txt','r') as file:
        for row in file:
            count_words.append(row)
    
    evaluates=[]
    with open('analysis.txt','r') as file:
        for row in file:
            evaluates.append(row)

    elements.append(top_articles)
    elements.append(count_words)
    elements.append(evaluates)


    return template('recommend.html',elements=elements)



@route('/static/<file_path:path>')
def static(file_path):
    return static_file(file_path,root='./static')



run(host='localhost',port=8080,debug=True,reload=True)