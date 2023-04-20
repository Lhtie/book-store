from pymongo import MongoClient
from be.model import error
from be.model import db_conn


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

    def send_books(self, store_id:str ,order_id:str) -> int:
        json={"store_id": store_id, "order_id": order_id}
        url = urljoin(self.url_prefix, "send_books")
        headers = {"token": self.token}
        r = requests.post(url, headers=headers, json=json)
        return r.status_code
    
    def store_processing_order(self, seller_id: str) -> (int, list):
        json = {"seller_id": seller_id}
        url = urljoin(self.url_prefix, "store_processing_order")
        r = requests.post(url, json=json)
        return r.status_code, r.json().get("result")
    
    def store_history_order(self, store_id: str) -> (int, list):
        json = {"store_id": store_id}
        url = urljoin(self.url_prefix, "store_history_order")
        r = requests.post(url, json=json)
        return r.status_code, r.json().get("result")