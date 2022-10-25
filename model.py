import code
import re
from loguru import logger
import sqlite3
from pymongo import MongoClient
from transliterator import TransliterateUkr

class Code:
    def __init__(self, name, code, price = "000", code_n = 0, rowid = 0) -> None:
        self.rowid = int( rowid )
        self.name = name
        self._price = price
        self.code = int( code )
        self.code_n = int( code_n )
        self._tr = TransliterateUkr()


    @property
    def price(self) -> float:
        # if type(self._price) is str:
        #     return float( int(self._price) / 100 )
        # elif type(self._price) is int:
        #     return float( self._price / 100 )
        # else:
        return float( self._price )
            

    @property
    def search_name(self) -> str:
        t = self._tr.transliteration(self.name, spec=True)
        return t.upper()


    def __str__(self) -> str:
        t = f'{self.name} : {self.code}, ціна: {self.price}\n'
        if self.code_n != 0:
            t = f'{self.name} : {self.code}, Н {self.code_n}\n'
        return t


class User:
    def __init__(self, message = None) -> None:
        self.admin = 0
        self.username = ''
        self.chat_id = 0
        if message != None:
            self.build_from_message(message)





    def build_from_message(self, message):
        self.username = str( message.from_user.username )
        self.chat_id = message.chat.id


    def set_admin(self):
        self.admin = 1


    def is_admin(self) -> bool:
        return bool( self.admin )


class Model:
    def __init__(self, path_file_db) -> None:
        self.connect = sqlite3.connect(path_file_db,  check_same_thread=False)
        self.cursor = self.connect.cursor()
        self.tr = TransliterateUkr()

        self.init_tables()


    def init_tables(self) -> None:
        q = ''' 
        CREATE TABLE IF NOT EXISTS codes (
            name TEXT NOT NULL,
            search_name TEXT NOT NULL,
            code INTEGER NOT NULL UNIQUE,
            code_n INTEGER DEFAULT 0,
            price TEXT
        )'''
        self.cursor.execute(q)
        self.connect.commit()
        q = ''' 
        CREATE TABLE IF NOT EXISTS users (
            username TEXT NOT NULL UNIQUE,
            chat_id INTEGER NOT NULL ,
            admin INTEGER DEFAULT 0
        )'''
        self.cursor.execute(q)
        self.connect.commit()


    def add_new_code(self, code: Code) -> Code:
        q = 'insert into codes (name, search_name, code, code_n, price) values (?, ?, ?, ?, ?)'
        self.cursor.execute(q, (code.name, code.search_name, code.code, code.code_n, code.price))
        self.connect.commit()
        self.cursor.execute(f'SELECT rowid, name, code, code_n, price FROM codes WHERE code = {code.code}')
        row = self.cursor.fetchone()
        if row != None:
            return Code(rowid=row[0], name=row[1], code=row[2], code_n=row[3],price=row[4])
        else:
            return Code('Немає товару', 0)


    def add_new_user(self, user: User) -> User:
        logger.debug(user.username)
        q = 'insert into users (username, chat_id, admin) values (?, ?, ?)'
        self.cursor.execute(q, (user.username, user.chat_id, user.admin))
        self.connect.commit()
        self.cursor.execute(f'SELECT * FROM users WHERE username="{user.username}"')
        row = self.cursor.fetchone()
        if row != None:
            u = User()
            u.username = row[0]
            u.chat_id = row[1]
            u.admin = row[2]
            return u
        else:
            return User()


    def is_exists_user(self, user: User) -> bool:
        q = f'select username from users where username = "{user.username}"'
        self.cursor.execute(q)
        return bool(self.cursor.fetchone())


    def all_codes(self) -> list:
        q = 'SELECT * FROM codes ORDER BY name ASC LIMIT 80'
        self.cursor.execute(q)
        codes = []
        for row in self.cursor.fetchall():
            codes.append( Code(name=row[0], code=row[2], code_n=row[3]) )
        return codes


    def search_code(self, search_text: str) -> list:
        codes = []
        search_text = self.tr.transliteration(search_text, spec=True).upper()
        self.cursor.execute(f'SELECT * FROM codes where search_name LIKE "%{search_text}%" LIMIT 80')
        for c in self.cursor.fetchall():
            codes.append( Code(name=c[0], code=c[2], price=c[4]) )
        return codes


    def search_product_for_code(self, code: int) -> list:
        codes = []
        code = int(code)
        self.cursor.execute(f'SELECT * FROM codes where code = {code}')
        for c in self.cursor.fetchall():
            codes.append( Code(name=c[0], code=c[2], price=c[4]) )
        return codes
            

            
class ModelMongo:
    def __init__(self, uri_mongo, database, collection) -> None:
        try:
            self.client = MongoClient(uri_mongo)
            self.db = self.client[database]
            self.collection = self.db[collection]
        except:
            logger.error('Помилка конекту до монго...')
        self.tr = TransliterateUkr()


    def add_new_code(self, code: Code) -> Code:
        q = 'insert into codes (name, search_name, code, code_n, price) values (?, ?, ?, ?, ?)'
        self.cursor.execute(q, (code.name, code.search_name, code.code, code.code_n, code.price))
        self.connect.commit()
        self.cursor.execute(f'SELECT rowid, name, code, code_n, price FROM codes WHERE code = {code.code}')
        row = self.cursor.fetchone()
        if row != None:
            return Code(rowid=row[0], name=row[1], code=row[2], code_n=row[3],price=row[4])
        else:
            return Code('Немає товару', 0)


    def add_new_user(self, user: User) -> User:
        logger.debug(user.username)
        q = 'insert into users (username, chat_id, admin) values (?, ?, ?)'
        self.cursor.execute(q, (user.username, user.chat_id, user.admin))
        self.connect.commit()
        self.cursor.execute(f'SELECT * FROM users WHERE username="{user.username}"')
        row = self.cursor.fetchone()
        if row != None:
            u = User()
            u.username = row[0]
            u.chat_id = row[1]
            u.admin = row[2]
            return u
        else:
            return User()


    def is_exists_user(self, user: User) -> bool:
        q = f'select username from users where username = "{user.username}"'
        self.cursor.execute(q)
        return bool(self.cursor.fetchone())


    def all_codes(self) -> list:
        q = 'SELECT * FROM codes ORDER BY name ASC LIMIT 80'
        self.cursor.execute(q)
        codes = []
        for row in self.cursor.fetchall():
            codes.append( Code(name=row[0], code=row[2], code_n=row[3]) )
        return codes


    def search_code(self, search_text: str) -> list:
        codes = []
        search_text = self.tr.transliteration(search_text, spec=True).upper()
        exp = re.compile(search_text, re.IGNORECASE)
        for doc in self.collection.find({"searchMask": exp}):
            codes.append( Code(name=doc['name'], code=doc['code'], price=doc['price']) )
        return codes


    def search_product_for_code(self, code: int) -> list:
        codes = []
        code = int(code)
        for doc in self.collection.find({"code": code}):
            codes.append( Code(name=doc['name'], code=doc['code'], price=doc['price']) )
        return codes
            