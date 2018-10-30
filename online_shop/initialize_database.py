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


def initialization():
	create_database()
    create_table()
    insert_inventory()