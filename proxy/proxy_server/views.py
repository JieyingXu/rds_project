from django.shortcuts import render
from proxy_server.forms import *
from django.http import HttpResponse, JsonResponse
import requests
import threading, time
import os, json

# Create your views here.
# SERVER_IP_LIST = ["http://127.0.0.1:8008", "http://127.0.0.1:8080", "http://127.0.0.1:8800"]
SERVER_IP_LIST = ["http://127.0.0.1:8008", "http://127.0.0.1:8080"]

LIVING = [1, 1, 1]
MASTER = 0
LOCK = threading.Lock()
# MASTER_SWITCH = 0

# transaction record inside the list is dictionary with keys:
# 'type', 'number', 'id'
REQ_RECORD = []
REQUESTS = []
UPDATES = {}
CHECKPOINT_FILE = os.path.join('.', 'proxy_checkpoint.csv')


class CheckPointThread(threading.Thread):
    def run(self):
        while True:
            global SERVER_IP_LIST, LOCK, REQ_RECORD, MASTER, REQUESTS, UPDATES
            time.sleep(10)
            
            LOCK.acquire()
            pending = False
            for i,transaction_record in enumerate(REQ_RECORD):
                if transaction_record['id'] == -1:
                    pending = True
                    break
            
            if not pending:
                new_master = MASTER
                for i,ip in enumerate(SERVER_IP_LIST):
                    if i != new_master and LIVING[i] == 1:
                        send_checkpoint(ip)
                with open(CHECKPOINT_FILE, 'a') as f:
                    for transaction in REQ_RECORD:
                        row = "%s,%s,%s\n" % (transaction["id"], transaction["type"], transaction["number"])
                        f.write(row)
                REQ_RECORD = []
                REQUESTS = []
                UPDATES = {}

            LOCK.release()
            

thread1 = CheckPointThread()
thread1.start()


def home(request):
    # interval = request.GET.get('interval')
    global SERVER_IP_LIST, MASTER
    ip = SERVER_IP_LIST[MASTER]
    print(request.META['REMOTE_ADDR'])
    try:
        payload = {'server_ip':ip}
        response = requests.post(ip+'/home', data=payload)
        # response = requests.get(ip+'/home')
        json_res = response.json()
        context = {}
        context["flag"] = True
        context["form"] = TransactionForm()
        context["shoes_number"] = json_res["shoes_number"]
        context["pants_number"] = json_res["pants_number"]
        return render(request, 'proxy_server/index.html', context)
    except:
        return HttpResponse("Primary server dead!", content_type="text/plain")


def make_transaction(request):
    global MASTER, LOCK, REQUESTS, REQ_RECORD
    LOCK.acquire()
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
                context["flag"] = True
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
                REQUESTS.append(None)
                LOCK.release()
                return render(request, 'proxy_server/index.html', context)
            else:
                # switch to a new master to complete the pending transaction
                new_record['id'] = -1
                context = {}
                # context["identifier"] = request.META["REMOTE_ADDR"]+"_"+request.META["HTTP_USER_AGENT"]
                identifier = request.META["REMOTE_ADDR"]+"_"+request.META["HTTP_USER_AGENT"]
                context["flag"] = False
                context["form"] = TransactionForm() # Have another form that disable submit button.
                context["shoes_number"] = "..."
                context["pants_number"] = "..."
                context["message"] = "Transaction Pending..." # disable frontend input and mark this as red
                REQ_RECORD.append(new_record)
                REQUESTS.append(identifier)
                LOCK.release()
                return render(request, 'proxy_server/index.html', context)
    else:
        LOCK.release()
        return HttpResponse("Make Transaction Cannot Accept GET Request", content_type="text/plain")


def detect(request):
    global MASTER,LOCK,LIVING,REQ_RECORD,REQUESTS
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
    # Check if there is any pending transaction.
    if new_living[prev_master] == 0:
        new_master = prev_master
        while new_living[new_master] == 0:
            new_master = (new_master + 1) % len(new_living)
            MASTER = new_master
        for i,transaction_record in enumerate(REQ_RECORD):
            if transaction_record['id'] == -1:
                ip = SERVER_IP_LIST[MASTER]
                finish_pending(ip, i, transaction_record['type'], transaction_record['number'])

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


def finish_pending(ip, i, product_type, product_number):
    # Modify REQ_RECORD transation ID and change REQUESTS corresponding slot to None.
    payload = {'product_type':product_type, 'product_number':product_number, 'server_ip':ip}
    try:
        response = requests.post(ip+'/make_transaction', data=payload)
        json_res = response.json()
        new_record = {'type':product_type, 'number':product_number, 'id':json_res["transaction_id"]}
        # new_record['id'] = json_res["transaction_id"]
        # context = {}
        # context["flag"] = True
        # context["form"] = TransactionForm()
        new_response = {}
        new_response["shoes_number"] = json_res["shoes_number"]
        new_response["pants_number"] = json_res["pants_number"]
        new_response["message"] = 'Transaction %s: %s of %s Succeeded!' % (new_record['id'], product_number, product_type)

        REQ_RECORD[i] = new_record
        identifier = REQUESTS[i]
        UPDATES[identifier] = new_response
        print("Finish pending transaction succeded!")
        # return render(request, 'proxy_server/index.html', context)
    except:
        print("Finish pending transaction failed!")
        # return 


def update_pending(request):
    global UPDATES,LOCK
    LOCK.acquire()
    identifier = request.META["REMOTE_ADDR"]+"_"+request.META["HTTP_USER_AGENT"]
    if identifier in UPDATES:
        response = UPDATES[identifier]
        response["code"] = "yes"
        LOCK.release()
        return JsonResponse(response)
    else:
        response = {}
        response["code"] = "no"
        LOCK.release()
        return JsonResponse(response)


def send_checkpoint(ip, record=None):
    global REQ_RECORD
    if record == None:
        new_record = json.dumps(REQ_RECORD)
        print("Normal: ", new_record)
    else:
        new_record = json.dumps(record)
        print("CatchUp: ", new_record)
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






