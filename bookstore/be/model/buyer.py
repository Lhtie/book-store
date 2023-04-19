from pymongo import MongoClient
import uuid
import json
import logging
from be.model import error


class Buyer:
    def __init__(self):
        client = MongoClient('mongodb://localhost:27017/')
        self.mongodb = client['bookstore_database']

    def new_order(self, user_id: str, store_id: str, id_and_count: [(str, int)]) -> (int, str, str):
        order_id = ""
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id) + (order_id,)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id) + (order_id,)
            uid = "{}_{}_{}".format(user_id, store_id, str(uuid.uuid1()))

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

            self.mongodb.new_order.insert_one({"order_id": uid, "store_id": store_id, "user_id": user_id})
            order_id = uid
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
            store_id = row["store_id"]

            if buyer_id != user_id:
                return error.error_authorization_fail()

            row = self.mongodb.user.find_one({"user_id": buyer_id})
            if row is None:
                return error.error_non_exist_user_id(buyer_id)
            balance = row["balance"]
            if password != row["password"]:
                return error.error_authorization_fail()

            row = self.mongodb.user_store.find_one({"store_id": store_id})
            if row is None:
                return error.error_non_exist_store_id(store_id)

            seller_id = row["user_id"]

            if not self.user_id_exist(seller_id):
                return error.error_non_exist_user_id(seller_id)

            cursor = self.mongodb.new_order_detail.find({"order_id": order_id})
            total_price = 0
            for row in cursor:
                count = row["count"]
                price = row["price"]
                total_price = total_price + price * count

            if balance < total_price:
                return error.error_not_sufficient_funds(order_id)

            self.mongodb.user.update_one({"user_id": buyer_id, "balance": {"$gte": total_price}},
                                         {"$inc": {"balance": -total_price}})
            self.mongodb.user.update_one({"user_id": seller_id},
                                         {"$inc": {"balance": total_price}})

            self.mongodb.new_order.delete_one({"order_id": order_id})
            self.mongodb.new_order_detail.delete_many({"order_id": order_id})

        except Exception as e:
            return 528, "{}".format(str(e))

        return 200, "ok"

    def add_funds(self, user_id, password, add_value) -> (int, str):
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

    def user_id_exist(self, user_id: str):
        result = self.mongodb.user.find_one({"user_id": user_id})
        return result is not None

    def store_id_exist(self, store_id: str):
        result = self.mongodb.user_store.find_one({"store_id": store_id})
        return result is not None