import pymysql.cursors
import json
from bottle import *
from uuid import uuid4
from hashlib import sha512


class ConnectAndCommit:
    def __init__(self, query, params):
        self.query = query
        self.params = params
        self.connection = None
        self.cursor = None

    def est_connection(self):
        self.connection = pymysql.connect(
            user='VEF',
            password='ab123',
            host='localhost',
            database='VEF',
            charset='utf8mb4'
        )

    def execute_n_commit(self):
        self.cursor = self.connection.cursor()
        result = self.cursor.execute(self.query, self.params)
        self.connection.commit()
        return result

    def close_connection(self):
        self.cursor.close()
        self.connection.close()


class Data:
    def __init__(self):
        self.errText = None
        self.cac = None

    def try_for_mysql_errors(self, query, params=tuple()):
        try:
            self.cac = ConnectAndCommit(query, params)
            self.cac.est_connection()
            self.cac.execute_n_commit()
            return True
        except pymysql.MySQLError as err:
            self.errText = ("Something went wrong :( Error: {}".format(err))
            if err.args[0] == 1062:
                self.errText = "PÃ¶ntun Ã¾egar til.. (Error: {})".format(err.args[0])
            elif err.args[0] == 1045:
                self.errText = "Tenging viÃ° gagnagrunn ekki leyfÃ°. (Error: {})".format(err.args[0])
            elif err.args[0] == 2003:
                self.errText = "Forrit nÃ¡Ã°i ekki aÃ° tengjast netinu.. " \
                               "Vinsamlegast athugaÃ°u nettenginguna Ã¾Ã­na (Error: {})".format(err.args[0])

            return False

    def send_order(self, customer_fullname, customer_phone, customer_email, nationality, card_number, CVN,
                   card_exp_date, order_date, return_date, car_id, driver_id_nr):
        query = """INSERT INTO orders (customer_fullname, customer_phone, customer_email, nationality, card_number, CVN,
         card_exp_date, order_date, return_date, car_id, driver_id_nr)
        values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        if self.try_for_mysql_errors(query, (customer_fullname, customer_phone, customer_email, nationality,
                                             card_number, CVN, card_exp_date, order_date, return_date, car_id,
                                             driver_id_nr)):
            self.cac.close_connection()
            return True
        self.cac.close_connection()
        return False

    def remove_order(self, id):
        query = "DELETE FROM orders WHERE order_id = %s"
        if self.try_for_mysql_errors(query, (id,)):
            self.cac.close_connection()
            return True
        self.cac.close_connection()
        return False

    def get_order_list(self):
        query = """SELECT * FROM orders"""
        if self.try_for_mysql_errors(query):
            fetch = self.cac.cursor.fetchall()
            self.cac.close_connection()
            return fetch
        return []

    def get_car_list(self):
        query = """SELECT * FROM cars
        inner join car_types on cars.car_type = car_types.type_id
        inner join categories on car_types.category_id = categories.cat_id"""
        if self.try_for_mysql_errors(query):
            fetch = self.cac.cursor.fetchall()
            self.cac.close_connection()
            return fetch
        return []

    def get_car_info(self, id):
        query = """SELECT * FROM cars
                inner join car_types on cars.car_type = car_types.type_id
                inner join categories on car_types.category_id = categories.cat_id
                where cars.car_id = %s"""
        if self.try_for_mysql_errors(query, tuple(id)):
            fetch = self.cac.cursor.fetchall()
            self.cac.close_connection()
            return fetch
        self.cac.close_connection()
        return []

    def user_info_valid(self, username, password):
        query = "SELECT * FROM admin_users WHERE username = %s AND password = %s"
        if self.try_for_mysql_errors(query, (username, password)):
            fetch = self.cac.cursor.fetchall()
            if len(fetch) > 0:
                return True
            return False
        return False

class TokenManager:

    tokens = []

    @staticmethod
    def get_new():
        token = uuid4()
        TokenManager.tokens.append(str(token))
        return token

    @staticmethod
    def exists(token):
        return token in TokenManager.tokens


def post_data_exists(*args):
    for a in args:
        if request.forms.get(a) is None:
            return False
    return True


@route("/api/cars")
def cars():
    data = Data()
    cars = data.get_car_list()
    return json.dumps(cars)


@route("/api/car/<id>")
def car(id):
    data = Data()
    car_info = data.get_car_info(id)
    if len(car_info) > 0:
        return json_dumps(car_info[0])
    return "[]"


@route("/api/order", method="post")
def order():
    if not post_data_exists("customer_fullname", "customer_phone", "customer_email", "nationality", "card_number",
                            "CVN", "card_exp_date", "order_date", "return_date", "car_id", "driver_id_nr"):
        return json.dumps({"order_status": 0, "error_msg": "Vantar upplýsingar"})
    customer_fullname = request.forms.get("customer_fullname")
    customer_phone = request.forms.get("customer_phone")
    customer_email = request.forms.get("customer_email")
    nationality = request.forms.get("nationality")
    card_number = request.forms.get("card_number")
    CVN = request.forms.get("CVN")
    card_exp_date = request.forms.get("card_exp_date")
    order_date = request.forms.get("order_date")
    return_date = request.forms.get("return_date")
    car_id = request.forms.get("car_id")
    driver_id_nr = request.forms.get("driver_id_nr")
    data = Data()
    status = data.send_order(customer_fullname, customer_phone, customer_email, nationality, card_number, CVN, card_exp_date,
                      order_date, return_date, car_id, driver_id_nr)
    return json.dumps({"order_status": status, "error_msg": data.errText})


@route("/api/order/remove/<id>", method="post")
def remove_order(id):
    token = request.forms.get("token")
    if TokenManager.exists(token):
        data = Data()
        status = data.remove_order(id)
        return json.dumps({"status": status, "error_msg": data.errText})
    return json.dumps({"status": 0, "error_msg": "Token does not exist"})


@route("/api/orders", method="post")
def orders():
    token = request.forms.get("token")
    if TokenManager.exists(token):
        data = Data().get_order_list()
        new_data = [[d[0], d[1], d[2], d[3], d[4], d[5], d[6], d[7], str(d[8]),
                     str(d[9]), d[10], d[11]] for d in data]
        return json.dumps(new_data)
    return json.dumps([])


@route("/api/admin/login", method="post")
def admin_login():
    login_status = 0
    token = ""
    username = request.forms.get("username")
    password = request.query.password
    p = sha512()
    p.update(password.encode("utf8"))
    password = p.hexdigest()
    if username is not None and password is not None and Data().user_info_valid(username, password):
        login_status = 1
        token = TokenManager.get_new()
    return json_dumps({"login_status": login_status, "token": str(token)})


@route("/api/download/desktopClient")
def download_desktop_client():
    return static_file("desktop.zip", root="incl/download/")
