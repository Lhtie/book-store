import pytest

from fe.access.buyer import Buyer
from fe.test.gen_book_data import GenBook
from fe.access.new_buyer import register_new_buyer
from fe.access.new_seller import register_new_seller
from fe.access.book import Book
import uuid


class TestFindBooks:
    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        self.seller_id = "test_find_books_seller_id_{}".format(str(uuid.uuid1()))
        self.store_id = "test_find_books_store_id_{}".format(str(uuid.uuid1()))
        self.buyer_id = "test_find_books_buyer_id_{}".format(str(uuid.uuid1()))
        self.password = self.seller_id
        self.buyer = register_new_buyer(self.buyer_id, self.password)
        # self.seller = register_new_seller(self.seller_id, self.password)
        gen_book = GenBook(self.seller_id, self.store_id)
        ok, buy_book_id_list = gen_book.gen(non_exist_book_id=False, low_stock_level=False, max_book_count=5)
        self.buy_book_info_list = gen_book.buy_book_info_list
        self.seller = gen_book.get_seller()
        assert ok

        yield

    def test_find_books_ok(self):
        list = ["数学", "美丽", "三毛"]
        code, result = self.buyer.find(list, False, 0)
        assert code == 200

    def test_find_books_sep_ok(self):
        list = ["数学", "美丽", "三毛"]
        code, result = self.buyer.find(list, True, 0)
        assert code == 200

    def test_find_books_empty(self):
        list = ["xxxx", "++++", "----"]
        code, result = self.buyer.find(list, False, 0)
        assert result == []

    def test_find_books_out_of_pages(self):
        list = ["数学", "美丽", "三毛"]
        code, result = self.buyer.find(list, True, 100)
        assert result == []

    def test_find_in_store_ok(self):
        list = ["数学", "美丽", "三毛"]
        code, result = self.buyer.find_in_store(self.store_id, list, False, 0)
        assert code == 200

    def test_find_in_store_sep_ok(self):
        list = ["数学", "美丽", "三毛"]
        code, result = self.buyer.find_in_store(self.store_id, list, True, 0)
        assert code == 200

    def test_find_in_store_empty(self):
        list = ["xxxx", "++++", "----"]
        code, result = self.buyer.find_in_store(self.store_id, list, True, 0)
        assert result == []

    def test_find_in_store_out_of_pages(self):
        list = ["数学", "美丽", "三毛"]
        code, result = self.buyer.find_in_store(self.store_id, list, True, 100)
        assert result == []

    def test_find_in_store_non_exist_store_id(self):
        list = ["数学", "美丽", "三毛"]
        code, result = self.buyer.find_in_store(self.store_id + "_x", list, False, 0)
        assert code != 200
