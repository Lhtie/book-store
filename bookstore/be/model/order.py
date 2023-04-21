from be.model import db_conn
from be.model import error

class Order(db_conn.DBConn):
    def __init__(self):
        db_conn.DBConn.__init__(self)

    def cancel_order(self,order_id, end_status):
        try:
            row = self.mongodb.new_order.find_one({"order_id": order_id})
            if row is None:
                return error.error_invalid_order_id(order_id)
            self.mongodb.new_order.delete_one({"order_id": order_id})

            order = {
                "order_id" : row['order_id'],
                "user_id" : row['user_id'],
                "store_id" : row['store_id'],
                "total_price" : row['total_price'],
                "order_time" : row['order_time'],
                "status" : end_status
            }

            books = []
            cursor = self.mongodb.new_order_detail.find({"order_id": order_id})
            self.mongodb.new_order_detail.delete_many({"order_id": order_id})

            for row in cursor:
                book = {
                    "book_id" : row["book_id"],
                    "count" : row["count"]
                }
                if end_status == 0:
                    if not self.book_id_exist(order["store_id"], book["book_id"]):
                        return error.error_non_exist_book_id(book["book_id"]) + (order_id,)

                    self.mongodb.store.update_one({"store_id": order["store_id"], "book_id": book["book_id"]},
                                                {"$inc": {"stock_level": book["count"]}})
                books.append(book)

            order["books"] = books
            self.mongodb.history_order.insert_one(order)
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"
