from django.shortcuts import render
from proxy_server.forms import *
from django.http import HttpResponse, JsonResponse
import requests
import threading, time
import os

# Create your views here.
SERVER_IP_LIST = ["http://127.0.0.1:8008", "http://127.0.0.1:8080", "http://127.0.0.1:8800"]
MASTER = 0

MASTER_SWITCH = 0
REQ_RECORD = []
CHECKPOINT_FILE = os.path.join('.', 'proxy_checkpoint.csv')

class CheckPointThread(threading.Thread):
    def run(self):
        while True:
            global SERVER_IP_LIST
            global MASTER
            time.sleep(60)
            if MASTER_SWITCH == 0:
                for i,ip in enumerate(SERVER_IP_LIST):
                    if i != MASTER:
                        send_checkpoint(ip)

thread1 = CheckPointThread()
thread1.start()

def home(request):
    # interval = request.GET.get('interval')
    global SERVER_IP_LIST
    global MASTER
    ip = SERVER_IP_LIST[MASTER]
    try:
        # payload = {'server_ip':ip}
        # response = requests.post(ip+'/home', data=payload)
        response = requests.get(ip+'/home')
        json_res = response.json()
        context = {}
        context["form"] = TransactionForm()
        context["shoes_number"] = json_res["shoes_number"]
        context["pants_number"] = json_res["pants_number"]
        return render(request, 'proxy_server/index.html', context)
    except:
        return HttpResponse("Primary server dead!", content_type="text/plain")


def make_transaction(request):
    global MASTER
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            product_type, number = form.cleaned_data['product_type'], form.cleaned_data['product_number']
            new_record = {}
            new_record["type"], new_record["number"], new_record["id"] = product_type, number, -1
            ip = SERVER_IP_LIST[MASTER]
            response = None
            try:
                payload = {'product_type':product_type, 'product_number':number, 'server_ip':ip}
                response = requests.post(ip+'/make_transaction', data=payload)
                print('Queried server is alive!')
            except:
                print('Queried server is dead!')
            
            if response != None: 
                json_res = response.json()
                new_record['id'] = json_res["transaction_id"]
                context = {}
                context["form"] = TransactionForm()
                context["shoes_number"] = json_res["shoes_number"]
                context["pants_number"] = json_res["pants_number"]
                if json_res['code'] == -1:
                    context["message"] = 'Database Error: Insertion Failed!'
                else:
                    context["message"] = 'Transaction %s: %s of %s Succeeded!' % \
                    (new_record['id'], number, product_type)
                return render(request, 'proxy_server/index.html', context)
            else:
                # switch to a new master to complete the pending transaction
                detect(request)
                switch_master(SERVER_IP_LIST[MASTER])
                for i,ip in enumerate(SERVER_IP_LIST):
                    if i != MASTER:
                        send_checkpoint(ip)
                return HttpResponse("Error Detected, Request Failed", content_type="text/plain")
    else:
        return HttpResponse("Make Transaction Cannot Accept GET Request", content_type="text/plain")

def detect(request):
    global MASTER
    prev_master = MASTER
    alive_count = 0
    alive_IP = []
    master = []
    for ip in SERVER_IP_LIST:
        try:
            requests.get(ip+'/detect')
            alive_count += 1
            master.append(1)
            alive_IP.append(ip)
        except:
            master.append(0)
            continue
    dead_count = len(SERVER_IP_LIST) - alive_count
    dead_IP = []
    for ip in SERVER_IP_LIST:
        if ip not in alive_IP:
            dead_IP.append(ip)
    if master[prev_master] == 0:
        new_master = prev_master
        while master[new_master] == 0:
            new_master = (new_master + 1) % len(master)
            MASTER = new_master
    return JsonResponse({'alive_count': str(alive_count), 'dead_count': str(dead_count), 
        'alive_IP': alive_IP, 'dead_IP': dead_IP, 'master': MASTER})

def send_checkpoint(ip):
    global REQ_RECORD
    try:
        payload = {'checkpoint':REQ_RECORD}
        response = requests.post(ip+'/update_checkpoint', json=payload)
        print("server: "+ip+" update finished!")
    except:
        print("server: "+ip+" update failed!")

def switch_master(ip):
    pass





