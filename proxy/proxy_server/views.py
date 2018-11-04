from django.shortcuts import render
from proxy_server.forms import *
import requests

# Create your views here.

def home(request):
    response = requests.get("http://127.0.0.1:8000/home")
    json_res = response.json()
    context = {}
    context["form"] = TransactionForm()
    context["shoes_number"] = json_res["shoes_number"]
    context["pants_number"] = json_res["pants_number"]
    return render(request, 'proxy_server/index.html', context)

def make_transaction(request):
    return render(request, 'proxy_server/index.html', {})

def detect(request):
    return render(request, 'proxy_server/index.html', {})

