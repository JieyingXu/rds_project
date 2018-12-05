from django.shortcuts import render
# from server.online_shop.forms import *
from online_shop.rds_mysql_apis import *
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

SQL_CONFIG = {"http://127.0.0.1:8008": "35.185.39.95", "http://127.0.0.1:8080": "35.224.182.68", "http://127.0.0.1:8800":"35.193.252.106"}

# Create your views here.
@csrf_exempt
def home(request):
    # transaction_form = TransactionForm()
    server_ip = request.POST.get('server_ip')
    remain_shoes_number = get_remains("shoes", SQL_CONFIG.get(server_ip))
    remain_pants_number = get_remains("pants", SQL_CONFIG.get(server_ip))
    context = {}
    context["shoes_number"] = remain_shoes_number
    context["pants_number"] = remain_pants_number
    # data = json.dumps(context)
    print("From server:", context)
    return JsonResponse(context)

@csrf_exempt
def make_transaction(request):
    if request.method == 'POST':
        product_type = request.POST.get('product_type')
        product_number = request.POST.get('product_number')
        server_ip = request.POST.get('server_ip')
        print("From Server: product type->%s, product number->%s" % (product_type, product_number))
        transaction_row = {}
        max_id_plus1 = get_maxid(SQL_CONFIG.get(server_ip)) + 1
        transaction_row['transaction_id'] = max_id_plus1
        transaction_row['product_type'] = product_type
        transaction_row['number'] = int(product_number)

        response = insert_transaction(transaction_row, SQL_CONFIG.get(server_ip))
        remain_shoes_number = get_remains("shoes", SQL_CONFIG.get(server_ip))
        remain_pants_number = get_remains("pants", SQL_CONFIG.get(server_ip))

        context = {}
        context["code"] = response['number']
        context["shoes_number"] = remain_shoes_number
        context["pants_number"] = remain_pants_number
        context["transaction_id"] = max_id_plus1
        print("From server:", context)
        return JsonResponse(context)

def detect(request):
    # print("I am alive!")
    return JsonResponse({'code':'1'})

@csrf_exempt
def update(request):
    remains = request.POST.get('checkpoint')
    server_ip = request.POST.get('server_ip')
    req_record = json.loads(remains)
    for transaction in req_record:
        transaction_row = {}
        transaction_row['transaction_id'] = transaction["id"]
        transaction_row['product_type'] = transaction["type"]
        transaction_row['number'] = transaction["number"]
        insert_transaction(transaction_row, SQL_CONFIG.get(server_ip))
    return JsonResponse({'code':'1'})


