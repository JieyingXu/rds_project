import json
import mysql.connector


def create_database():
    """
    call this function to create database, if the database already exists, it will do nothing
    :return: no return
    """
    cnx = mysql.connector.connect(user='root', password='Jiang0814', host='35.185.39.95')

    cursor = cnx.cursor()
    try:
        cursor.execute(
            "CREATE DATABASE rds CHARACTER SET 'utf8'"
        )
    except mysql.connector.Error as err:
        print("Failed creating database: {}".format(err))
    cursor.close()
    cnx.close()


def create_table():
    """
    create two tables inventory and transaction
    inventory(product_type, remains)
    transaction(transaction_id, product_type, number)
    if the table already exists, it will drop the table and create a new one
    :return: no return
    """
    cnx = mysql.connector.connect(user='root', password='Jiang0814', host='35.185.39.95')
    cursor = cnx.cursor()
    cursor.execute("USE rds")
    cursor.execute("DROP TABLE IF EXISTS inventory")
    cursor.execute("DROP TABLE IF EXISTS transaction")
    cursor.execute("CREATE TABLE `inventory` ("
                   " `product_type` varchar(20) NOT NULL,"
                   " `remains` int NOT NULL)")
    cursor.execute("CREATE TABLE `transaction` ("
                   " `transaction_id` int NOT NULL PRIMARY KEY,"
                   " `product_type` varchar(20) NOT NULL,"
                   " `number` int NOT NULL)")
    cursor.close()
    cnx.close()


def insert_transaction(dic):
    """
    insert a transaction record to the transaction table
    will ignore duplicated transaction id and catch exception
    :param dic: a dictionary with fields (transaction_id, product_type, number)
    :return: no return
    """
    cnx = mysql.connector.connect(user='root', password='Jiang0814', host='35.185.39.95')
    cursor = cnx.cursor()
    cursor.execute("USE rds")
    add_transaction = ("INSERT INTO transaction "
                       "(transaction_id, product_type, number) "
                       "VALUES (%(transaction_id)s, %(product_type)s, %(number)s)")
    try:
        cursor.execute(add_transaction, dic)
        cnx.commit()
        number = dic.get('number')
        product_type = dic.get('product_type')
        cursor.execute("UPDATE inventory SET remains = remains - " + str(number)
                       + " WHERE product_type = '" + product_type + "'")
        cnx.commit()
    except mysql.connector.Error as err:
        print("{}".format(err))
    cursor.close()
    cnx.close()


def insert_inventory():
    """
    insert inventory information(shoes with 100 remains & pants with 100 remains),
    should be called only once at the creation of the table
    :return:
    """
    cnx = mysql.connector.connect(user='root', password='Jiang0814', host='35.185.39.95')
    cursor = cnx.cursor()
    cursor.execute("USE rds")
    add_transaction = ("INSERT INTO inventory "
                       "(product_type, remains) "
                       "VALUES (%(product_type)s, %(remains)s)")
    dic = {
        'product_type': 'shoes',
        'remains': 100
    }
    cursor.execute(add_transaction, dic)
    cnx.commit()
    dic = {
        'product_type': 'pants',
        'remains': 100
    }
    cursor.execute(add_transaction, dic)
    cnx.commit()
    cursor.close()
    cnx.close()


if __name__ == "__main__":
    create_database()
    create_table()
    insert_inventory()
    dic = {
        'transaction_id': 1000,
        'product_type': 'shoes',
        'number': 7
    }
    insert_transaction(dic)
    dic = {
        'transaction_id': 1001,
        'product_type': 'pants',
        'number': 8
    }
    insert_transaction(dic)
    insert_transaction(dic)
