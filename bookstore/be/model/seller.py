import json
from pymongo import MongoClient
from be.model import error
from be.model import db_conn

from .tokenize import Tokenizer

class Seller(db_conn.DBConn):

    def __init__(self):
        db_conn.DBConn.__init__(self)

    def add_book(self, user_id: str, store_id: str, book_id: str, book_json_str: str, stock_level: int):
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)
            if self.book_id_exist(store_id, book_id):
                return error.error_exist_book_id(book_id)

            self.mongodb.store.insert_one({"store_id": store_id, "book_id": book_id, "book_info": book_json_str,
                                           "stock_level": stock_level})
            
            # insert book into inverted_index
            book_info = json.loads(book_json_str)
            tokenizer = Tokenizer()

            ctx = []
            def insert(raw):
                if not isinstance(raw, str):
                    return
                tokens = tokenizer.forward(raw)
                for token in tokens:
                    ctx.append({"key_ctx": token, "store_id": store_id, "book_id": book_id})

            if "title" in book_info:
                token = book_info["title"]
                if isinstance(token, str):
                    ctx.append({"key_ctx": token, "store_id": store_id, "book_id": book_id})
            if "author" in book_info:
                code, token = tokenizer.parse_author(book_info["author"])
                if code == 200:
                    ctx.append({"key_ctx": token, "store_id": store_id, "book_id": book_id})
            if "publisher" in book_info:
                token = book_info["publisher"]
                if isinstance(token, str):
                    ctx.append({"key_ctx": token, "store_id": store_id, "book_id": book_id})
            if "translator" in book_info:
                token = book_info["translator"]
                if isinstance(token, str):
                    ctx.append({"key_ctx": token, "store_id": store_id, "book_id": book_id})
            if "tags" in book_info:
                tags = book_info["tags"]
                if isinstance(tags, list):
                    for tag in tags:
                        ctx.append({"key_ctx": tag, "store_id": store_id, "book_id": book_id})
            if "author_intro" in book_info:
                insert(book_info["author_intro"])
            if "book_intro" in book_info:
                insert(book_info["book_intro"])
            if "content" in book_info:
                insert(book_info["content"])
            self.mongodb.inverted_index.insert_many(ctx)

        except Exception as e:
            print(str(e))
            return 528, "{}".format(str(e))
        return 200, "ok"

    def add_stock_level(self, user_id: str, store_id: str, book_id: str, add_stock_level: int):
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)
            if not self.book_id_exist(store_id, book_id):
                return error.error_non_exist_book_id(book_id)

            self.mongodb.store.update_one({"store_id": store_id, "book_id": book_id},
                                          {"$inc": {"stock_level": add_stock_level}})
        except Exception as e:
            return 528, "{}".format(str(e))
        return 200, "ok"

    def create_store(self, user_id: str, store_id: str) -> (int, str):
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if self.store_id_exist(store_id):
                return error.error_exist_store_id(store_id)
            self.mongodb.user_store.insert_one({"store_id": store_id, "user_id": user_id})
        except Exception as e:
            return 528, "{}".format(str(e))
        return 200, "ok"

    def send_books(self,store_id,order_id):
        try:
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)
            row = self.mongodb.new_order.find_one({"order_id": order_id})
            if row is None:
                return error.error_invalid_order_id(order_id)
            
            status = row["status"]
            if status != 2:
                return error.error_invalid_order_status(order_id)

            self.mongodb.new_order.update_one({"order_id": order_id}, {"$set": {"status": 3}})
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"