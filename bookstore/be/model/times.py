import time
from be.model.order import Order

def get_now_time():
    now_time = int(time.time())
    return now_time

time_limit = 30
unpaid_orders = {}

def add_unpaid_order(orderID, order_time):
    unpaid_orders[orderID] = order_time
    return 200, "ok"

def delete_unpaid_order(orderID):
    try:
        unpaid_orders.pop(orderID)
    except BaseException as e:
        return 530, "{}".format(str(e))
    return 200, "ok"

def check_order_time(order_time):
    cur_time = get_now_time()
    time_diff = cur_time - order_time
    if time_diff > time_limit:
        return False
    else:
        return True

def time_exceed_delete():
    del_temp=[]
    order = Order()
    for (oid,tim) in unpaid_orders.items():
        if check_order_time(tim) == False:
            del_temp.append(oid)
    for oid in del_temp:
        delete_unpaid_order(oid)
        order.cancel_order(oid, end_status=0)
    return 0
