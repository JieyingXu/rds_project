from django.shortcuts import render
# from server.online_shop.forms import *
from online_shop.rds_mysql_apis import *
from django.http import HttpResponse
from django.http import JsonResponse

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

def make_transaction(request):
    # if request.method == 'POST':
    #     form = TransactionForm(request.POST)
    #     if form.is_valid():
    #         transaction_row = {}
    #         transaction_row['transaction_id'] = get_maxid() + 1
    #
    #         product_type, number = form.cleaned_data['product_type'], form.cleaned_data['product_number']
    #         transaction_row['product_type'] = product_type
    #         transaction_row['number'] = int(number)
    #         response = insert_transaction(transaction_row)
    #
    #         remain_shoes_number = get_remains("shoes")
    #         remain_pants_number = get_remains("pants")
    #         context = HttpResponse()
    #         context["form"] = TransactionForm()
    #         context["shoes_number"] = remain_shoes_number
    #         context["pants_number"] = remain_pants_number
    #
    #         if response['number'] == -1:
    #             context["message"] = 'Database Error: Insertion Failed!'
    #         else:
    #             context["message"] = 'Transaction: %s of %s Succeeded!' % \
    #             (number, product_type)
    #         return context
    return HttpResponse("Alive", content_type="text/plain")

def detect(request):
    # print("I am alive!")
    return HttpResponse("Alive", content_type="text/plain")

