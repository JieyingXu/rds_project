import json
import mysql.connector


def get_maxid(host):
    """
    get the largest transaction_id from transaction table, first time call it will return 1000
    :return: the largest transaction_id
    """
    cnx = mysql.connector.connect(user="root", password="Jiang0814", host=host)
    cursor = cnx.cursor()
    cursor.execute("USE rds")
    cursor.execute("SELECT COUNT(transaction_id) from transaction")
    for count in cursor:
        temp = count
    count_result = temp[0]
    if count_result == 0:
        result = 0
        return result
    else:
        cursor.execute("SELECT MAX(transaction_id) from transaction")
        for transaction_id in cursor:
            max_id = transaction_id
        result = max_id[0]
    return result


def get_remains(product_type, host):
    """
    get remain number of a certain product
    :param product_type: the type you want to query, it should be a string('shoes' or 'pants')
    :return: the number of this product
    """
    cnx = mysql.connector.connect(user="root", password="Jiang0814", host=host)
    cursor = cnx.cursor()
    cursor.execute("USE rds")
    cursor.execute("SELECT remains FROM inventory WHERE product_type = '" + product_type + "'")
    for remain in cursor:
        remain_result = remain
    remain_result = remain_result[0]
    print(remain_result)
    return remain_result

def insert_transaction(dic, host):
    """
    insert a transaction record to the transaction table
    will ignore duplicated transaction id and catch exception
    :param dic: a dictionary with fields (transaction_id, product_type, number)
    :return: a direction which shows the remain number of the product you insert
             (product_type, number). number = -1 if the insert operation is wrong
    """
    cnx = mysql.connector.connect(user="root", password="Jiang0814", host=host)
    cursor = cnx.cursor()
    cursor.execute("USE rds")
    add_transaction = ("INSERT INTO transaction "
                       "(transaction_id, product_type, number) "
                       "VALUES (%(transaction_id)s, %(product_type)s, %(number)s)")
    remain_result = 0
    try:
        cursor.execute(add_transaction, dic)
        cnx.commit()
        number = dic.get('number')
        product_type = dic.get('product_type')
        cursor.execute("UPDATE inventory SET remains = remains - " + str(number)
                       + " WHERE product_type = '" + product_type + "'")
        cnx.commit()
        cursor.execute("SELECT remains FROM inventory WHERE product_type = '" + product_type + "'")
        for remain in cursor:
            remain_result = remain
        remain_result = remain_result[0]
        return_dic = {
            'product_type': product_type,
            'number': remain_result
        }
        cursor.close()
        cnx.close()
        print(return_dic)
        return return_dic
    except mysql.connector.Error as err:
        print("{}".format(err))
        product_type = dic.get('product_type')
        return_dic = {
            'product_type': product_type,
            'number': -1
        }
        cursor.close()
        cnx.close()
        print(return_dic)
        return return_dic
