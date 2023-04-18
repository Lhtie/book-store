import logging
import os
from pymongo import MongoClient


class Store:
    def __init__(self, db_path):
        self.client = MongoClient('mongodb://localhost:27017/')
        self.mongodb = self.client['store_database']
        self.init_tables()

    def init_tables(self):
        try:
            self.user_collection = self.mongodb['user']
            self.user_store_collection = self.mongodb['user_store']
            self.store_collection = self.mongodb['store']
            self.new_order_collection = self.mongodb['new_order']
            self.new_order_detail_collection = self.mongodb['new_order_detail']
        except Exception as e:
            logging.error(e)

    def get_db(self):
        return self.mongodb


database_instance: Store = None


def init_database(db_path):
    global database_instance
    database_instance = Store(db_path)


def get_db():
    global database_instance
    return database_instance.get_db()
