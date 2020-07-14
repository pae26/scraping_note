from bottle import route,run,template,static_file
import sqlite3

@route('/recommend')
def recommend():
    try:
        conn=sqlite3.connect('recommend.sqlite3')
        c=conn.cursor()
        c.execute('SELECT * FROM articles')
        top_articles=c.fetchall()
    except sqlite3.Error as e:
        print('エラー!')
        print(e)
    finally:
        conn.close()

    return template('recommend.html',top_articles=top_articles)

@route('/static/<file_path:path>')
def static(file_path):
    return static_file(file_path,root='./static')

run(host='localhost',port=8080,debug=True,reload=True)