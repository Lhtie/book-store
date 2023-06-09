import jwt
import time
import logging
from be.model import error
from be.model import db_conn
from be.model import store

def jwt_encode(user_id: str, terminal: str) -> str:
    encoded = jwt.encode(
        {"user_id": user_id, "terminal": terminal, "timestamp": time.time()},
        key=user_id,
        algorithm="HS256",
    )
    return encoded.encode("utf-8").decode("utf-8")


def jwt_decode(encoded_token, user_id: str) -> str:
    decoded = jwt.decode(encoded_token, key=user_id, algorithms="HS256")
    return decoded


class User(db_conn.DBConn):
    token_lifetime: int = 3600

    def __init__(self):
        db_conn.DBConn.__init__(self)

    def __check_token(self, user_id, db_token, token) -> bool:
        try:
            if db_token != token:
                return False
            jwt_text = jwt_decode(encoded_token=token, user_id=user_id)
            ts = jwt_text["timestamp"]
            if ts is not None:
                now = time.time()
                if self.token_lifetime > now - ts >= 0:
                    return True
        except jwt.exceptions.InvalidSignatureError as e:
            logging.error(str(e))
            return False

    def register(self, user_id: str, password: str):
        try:
            if self.user_id_exist(user_id):
                raise error.error_exist_user_id(user_id)
            terminal = "terminal_{}".format(str(time.time()))
            token = jwt_encode(user_id, terminal)

            user_data = store.User_Table(
                user_id=user_id,
                password=password,
                balance=0,
                token=token,
                terminal=terminal
            )
            self.db.insert(user_data)

        except Exception as e:
            logging.error(str(e))
            return error.error_exist_user_id(user_id)
        return 200, "ok"

    def check_token(self, user_id: str, token: str) -> (int, str):
        session = self.db.DbSession()
        user = session.query(store.User_Table).filter_by(user_id=user_id).first()
        if user is None:
            session.close()
            return error.error_authorization_fail()
        db_token = user.token
        session.close()
        if not self.__check_token(user_id, db_token, token):
            return error.error_authorization_fail()
        return 200, "ok"

    def check_password(self, user_id: str, password: str) -> (int, str):
        session = self.db.DbSession()
        user = session.query(store.User_Table).filter_by(user_id=user_id).first()
        if user is None:
            session.close()
            return error.error_authorization_fail()

        if password != user.password:
            session.close()
            return error.error_authorization_fail()
        
        session.close()
        return 200, "ok"

    def login(self, user_id: str, password: str, terminal: str) -> (int, str, str):
        token = ""
        try:
            code, message = self.check_password(user_id, password)
            if code != 200:
                return code, message, ""

            token = jwt_encode(user_id, terminal)
            session = self.db.DbSession()
            update_result = session.query(store.User_Table).filter_by(user_id=user_id)\
                                    .update({"token": token, "terminal": terminal})
            session.commit()
            session.close()
            if update_result == 0:
                return error.error_authorization_fail() + ("", )
        except Exception as e:
            return 528, "{}".format(str(e)), ""
        return 200, "ok", token

    def logout(self, user_id: str, token: str) -> bool:
        try:
            code, message = self.check_token(user_id, token)
            if code != 200:
                return code, message

            terminal = "terminal_{}".format(str(time.time()))
            dummy_token = jwt_encode(user_id, terminal)

            session = self.db.DbSession()
            update_result = session.query(store.User_Table).filter_by(user_id=user_id)\
                                    .update({"token": dummy_token, "terminal": terminal})
            session.commit()
            session.close()
            if update_result == 0:
                return error.error_authorization_fail()
        except Exception as e:
            return 528, "{}".format(str(e))
        return 200, "ok"

    def unregister(self, user_id: str, password: str) -> (int, str):
        try:
            code, message = self.check_password(user_id, password)
            if code != 200:
                return code, message

            session = self.db.DbSession()
            delete_result = session.query(store.User_Table).filter_by(user_id=user_id).delete()
            session.commit()
            if delete_result != 1:
                return error.error_authorization_fail()
        except Exception as e:
            return 528, "{}".format(str(e))
        return 200, "ok"

    def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        try:
            code, message = self.check_password(user_id, old_password)
            if code != 200:
                return code, message

            terminal = "terminal_{}".format(str(time.time()))
            token = jwt_encode(user_id, terminal)

            session = self.db.DbSession()
            update_result = session.query(store.User_Table).filter_by(user_id=user_id)\
                                    .update({"password": new_password,
                                                "token": token,
                                                "terminal": terminal})
            session.commit()
            session.close()
            if update_result == 0:
                return error.error_authorization_fail()
        except Exception as e:
            return 528, "{}".format(str(e))
        return 200, "ok"