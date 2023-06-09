from be.model import store

class DBConn:
    def __init__(self):
        self.db = store.get_db()

    def user_id_exist(self, user_id: str) -> bool:
        session = self.db.DbSession()
        result = session.query(store.User_Table).filter_by(user_id=user_id).all()
        session.close()
        return len(result) > 0

    def book_id_exist(self, store_id: str, book_id: str) -> bool:
        session = self.db.DbSession()
        result = session.query(store.Store_Table).filter_by(store_id=store_id, book_id=book_id).all()
        session.close()
        return len(result) > 0

    def store_id_exist(self, store_id: str) -> bool:
        session = self.db.DbSession()
        result = session.query(store.User_Store_Table).filter_by(store_id=store_id).all()
        session.close()
        return len(result) > 0
    
    def new_order_id_exist(self, order_id: str) -> bool:
        session = self.db.DbSession()
        result = session.query(store.New_Order_Table).filter_by(order_id=order_id).all()
        session.close()
        return len(result) > 0