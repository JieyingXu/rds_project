from django.shortcuts import render
# from server.online_shop.forms import *
from online_shop.rds_mysql_apis import *
from django.http import HttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


# Create your views here.
def home(request):
    # transaction_form = TransactionForm()
    remain_shoes_number = get_remains("shoes")
    remain_pants_number = get_remains("pants")
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
        print("From Server: product type->%s, product number->%s" % (product_type, product_number))
        transaction_row = {}
        transaction_row['transaction_id'] = get_maxid() + 1
        transaction_row['product_type'] = product_type
        transaction_row['number'] = int(product_number)

        response = insert_transaction(transaction_row)
        remain_shoes_number = get_remains("shoes")
        remain_pants_number = get_remains("pants")

        context = {}
        context["code"] = response['number']
        context["shoes_number"] = remain_shoes_number
        context["pants_number"] = remain_pants_number
        print("From server:", context)
        return JsonResponse(context)

def detect(request):
    # print("I am alive!")
    context = {'code': '1'}
    return HttpResponse("Alive", content_type="text/plain")

