import pytest

from fe.access.buyer import Buyer
from fe.test.gen_book_data import GenBook
from fe.access.new_buyer import register_new_buyer
from fe.access.book import Book
import uuid

seller_id = "test_payment_seller_id_{}".format(str(uuid.uuid1()))
store_id = "test_payment_store_id_{}".format(str(uuid.uuid1()))
buyer_id = "test_payment_buyer_id_{}".format(str(uuid.uuid1()))
password = seller_id
gen_book = GenBook(seller_id, store_id)
ok, buy_book_id_list = gen_book.gen(non_exist_book_id=False, low_stock_level=False, max_book_count=5)
buy_book_info_list = gen_book.buy_book_info_list
assert ok
b = register_new_buyer(buyer_id, password)
buyer = b
code, order_id = b.new_order(store_id, buy_book_id_list)
assert code == 200
total_price = 0
for item in buy_book_info_list:
    book: Book = item[0]
    num = item[1]
    if book.price is None:
        continue
    else:
        total_price = total_price + book.price * num

code = buyer.add_funds(total_price)
assert code == 200
code = buyer.payment(order_id)
assert code == 200