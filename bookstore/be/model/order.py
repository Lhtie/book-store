from be.model import db_conn
from be.model import error
from be.model import store

class Order(db_conn.DBConn):
    def __init__(self):
        db_conn.DBConn.__init__(self)

    def cancel_order(self,order_id, end_status):
        try:
            session = self.db.DbSession()
            row = session.query(store.New_Order_Table).filter_by(order_id=order_id).first()
            if row is None:
                session.close()
                return error.error_invalid_order_id(order_id)
            session.delete(row)
            session.commit()
            session.close()

            store_id = row.store_id
            order = store.History_Order_Table(
                order_id=row.order_id,
                user_id=row.user_id,
                store_id=row.store_id,
                total_price=row.total_price,
                order_time=row.order_time,
                status=row.status
            )
            self.db.insert(order)

            session = self.db.DbSession()
            cursor = session.query(store.New_Order_Detail_Table).filter_by(order_id=order_id).all()
            session.query(store.New_Order_Detail_Table).filter_by(order_id=order_id).delete()
            session.commit()
            session.close()

            books = []
            for row in cursor:
                book = {
                    "book_id" : row.book_id,
                    "count" : row.count
                }
                if end_status == 0:
                    if not self.book_id_exist(store_id, book["book_id"]):
                        return error.error_non_exist_book_id(book["book_id"]) + (order_id,)

                    session = self.db.DbSession()
                    res = session.query(store.Store_Table).filter_by(store_id=store_id, book_id=book["book_id"]).first()
                    res.stock_level += book["count"]
                    session.add(res)
                    session.commit()
                    session.close()

                    books.append(store.History_Order_Books_Table(order_id=order_id, book_id=book["book_id"], count=book["count"]))
            
            self.db.insert_many(books)

        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"
