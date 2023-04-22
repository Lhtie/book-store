from pymongo import MongoClient
import uuid
import json
import logging
from be.model import error
from be.model import db_conn
from be.model.times import get_now_time, add_unpaid_order, delete_unpaid_order, check_order_time
from be.model.order import Order

class Buyer(db_conn.DBConn):
    def __init__(self):
        db_conn.DBConn.__init__(self)
        self.page_size = 20

    def new_order(self, user_id: str, store_id: str, id_and_count: [(str, int)]) -> (int, str, str):
        order_id = ""
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id) + (order_id,)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id) + (order_id,)
            uid = "{}_{}_{}".format(user_id, store_id, str(uuid.uuid1()))
            
            # computer the order's total price, and update the database
            total_price = 0
            for book_id, count in id_and_count:
                row = self.mongodb.store.find_one({"store_id": store_id, "book_id": book_id})
                if row is None:
                    return error.error_non_exist_book_id(book_id) + (order_id,)

                stock_level = row["stock_level"]
                book_info = row["book_info"]
                book_info_json = json.loads(book_info)
                price = book_info_json.get("price")

                if stock_level < count:
                    return error.error_stock_level_low(book_id) + (order_id,)

                self.mongodb.store.update_one({"store_id": store_id, "book_id": book_id},
                                               {"$inc": {"stock_level": -count}})
                self.mongodb.new_order_detail.insert_one({"order_id": uid, "book_id": book_id,
                                                          "count": count, "price": price})
                
                total_price += count * price

            order_time = get_now_time()
            self.mongodb.new_order.insert_one(
                {"order_id": uid, "store_id": store_id, "user_id": user_id, "status": 1, "total_price": total_price, "order_time": order_time})
            order_id = uid
            add_unpaid_order(order_id, order_time)

        except Exception as e:
            logging.info("528, {}".format(str(e)))
            return 528, "{}".format(str(e)), ""
        return 200, "ok", order_id

    def payment(self, user_id: str, password: str, order_id: str) -> (int, str):
        try:
            row = self.mongodb.new_order.find_one({"order_id": order_id})
            if row is None:
                return error.error_invalid_order_id(order_id)

            buyer_id = row["user_id"]
            status = row["status"]
            total_price = row["total_price"]
            order_time = row["order_time"]

            if buyer_id != user_id:
                return error.error_authorization_fail()
            if status != 1:
                return error.error_invalid_order_status()
            # the soft real time cannot handle all the cases, so we need to double check it here to avoid exceed time order
            if check_order_time(order_time) == False:
                delete_unpaid_order(order_id)
                order = Order()
                order.cancel_order(order_id, end_status=0)
                return error.error_invalid_order_id

            row = self.mongodb.user.find_one({"user_id": buyer_id})
            if row is None:
                return error.error_non_exist_user_id(buyer_id)
            balance = row["balance"]
            if password != row["password"]:
                return error.error_authorization_fail()
            
            if balance < total_price:
                return error.error_not_sufficient_funds(order_id)

            self.mongodb.user.update_one({"user_id": buyer_id, "balance": {"$gte": total_price}},
                                         {"$inc": {"balance": -total_price}})
            self.mongodb.new_order.update_one({"order_id": order_id}, {"$set":{"status": 2}})
            delete_unpaid_order(order_id)

        except Exception as e:
            return 528, "{}".format(str(e))

        return 200, "ok"

    def add_funds(self, user_id: str, password: str, add_value: str) -> (int, str):
        try:
            row = self.mongodb.user.find_one({"user_id": user_id})
            if row is None:
                return error.error_authorization_fail()

            if row["password"] != password:
                return error.error_authorization_fail()

            self.mongodb.user.update_one({"user_id": user_id},
                                         {"$inc": {"balance": add_value}})

        except Exception as e:
            return 528, "{}".format(str(e))

        return 200, "ok"
    
    def receive_books(self, user_id: str, password: str, order_id: str) -> (int, str):
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)

            row = self.mongodb.new_order.find_one({"order_id": order_id})
            if row is None:
                return error.error_invalid_order_id(order_id)

            order_id = row["order_id"]
            buyer_id = row["user_id"]
            store_id = row["store_id"]
            status = row["status"]
            total_price = row["total_price"]

            if buyer_id != user_id:
                return error.error_authorization_fail()
            if status != 3:
                return error.error_invalid_order_status(order_id)
            
            row = self.mongodb.user.find_one({"user_id": buyer_id})
            if row is None:
                return error.error_non_exist_user_id(buyer_id)
            if password != row["password"]:
                return error.error_authorization_fail()

            row = self.mongodb.user_store.find_one({"store_id": store_id})
            if row is None:
                return error.error_non_exist_store_id(store_id)
            seller_id = row["user_id"]
            if not self.user_id_exist(seller_id):
                return error.error_non_exist_user_id(seller_id)
            
            self.mongodb.user.update_one({"user_id": seller_id},
                                         {"$inc": {"balance": total_price}})
            
            order = Order()
            order.cancel_order(order_id, end_status=4)
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"

    def cancel_order(self, buyer_id, order_id) -> (int, str):
        try:
            row = self.mongodb.new_order.find_one({"order_id": order_id})
            if row is None:
                return error.error_invalid_order_id(order_id)
            
            if row["status"] != 1:  # we can just cancel the order if the order is unpaid.
                return error.error_invalid_order_status(order_id)

            if not self.user_id_exist(buyer_id):
                return error.error_non_exist_user_id(buyer_id)

            delete_unpaid_order(order_id)
            order = Order()
            order.cancel_order(order_id, end_status=0)

        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"
    
    def query_new_order(self, user_id):
        try:
            if not self.user_id_exist(user_id):
                raise error.error_non_exist_user_id(user_id)

            result = []
            cursor = self.mongodb.new_order.find({"user_id": user_id})
            if len(list(cursor)) != 0:
                for row in cursor:
                    order = {
                        "order_id": row["order_id"],
                        "store_id": row["store_id"],
                        "status": row["status"],
                        "total_price": row["total_price"], 
                        "order_time": row["order_time"]
                    }
                    books = []
                    bookrows = self.mongodb.new_order_detail.find({"order_id": order["order_id"]})
                    for bookrow in bookrows:
                        book = {
                            "book_id": bookrow["book_id"],
                            "count": bookrow["count"]
                        }
                        books.append(book)
                    order["books"] = books
                    result.append(order)
            else:
                result = ["NO Order is Processing"]
        except BaseException as e:
            return 530, "{}".format(str(e)), []
        return 200, "ok", result
    
    def query_history_order(self, user_id):
        try:
            if not self.user_id_exist(user_id):
                raise error.error_non_exist_user_id(user_id)

            result = []
            orders = self.mongodb.history_order.find({'user_id': user_id},{'_id':0})
            for order in orders:
                result.append(order)

        except BaseException as e:
            return 530, "{}".format(str(e)), []
        return 200, "ok", result
    
    # store_id: if not None, retrieve books stored in store_id
    def __find_one_key(self, key: str, store_id: str=None) -> (int, str, set):
        try:
            if store_id is None:
                row = self.mongodb.inverted_index.find({"key_ctx": key})
            else:
                row = self.mongodb.inverted_index.find({"key_ctx": key, "store_id": store_id})
            book_ids = []
            for each in row:
                book_ids.append(each["book_id"])

        except Exception as e:
            return 528, "{}".format(str(e)), set()

        return 200, "ok", set(book_ids)
    
    def __find_book_ids(self, keys: list, sep: bool, page: int, store_id: str=None) -> (int, str, list):
        try:
            book_ids = set()
            for key in keys:
                code, _, upds = self.__find_one_key(key, store_id)
                if code == 200:
                    book_ids.update(upds)
            book_ids = list(sorted(book_ids))
            if sep:
                off = page * self.page_size
                if off >= len(book_ids):
                    book_ids = []
                else:
                    book_ids = book_ids[off:min(len(book_ids), off+self.page_size)]

        except Exception as e:
            return 528, "{}".format(str(e)), []
        
        return 200, "ok", book_ids

    def find(self, keys: list, sep: bool, page: int) -> (int, str, list):
        try:
            code, msg, book_ids = self.__find_book_ids(keys, sep, page)
            if code != 200:
                raise error.error_and_message(code, msg)

            book_infos = []
            for book_id in book_ids:
                row = self.mongodb.store.find_one({"book_id": book_id})
                if row is None:
                    raise error.error_non_exist_book_id(book_id)
                book_infos.append(json.loads(row["book_info"]))

        except Exception as e:
            return 528, "{}".format(str(e)), []
        
        return 200, "ok", book_infos
    
    def find_in_store(self, store_id: str, keys: list, sep: bool, page: int) -> (int, str, list):
        try:
            if not self.store_id_exist(store_id):
                raise error.error_non_exist_store_id(store_id)

            code, msg, book_ids = self.__find_book_ids(keys, sep, page, store_id)
            if code != 200:
                raise error.error_and_message(code, msg)

            book_infos = []
            for book_id in book_ids:
                row = self.mongodb.store.find_one({"store_id": store_id, "book_id": book_id})
                if row is None:
                    raise error.error_non_exist_book_id(book_id)
                book_infos.append(json.loads(row["book_info"]).update(stock_level=row["stock_level"]))

        except Exception as e:
            return 528, "{}".format(str(e)), []
        
        return 200, "ok", book_infos
