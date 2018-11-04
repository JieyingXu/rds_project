from django.shortcuts import render
from proxy_server.forms import *
from django.http import HttpResponse, JsonResponse
import requests

# Create your views here.
SERVER_IP_LIST = ["http://127.0.0.1:8000"]

def home(request):
    try:
        response = requests.get(SERVER_IP_LIST[0]+"/home")
        if response.status_code == requests.codes.ok:
            json_res = response.json()
            context = {}
            context["form"] = TransactionForm()
            context["shoes_number"] = json_res["shoes_number"]
            context["pants_number"] = json_res["pants_number"]
            print('Proxy', context)
            return render(request, 'proxy_server/index.html', context)
        else:
            return HttpResponse("Server error", content_type="text/plain")
    except ValueError:
        return HttpResponse("Json Decode Failed", content_type="text/plain")
    except:
        return HttpResponse("Server Connection Failed", content_type="text/plain")


def make_transaction(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            product_type, number = form.cleaned_data['product_type'], form.cleaned_data['product_number']
            try:
                payload = {'product_type':product_type, 'product_number':number}
                response = requests.post(SERVER_IP_LIST[0]+'/make_transaction', data=payload)
                json_res = response.json()
                context = {}
                context["form"] = TransactionForm()
                context["shoes_number"] = json_res["shoes_number"]
                context["pants_number"] = json_res["pants_number"]
                if json_res['code'] == -1:
                    context["message"] = 'Database Error: Insertion Failed!'
                else:
                    context["message"] = 'Transaction: %s of %s Succeeded!' % \
                    (number, product_type)
                return render(request, 'proxy_server/index.html', context)
            except ValueError:
                return HttpResponse("Json Decode Failed", content_type="text/plain")
            except:
                return HttpResponse("Server Connection Failed", content_type="text/plain")
    else:
        return HttpResponse("Make Transaction Cannot Accept GET Request", content_type="text/plain")

def detect(request):
    try:
        response = requests.get(SERVER_IP_LIST[0]+'/detect')
        json_res = response.json()
        if json_res['code'] == '1':
            return JsonResponse({'code':'1'})
        else:
            return JsonResponse({'code':'Unknown Error'})
    except:
        return JsonResponse({'code':'0'})


