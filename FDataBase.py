import math
import re
import time
import sqlite3
from flask import url_for


class FDataBase:
    def __init__(self, db):
        self.__db = db
        self.__cur = db.cursor()

    def get_menu(self):
        sql = '''SELECT * FROM mainmenu'''
        try:
            self.__cur.execute(sql)
            res = self.__cur.fetchall()
            if res:
                return res
        except:
            print('get_menu(): DB reading error')
        return []

    def add_post(self, title, text, url):
        try:
            tm = math.floor(time.time())
            self.__cur.execute(f"SELECT COUNT() as `count` FROM posts WHERE url LIKE '{url}'")
            res = self.__cur.fetchone()
            if res['count'] > 0:
                print("Статья с таким URL уже существует")
                return False
            self.__cur.execute('''INSERT INTO posts VALUES(NULL, ?, ?, ?, ?)''', (title, text, url, tm))
            self.__db.commit()
        except sqlite3.Error as e:
            print("Ошибка добавления статьи в БД: "+str(e))
            return False
        return True

    def get_post(self, alias):
        try:
            self.__cur.execute(f"SELECT title,text,time FROM posts WHERE url LIKE '{alias}' LIMIT 1")
            res = self.__cur.fetchone()
            if res:
                base = url_for('static', filename='images')
                text = re.sub(r"(?P<tag><img\s+[^>]*src=)(?P<quote>[\"'])(?P<url>.+?)(?P=quote)>",
                              "\\g<tag>" + base + "/\\g<url>>",
                              res['text'])
                # print(text)
                return (res['title'], text, res['time'])
        except sqlite3.Error as e:
            print('get_post(): DB reading error '+str(e))
        return (False, False, False)

    def get_posts_announce(self):
        try:
            self.__cur.execute('''SELECT id,title,text,url FROM posts ORDER BY time DESC''')
            res = self.__cur.fetchall()
            if res:
                return res
        except sqlite3.Error as e:
            print('get_post(): DB reading error '+e)
        return []

    def add_user(self, name, email, hpsw):
        try:
            self.__cur.execute(f"SELECT COUNT() as `count` FROM users WHERE email LIKE '{email}'")
            res = self.__cur.fetchone()
            if res['count'] > 0:
                print('Пользователь с таким email уже существует')
                return False
            else:
                tm = math.floor(time.time())
                self.__cur.execute("INSERT INTO users VALUES(NULL, ?, ?, ?, NULL, ?)", (name, email, hpsw, tm))
                self.__db.commit()
        except sqlite3.Error as e:
            print("add_user(): Ошибка добавления в БД "+str(e))
            return False
        return True

    def get_user(self, user_id):
        try:
            self.__cur.execute(f"SELECT * FROM users WHERE id ==  {user_id} LIMIT 1")
            res = self.__cur.fetchone()
            if not res:
                print("get_user(): Пользователь не найден")
                return False
            return res
        except sqlite3.Error as e:
            print("get_user(): Ощибка чтения из БД "+str(e))
        return False

    def get_user_by_email(self, email):
        try:
            self.__cur.execute(f"SELECT * FROM users WHERE email LIKE  '{email}' LIMIT 1")
            res = self.__cur.fetchone()
            if not res:
                print("get_user_by_mail(): Пользователь не найден")
                return False
            return res
        except sqlite3.Error as e:
            print("get_user_by_mail(): Ощибка чтения из БД: "+str(e))
        return False

    def update_user_avatar(self, avatar, user_id):
        if not avatar:
            return False
        try:
            binary = sqlite3.Binary(avatar)
            self.__cur.execute("UPDATE users SET avatar = ? WHERE id == ?", (binary,user_id))
            self.__db.commit()
        except sqlite3.Error as e:
            print("Ошибка обновления аватара в БД: "+str(e))
            return False
        return True
