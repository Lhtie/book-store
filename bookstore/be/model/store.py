import logging
import uuid
from sqlalchemy import create_engine, Column, String, Integer, Text, Date
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()

class User_Table(Base):
    __tablename__ = "user"
    user_id = Column(Text, primary_key=True, unique=True, index=True, nullable=False)
    password = Column(Text, nullable=False)
    balance = Column(Integer, nullable=False)
    token = Column(Text, nullable=False)
    terminal = Column(Text, nullable= False)

class User_Store_Table(Base):
    __tablename__ = "user_store"
    user_id = Column(Text, primary_key=True, index=True, nullable=False)
    store_id = Column(Text, primary_key=True, index=True, nullable=False)

class Store_Table(Base):
    __tablename__ = "store"
    store_id = Column(Text, primary_key=True, index=True, nullable=False)
    book_id = Column(Text, primary_key=True, index=True, nullable=False)
    book_info = Column(Text, nullable=False)
    stock_level = Column(Integer, nullable=False)

class New_Order_Table(Base):
    __tablename__ = "new_order"
    order_id = Column(Text, primary_key=True, unique=True, index=True, nullable=False)
    user_id = Column(Text, nullable=False)
    store_id = Column(Text, nullable=False)
    status = Column(Integer, nullable=False)
    total_price = Column(Integer, nullable=False)
    order_time = Column(Integer, nullable=False)

class New_Order_Detail_Table(Base):
    __tablename__ = "new_order_detail"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(Text, index=True, nullable=False)
    book_id = Column(Text, nullable=False)
    count = Column(Integer, nullable=False)
    price = Column(Integer, nullable=False)

class History_Order_Table(Base):
    __tablename__ = "history_order"
    order_id = Column(Text, primary_key=True, unique=True, index=True, nullable=False)
    user_id = Column(Text, nullable=False)
    store_id = Column(Text, nullable=False)
    total_price = Column(Integer, nullable=False)
    status = Column(Integer, nullable=False)
    order_time = Column(Integer, nullable=False)

class History_Order_Books_Table(Base):
    __tablename__ = "history_order_books"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(Text, index=True, nullable=False)
    book_id = Column(Text, nullable=False)
    count = Column(Text, nullable=False)

class Inverted_Index_Table(Base):
    __tablename__ = "inverted_index"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    key_ctx = Column(Text, index=True, nullable=False)
    store_id = Column(Text, nullable=False)
    book_id = Column(Text, nullable=False)

class Store:
    def __init__(self):
        self.engine = create_engine("postgresql://postgres:postgres@127.0.0.1:5432/bookstore",
            echo=True,
            pool_size=8, 
            pool_recycle=60*30
        )
        self.DbSession = sessionmaker(bind=self.engine)
        self.init_tables()

    def init_tables(self):
        try:
            Base.metadata.drop_all(self.engine)
            Base.metadata.create_all(self.engine)

        except Exception as e:
            logging.error(e)

    def insert(self, inst):
        session = self.DbSession()
        session.add(inst)
        session.commit()
        session.close()

    def insert_many(self, inst_list):
        session = self.DbSession()
        for inst in inst_list:
            session.add(inst)
        session.commit()
        session.close()


database_instance: Store = None


def init_database():
    global database_instance
    database_instance = Store()


def get_db():
    global database_instance
    return database_instance