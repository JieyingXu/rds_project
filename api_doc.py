def getmaxid():
    """
    get the largest transaction_id from transaction table, first time call it will return 1000
    :return: the largest transaction_id
    """

def getremains(product_type):
    """
    get remain number of a certain product
    :param product_type: the type you want to query
    :return: the number of this product
    """

def insert_transaction(dic):
    """
    insert a transaction record to the transaction table
    will ignore duplicated transaction id and catch exception
    :param dic: a dictionary with fields (transaction_id, product_type, number)
    :return: a direction which shows the remain number of the product you insert
             (product_type, number). number = -1 if the insert operation is wrong
    """