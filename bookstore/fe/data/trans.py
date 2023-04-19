import sqlite3
from pymongo import MongoClient

# 连接到SQLite3数据库
sqlite_db_path = 'book.db'
sqlite_conn = sqlite3.connect(sqlite_db_path)
sqlite_cursor = sqlite_conn.cursor()

# 连接到MongoDB数据库
mongo_client = MongoClient('mongodb://localhost:27017/')
mongo_db = mongo_client['bookstore_database']

book_collection = mongo_db['book']
book_collection.delete_many({})
    
sqlite_cursor.execute("SELECT * FROM book")
for row in sqlite_cursor:
    book = {
        'id': row[0],
        'title': row[1],
        'author': row[2],
        'publisher': row[3],
        'original_title': row[4],
        'translator': row[5],
        'pub_year': row[6],
        'pages': row[7],
        'price': row[8],
        'currency_unit': row[9],
        'binding': row[10],
        'isbn': row[11],
        'author_intro': row[12],
        'book_intro': row[13],
        'content': row[14],
        'tags': row[15],
        'picture': row[16],
    }
    book_collection.insert_one(book)

# 关闭数据库连接
sqlite_conn.close()
mongo_client.close()