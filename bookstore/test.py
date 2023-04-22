import pytest

from fe.access.buyer import Buyer
from fe.test.gen_book_data import GenBook
from fe.access.new_buyer import register_new_buyer
from fe.access.new_seller import register_new_seller
from fe.access.book import Book
import uuid
import time

seller_id = "test_orders_seller_id_{}".format(str(uuid.uuid1()))
store_id = "test_orders_store_id_{}".format(str(uuid.uuid1()))
buyer_id = "test_orders_buyer_id_{}".format(str(uuid.uuid1()))
password = seller_id
# self.seller = register_new_seller(self.seller_id, self.password)
gen_book = GenBook(seller_id, store_id)
ok, buy_book_id_list = gen_book.gen(non_exist_book_id=False, low_stock_level=False, max_book_count=5)
buy_book_info_list = gen_book.buy_book_info_list
seller = gen_book.get_seller()
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

# code = buyer.cancel_order(buyer_id, order_id)
# assert code == 200
# code, result = buyer.query_new_order(buyer_id)
# # assert result == ["NO Order is Processing"]
# code, result = buyer.query_history_order(buyer_id)
# assert code == 200

# code = buyer.add_funds(total_price)
# assert code == 200
# code = buyer.payment(order_id)
# assert code == 200
# code = seller.send_books(store_id, order_id)
# assert code == 200
# code = buyer.receive_books(buyer_id, password, order_id)
# assert code == 200

# code, result = buyer.query_new_order(buyer_id)
# assert result == ["NO Order is Processing"]

# code, result = buyer.query_new_order(buyer_id)
# assert code == 200

time.sleep(60)
code, result = buyer.query_new_order(buyer_id)
assert result == ["NO Order is Processing"]
print(result)
code, result = buyer.query_history_order(buyer_id)
assert code == 200
print(result)