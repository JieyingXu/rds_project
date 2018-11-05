from django.shortcuts import render
from proxy_server.forms import *
from django.http import HttpResponse, JsonResponse
import requests

# Create your views here.
SERVER_IP_LIST = ["http://127.0.0.1:8008", "http://127.0.0.1:8080"]
INTERVAL = 1

def home(request, interval):
    # interval = request.GET.get('interval')
    global INTERVAL
    INTERVAL = interval
    for ip in SERVER_IP_LIST:
        try:
            response = requests.get(ip+"/home")
            if response.status_code == requests.codes.ok:
                json_res = response.json()
                context = {}
                context["form"] = TransactionForm()
                context["shoes_number"] = json_res["shoes_number"]
                context["pants_number"] = json_res["pants_number"]
                context["interval"] = INTERVAL
                print('Proxy', context)
                return render(request, 'proxy_server/index.html', context)
            else:
                continue
        # except ValueError:
        #     return HttpResponse("Json Decode Failed", content_type="text/plain")
        # except:
        #     return HttpResponse("Server Connection Failed", content_type="text/plain")
        except:
            continue
    return HttpResponse("Error Detected, Request Failed", content_type="text/plain")


def make_transaction(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            product_type, number = form.cleaned_data['product_type'], form.cleaned_data['product_number']
            for ip in SERVER_IP_LIST:
                try:
                    payload = {'product_type':product_type, 'product_number':number}
                    response = requests.post(ip+'/make_transaction', data=payload)
                    json_res = response.json()
                    context = {}
                    context["form"] = TransactionForm()
                    context["shoes_number"] = json_res["shoes_number"]
                    context["pants_number"] = json_res["pants_number"]
                    context["interval"] = INTERVAL
                    if json_res['code'] == -1:
                        context["message"] = 'Database Error: Insertion Failed!'
                    else:
                        context["message"] = 'Transaction: %s of %s Succeeded!' % \
                        (number, product_type)
                    return render(request, 'proxy_server/index.html', context)
                # except ValueError:
                #     return HttpResponse("Json Decode Failed", content_type="text/plain")
                # except:
                #     return HttpResponse("Server Connection Failed", content_type="text/plain")
                except:
                    continue
            return HttpResponse("Error Detected, Request Failed", content_type="text/plain")
    else:
        return HttpResponse("Make Transaction Cannot Accept GET Request", content_type="text/plain")

def detect(request):
    count = 0
    for ip in SERVER_IP_LIST:
        try:
            requests.get(ip+'/detect')
            count += 1
        except:
            continue
    return JsonResponse({'count': str(count)})


