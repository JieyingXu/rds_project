from django.shortcuts import render
from proxy_server.forms import *
from django.http import HttpResponse, JsonResponse
import requests
import threading, time
import os, json

# Create your views here.
SERVER_IP_LIST = ["http://127.0.0.1:8008", "http://127.0.0.1:8080", "http://127.0.0.1:8800"]
LIVING = [1, 1, 1]
MASTER = 0
LOCK = threading.Lock()
MASTER_SWITCH = 0
# transaction record inside the list is dictionary with keys:
# 'type', 'number', 'id'
REQ_RECORD = []
CHECKPOINT_FILE = os.path.join('.', 'proxy_checkpoint.csv')


class CheckPointThread(threading.Thread):
    def run(self):
        while True:
            global SERVER_IP_LIST, LOCK
            global REQ_RECORD
            global MASTER
            global MASTER_SWITCH
            time.sleep(10)
            LOCK.acquire()
            if MASTER_SWITCH == 0:
                new_master = MASTER
                for i,ip in enumerate(SERVER_IP_LIST):
                    if i != new_master and LIVING[i] == 1:
                        send_checkpoint(ip)
                with open(CHECKPOINT_FILE, 'a') as f:
                    for transaction in REQ_RECORD:
                        row = "%s,%s,%s\n" % (transaction["id"], transaction["type"], transaction["number"])
                        f.write(row)
                REQ_RECORD = []
            LOCK.release()


thread1 = CheckPointThread()
thread1.start()


def home(request):
    # interval = request.GET.get('interval')
    global SERVER_IP_LIST
    global MASTER
    ip = SERVER_IP_LIST[MASTER]
    try:
        payload = {'server_ip':ip}
        response = requests.post(ip+'/home', data=payload)
        # response = requests.get(ip+'/home')
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
                # Append it to current checkpoint list
                REQ_RECORD.append(new_record)
                return render(request, 'proxy_server/index.html', context)
            # else:
            #     # switch to a new master to complete the pending transaction
            #     detect(request)
            #     switch_master(SERVER_IP_LIST[MASTER])
            #     for i,ip in enumerate(SERVER_IP_LIST):
            #         if i != MASTER:
            #             send_checkpoint(ip)
            #     return HttpResponse("Error Detected, Request Failed", content_type="text/plain")
    else:
        return HttpResponse("Make Transaction Cannot Accept GET Request", content_type="text/plain")


def detect(request):
    global MASTER, LOCK,LIVING
    LOCK.acquire()
    
    prev_master, prev_living = MASTER, LIVING
    alive_count, alive_IP, new_living = 0, [], []
    
    # Get new living IP status.
    for ip in SERVER_IP_LIST:
        try:
            requests.get(ip+'/detect')
            alive_count += 1
            new_living.append(1)
            alive_IP.append(ip)
        except:
            new_living.append(0)
            continue
    LIVING = new_living
    dead_count = len(SERVER_IP_LIST) - alive_count
    dead_IP = []
    for ip in SERVER_IP_LIST:
        if ip not in alive_IP:
            dead_IP.append(ip)

    # Elect new master if previous master is dead now.
    if new_living[prev_master] == 0:
        new_master = prev_master
        while new_living[new_master] == 0:
            new_master = (new_master + 1) % len(new_living)
            MASTER = new_master

    # Let coming back server catch up with checkpoint.
    for i in range(len(new_living)):
        pre, now = prev_living[i], new_living[i]
        if pre == 0 and now == 1:
            catchup(SERVER_IP_LIST[i])
            print("Reviving server: %s catched up!" % SERVER_IP_LIST[i])
    # print(MASTER)
    LOCK.release()
    return JsonResponse({'alive_count': str(alive_count), 'dead_count': str(dead_count), 
        'alive_IP': alive_IP, 'dead_IP': dead_IP, 'master': MASTER})


def send_checkpoint(ip, record=None):
    global REQ_RECORD
    if record == None:
        new_record = json.dumps(REQ_RECORD)
    else:
        new_record = json.dumps(record)
    try:
        payload = {'checkpoint':new_record, 'server_ip':ip}
        response = requests.post(ip+'/update', data=payload)
        if record == None:
            print("server: "+ip+" update succeded!")
    except:
        print("server: "+ip+" update failed!")


def catchup(ip):
    payload = {'server_ip':ip}
    response = requests.post(ip+'/get_current_record', data=payload)
    json_res = response.json()
    max_id = str(json_res['max_id'])
    req_record = []
    with open(CHECKPOINT_FILE, 'r') as f:
        transaction_id = "-1"
        while (transaction_id != max_id):
            line = f.readline().strip()
            transaction_id = str(line.split(',')[0])
        line = f.readline().strip()
        while (line):
            print(line)
            l = line.split(',')
            new_record = {}
            new_record['id'], new_record['type'], new_record['number'] = l[0],l[1],l[2]
            req_record.append(new_record)
            line = f.readline().strip()
    send_checkpoint(ip, req_record)






