import uuid
import json
import logging
from be.model import store
from be.model import error
from be.model import db_conn
from be.model.times import get_now_time, add_unpaid_order, delete_unpaid_order, check_order_time
from be.model.order import Order
from sqlalchemy import func

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
                session = self.db.DbSession()
                row = session.query(store.Store_Table).filter_by(store_id=store_id, book_id=book_id).first()
                if row is None:
                    session.close()
                    return error.error_non_exist_book_id(book_id) + (order_id,)

                stock_level = row.stock_level
                book_info = row.book_info
                book_info_json = json.loads(book_info)
                price = book_info_json.get("price")

                if stock_level < count:
                    session.close()
                    return error.error_stock_level_low(book_id) + (order_id,)

                row.stock_level -= count
                session.add(row)
                session.commit()
                session.close()
                
                new_order_detail = store.New_Order_Detail_Table(order_id=uid, book_id=book_id, count=count, price=price)
                self.db.insert(new_order_detail)
                
                total_price += count * price

            order_time = get_now_time()
            new_order = store.New_Order_Table(order_id=uid, store_id=store_id, user_id=user_id, 
                                              status=1, total_price=total_price, order_time=order_time)
            self.db.insert(new_order)

            order_id = uid
            add_unpaid_order(order_id, order_time)

        except Exception as e:
            logging.info("528, {}".format(str(e)))
            return 528, "{}".format(str(e)), ""
        return 200, "ok", order_id

    def payment(self, user_id: str, password: str, order_id: str) -> (int, str):
        try:
            session = self.db.DbSession()
            row = session.query(store.New_Order_Table).filter_by(order_id=order_id).first()
            session.close()
            if row is None:
                return error.error_invalid_order_id(order_id)

            buyer_id = row.user_id
            status = row.status
            total_price = row.total_price
            order_time = row.order_time

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

            session = self.db.DbSession()
            row = session.query(store.User_Table).filter_by(user_id=buyer_id).first()
            if row is None:
                session.close()
                return error.error_non_exist_user_id(buyer_id)
            balance = row.balance
            if password != row.password:
                session.close()
                return error.error_authorization_fail()
            
            if balance < total_price:
                session.close()
                return error.error_not_sufficient_funds(order_id)

            row.balance -= total_price
            session.add(row)
            session.query(store.New_Order_Table).filter_by(order_id=order_id).update({'status': 2})

            session.commit()
            session.close()
            delete_unpaid_order(order_id)

        except Exception as e:
            return 528, "{}".format(str(e))

        return 200, "ok"

    def add_funds(self, user_id: str, password: str, add_value: str) -> (int, str):
        try:
            session = self.db.DbSession()
            row = session.query(store.User_Table).filter_by(user_id=user_id).first()
            if row is None:
                session.close()
                return error.error_authorization_fail()

            if row.password != password:
                session.close()
                return error.error_authorization_fail()

            row.balance += add_value
            session.add(row)
            session.commit()
            session.close()

        except Exception as e:
            return 528, "{}".format(str(e))

        return 200, "ok"
    
    def receive_books(self, user_id: str, password: str, order_id: str) -> (int, str):
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)

            session = self.db.DbSession()
            row = session.query(store.New_Order_Table).filter_by(order_id=order_id).first()
            session.close()
            if row is None:
                return error.error_invalid_order_id(order_id)

            order_id = row.order_id
            buyer_id = row.user_id
            store_id = row.store_id
            status = row.status
            total_price = row.total_price

            if buyer_id != user_id:
                return error.error_authorization_fail()
            if status != 3:
                return error.error_invalid_order_status(order_id)
            
            session = self.db.DbSession()
            row = session.query(store.User_Table).filter_by(user_id=buyer_id).first()
            session.close()
            if row is None:
                return error.error_non_exist_user_id(buyer_id)
            if password != row.password:
                return error.error_authorization_fail()

            session = self.db.DbSession()
            row = session.query(store.User_Store_Table).filter_by(store_id=store_id).first()
            session.close()
            if row is None:
                return error.error_non_exist_store_id(store_id)
            seller_id = row.user_id
            if not self.user_id_exist(seller_id):
                return error.error_non_exist_user_id(seller_id)
            
            session = self.db.DbSession()
            row = session.query(store.User_Table).filter_by(user_id=seller_id).first()
            row.balance += total_price
            session.commit()
            session.close()
            
            order = Order()
            order.cancel_order(order_id, end_status=4)
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"

    def cancel_order(self, buyer_id, order_id) -> (int, str):
        try:
            session = self.db.DbSession()
            row = session.query(store.New_Order_Table).filter_by(order_id=order_id).first()
            session.close()
            if row is None:
                return error.error_invalid_order_id(order_id)
            
            if row.status != 1:  # we can just cancel the order if the order is unpaid.
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

            session = self.db.DbSession()
            cursor = session.query(store.New_Order_Table).filter_by(user_id=user_id).all()
            session.close()
            results = []
            if len(list(cursor)) != 0:
                for row in cursor:
                    order = {
                        "order_id": row.order_id,
                        "store_id": row.store_id,
                        "status": row.status,
                        "total_price": row.total_price, 
                        "order_time": row.order_time
                    }
                    books = []
                    session = self.db.DbSession()
                    bookrows = session.query(store.New_Order_Detail_Table).filter_by(order_id=order["order_id"]).all()
                    session.close()
                    for bookrow in bookrows:
                        book = {
                            "book_id": bookrow.book_id,
                            "count": bookrow.count
                        }
                        books.append(book)
                    order["books"] = books
                    results.append(order)
            else:
                results = ["NO Order is Processing"]
        except BaseException as e:
            return 530, "{}".format(str(e)), []
        return 200, "ok", results
    
    def query_history_order(self, user_id):
        try:
            if not self.user_id_exist(user_id):
                raise error.error_non_exist_user_id(user_id)

            results = []
            session = self.db.DbSession()
            orders = session.query(store.History_Order_Table).filter_by(user_id=user_id).all()
            for order in orders:
                result = dict(
                    order_id=order.order_id,
                    user_id=order.user_id,
                    store_id=order.store_id,
                    total_price=order.total_price,
                    status=order.status,
                    order_time=order.order_time
                )
                books = session.query(func.array_agg(store.History_Order_Books_Table.book_id), 
                                      func.array_agg(store.History_Order_Books_Table.count))\
                    .filter_by(order_id=order.order_id)\
                    .group_by(store.History_Order_Books_Table.order_id).first()
                result["books"] = [dict(book_id=x, count=y) for x, y in zip(books[0], books[1])]
                results.append(result)

        except BaseException as e:
            print(str(e))
            return 530, "{}".format(str(e)), []
        return 200, "ok", results
    
    # store_id: if not None, retrieve books stored in store_id
    def __find_one_key(self, key: str, store_id: str=None) -> (int, str, set):
        try:
            session = self.db.DbSession()
            if store_id is None:
                row = session.query(store.Inverted_Index_Table).filter_by(key_ctx=key).all()
            else:
                row = session.query(store.Inverted_Index_Table).filter_by(key_ctx=key, store_id=store_id).all()
            session.close()
            book_ids = []
            for each in row:
                book_ids.append(each.book_id)

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
            session = self.db.DbSession()
            for book_id in book_ids:
                row = session.query(store.Store_Table).filter_by(book_id=book_id).first()
                if row is None:
                    raise error.error_non_exist_book_id(book_id)
                book_infos.append(json.loads(row.book_info))
            session.close()

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
            session = self.db.DbSession()
            for book_id in book_ids:
                row = session.query(store.Store_Table).filter_by(store_id=store_id, book_id=book_id).first()
                if row is None:
                    raise error.error_non_exist_book_id(book_id)
                book_infos.append(json.loads(row.book_info).update(stock_level=row.stock_level))

        except Exception as e:
            return 528, "{}".format(str(e)), []
        
        return 200, "ok", book_infos
