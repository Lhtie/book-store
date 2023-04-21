from fe.access.new_seller import register_new_seller
from fe.access.new_buyer import register_new_buyer
from fe.access import book
import uuid

seller_id = "test_add_books_seller_id_{}".format(str(uuid.uuid1()))
store_id = "test_add_books_store_id_{}".format(str(uuid.uuid1()))
buyer_id = "test_new_order_buyer_id_{}".format(str(uuid.uuid1()))
password = seller_id
seller = register_new_seller(seller_id, password)
buyer = register_new_buyer(buyer_id, password)

code = seller.create_store(store_id)
assert code == 200
book_db = book.BookDB()
books = book_db.get_book_info(0, 50)

for b in books:
    code = seller.add_book(store_id, 0, b)
    assert code == 200

print("started")
code, selected = buyer.find(["小说", "中国"], sep=True, page=1)
for book in selected:
    print(book["title"])