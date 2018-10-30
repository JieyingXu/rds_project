def create_database():
    """
    call this function to create database, if the database already exists, it will do nothing
    :return: no return
    """

def create_table():
    """
    create two tables inventory and transaction
    inventory(product_type, remains)
    transaction(transaction_id, product_type, number)
    if the table already exists, it will drop the table and create a new one
    :return: no return
    """

def getmaxid():
    """
    get the largest transaction_id from transaction table, first time call it will return 1000
    :return: the largest transaction_id
    """

def insert_transaction(dic):
    """
    insert a transaction record to the transaction table
    will ignore duplicated transaction id and catch exception
    :param dic: a dictionary with fields (transaction_id, product_type, number)
    :return: no return
    """

def insert_inventory():
    """
    insert inventory information(shoes with 100 remains & pants with 100 remains),
    should be called only once at the creation of the table
    :return:
    """

example:


	create_database()
    create_table()
    insert_inventory()
    dic = {
        'transaction_id': 0,
        'product_type': 'shoes',
        'number': 7
    }
    dic['transaction_id'] = getmaxid() + 1
    insert_transaction(dic)
    dic = {
        'transaction_id': 0,
        'product_type': 'pants',
        'number': 8
    }
    dic['transaction_id'] = getmaxid() + 1
    insert_transaction(dic)
    insert_transaction(dic)