import json
from be.model import error
from be.model import db_conn
from be.model import store

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

            store_inst = store.Store_Table(store_id=store_id, book_id=book_id, book_info=book_json_str,
                                           stock_level=stock_level)
            self.db.insert(store_inst)
            
            # insert book into inverted_index
            book_info = json.loads(book_json_str)
            tokenizer = Tokenizer()
            ctx = []

            def insert_one(token):
                ctx_inst = store.Inverted_Index_Table(key_ctx=token, store_id=store_id, book_id=book_id)
                ctx.append(ctx_inst)
            def insert(raw):
                if not isinstance(raw, str):
                    return
                tokens = tokenizer.forward(raw)
                for token in tokens:
                    ctx_inst = store.Inverted_Index_Table(key_ctx=token, store_id=store_id, book_id=book_id)
                    ctx.append(ctx_inst)

            if "title" in book_info:
                token = book_info["title"]
                if isinstance(token, str):
                    insert_one(token)
            if "author" in book_info:
                code, token = tokenizer.parse_author(book_info["author"])
                if code == 200:
                    insert_one(token)
            if "publisher" in book_info:
                token = book_info["publisher"]
                if isinstance(token, str):
                    insert_one(token)
            if "translator" in book_info:
                token = book_info["translator"]
                if isinstance(token, str):
                    insert_one(token)
            if "tags" in book_info:
                tags = book_info["tags"]
                if isinstance(tags, list):
                    for tag in tags:
                        insert_one(tag)
            if "author_intro" in book_info:
                insert(book_info["author_intro"])
            if "book_intro" in book_info:
                insert(book_info["book_intro"])
            if "content" in book_info:
                insert(book_info["content"])

            self.db.insert_many(ctx)

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

            session = self.db.DbSession()
            s = session.query(store.Store_Table).filter(
                store.Store_Table.store_id == store_id, store.Store_Table.book_id == book_id
            ).first()
            if s is not None:
                s.stock_level += add_stock_level
                session.add(s)
                session.commit()
            session.close()

        except Exception as e:
            return 528, "{}".format(str(e))
        return 200, "ok"

    def create_store(self, user_id: str, store_id: str) -> (int, str):
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if self.store_id_exist(store_id):
                return error.error_exist_store_id(store_id)
            
            user_store = store.User_Store_Table(user_id=user_id, store_id=store_id)
            self.db.insert(user_store)

        except Exception as e:
            return 528, "{}".format(str(e))
        return 200, "ok"

    def send_books(self,store_id,order_id):
        try:
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)
            
            session = self.db.DbSession()
            row = session.query(store.New_Order_Table).filter_by(order_id=order_id).first()
            if row is None:
                session.close()
                return error.error_invalid_order_id(order_id)
            
            status = row.status
            if status != 2:
                session.close()
                return error.error_invalid_order_status(order_id)

            row.status = 3
            session.add(row)
            session.commit()
            session.close()
            
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"