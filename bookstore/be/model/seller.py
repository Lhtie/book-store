from pymongo import MongoClient
from be.model import error


class Seller:

    def __init__(self):
        client = MongoClient('mongodb://localhost:27017/')
        self.mongodb = client['bookstore_database']

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
        except Exception as e:
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