from be.model import store
from pymongo import MongoClient

class DBConn:
    def __init__(self):
        self.mongodb = store.get_db()

    def user_id_exist(self, user_id: str) -> bool:
        result = self.mongodb.user.find_one({"user_id": user_id})
        return result is not None

    def book_id_exist(self, store_id: str, book_id: str) -> bool:
        result = self.mongodb.store.find_one({"store_id": store_id, "book_id": book_id})
        return result is not None

    def store_id_exist(self, store_id: str) -> bool:
        result = self.mongodb.user_store.find_one({"store_id": store_id})
        return result is not None
    
    # def new_order_id_exist(self, order_id: str) -> bool:
    #     result = self.mongodb.new_order.find_one({"order_id": order_id})
    #     return result is not None