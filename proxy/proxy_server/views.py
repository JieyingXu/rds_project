from django.shortcuts import render
from proxy_server.forms import *
from django.http import HttpResponse, JsonResponse
from proxy_server.rds_mysql_apis import *
import requests
import threading, time
import os, json

# Create your views here.
# SERVER_IP_LIST = ["http://127.0.0.1:8008", "http://127.0.0.1:8080", "http://127.0.0.1:8800"]
SERVER_IP_LIST = ["http://127.0.0.1:8008", "http://127.0.0.1:8080"]

# Mapping the status of server in the SERVER_IP_LIST, 1 is alive, 0 is dead.
LIVING = [1] * len(SERVER_IP_LIST)

# Current master replica's index in the SERVER_IP_LIST.
MASTER = 0

# Use this global lock to ensure atomic operations in checkpointing, make_transaction and detect
LOCK = threading.Lock()

# Log transaction records inside the list is dictionary with keys:
''' 'type', 'number', 'id' '''
REQ_RECORD = []

# Mapping the transaction record to completed or pending.
COMPLETED = []

# Record the corresponding client identifier (ip_browser) of pending request.
REQUESTS = []

# Key is client identifier, value is result dictionary of finished pending transaction.
UPDATES = {}

# File path of checkpoint file.
CHECKPOINT_FILE = os.path.join('.', 'proxy_checkpoint.csv')

# Checkpointing interval in seconds
CHECKPOINT_INTERVAL = 30

# Server IP mapping to database IP.
SQL_CONFIG = {"http://127.0.0.1:8008": "35.185.39.95", "http://127.0.0.1:8080": "35.224.182.68", "http://127.0.0.1:8800":"35.193.252.106"}

# A independent thread that is going to send the transaction records in REQ_RECORD to 
# all living slave replicas and then write them into local csv file.
class CheckPointThread(threading.Thread):
    def run(self):
        while True:
            global SERVER_IP_LIST, LOCK, REQ_RECORD, MASTER, REQUESTS, UPDATES, COMPLETED
            time.sleep(CHECKPOINT_INTERVAL)
            
            LOCK.acquire()

            # Flag to mark if there is pending transaction in log list.
            pending = False
            print("REQ_RECORD:",REQ_RECORD)
            print("COMPLETED:",COMPLETED)
            for i,transaction_record in enumerate(REQ_RECORD):
                if COMPLETED[i] == "pending":
                    pending = True
                    break
            
            # If there is pending transaction in log list, abort this checkpointing section, wait
            # after the heartbeat to finish the pending transaction first.
            if not pending:
                new_master = MASTER
                for i,ip in enumerate(SERVER_IP_LIST):
                    # Only send all completed transactions logs to living slave replicas.
                    if i != new_master and LIVING[i] == 1:
                        send_checkpoint(ip)

                # Write logs into checkpoint and discard the logs after writing.
                with open(CHECKPOINT_FILE, 'a') as f:
                    for transaction in REQ_RECORD:
                        row = "%s,%s,%s\n" % (transaction["id"], transaction["type"], transaction["number"])
                        f.write(row)
                REQ_RECORD = []
                COMPLETED = []
                REQUESTS = []
                UPDATES = {}

            LOCK.release()
            
# Start the thread.
thread1 = CheckPointThread()
thread1.start()


# The home page of online shop. Query the master replica's database to first get the numbers.
def home(request):
    # interval = request.GET.get('interval')
    global SERVER_IP_LIST, MASTER
    ip = SERVER_IP_LIST[MASTER]
    # print(request.META['REMOTE_ADDR'])
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


# When user submit the form, make_transaction will be called.
# It is atomic transaction guranteed by LOCK.
def make_transaction(request):
    global MASTER, LOCK, REQUESTS, REQ_RECORD, COMPLETED
    LOCK.acquire()
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            product_type, number = form.cleaned_data['product_type'], form.cleaned_data['product_number']
            new_record = {}

            # Transaction id is first assigned to -1.
            new_record["type"], new_record["number"], new_record["id"] = product_type, number, -1
            ip = SERVER_IP_LIST[MASTER]
            response = None
            try:
                payload = {'product_type':product_type, 'product_number':number, 'server_ip':ip}
                response = requests.post(ip+'/make_transaction', data=payload)
                print('Queried server is alive!')
            except:
                print('Queried server is dead!')
            
            # Transaction succeeded, give the transaction record correct id.
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
                COMPLETED.append("completed")
                REQUESTS.append(None)
                LOCK.release()
                return render(request, 'proxy_server/index.html', context)
            # Pending request will mark transaction id as -1 and record its client identifier,
            # wait for next heartbeat to assign new master to finish the pending transaction.
            else:
                # new_record['id'] = -1
                anticipated_id = get_maxid(SQL_CONFIG.get(ip)) + 1
                new_record['id'] = anticipated_id
                context = {}
                identifier = request.META["REMOTE_ADDR"]+"_"+request.META["HTTP_USER_AGENT"]
                # Use this flag to disable front end submit button to prevent further transaction request.
                context["flag"] = False
                context["form"] = TransactionForm()
                context["shoes_number"] = "..."
                context["pants_number"] = "..."
                context["message"] = "Transaction Pending..."
                REQ_RECORD.append(new_record)
                COMPLETED.append("pending")
                REQUESTS.append(identifier) # Record corresponding client identifier.
                LOCK.release()
                return render(request, 'proxy_server/index.html', context)
    else:
        LOCK.release()
        return HttpResponse("Make Transaction Cannot Accept GET Request", content_type="text/plain")


# Heartbeat function called by fronted AJAX with configurable interval.
def detect(request):
    global MASTER,LOCK,LIVING,REQ_RECORD,REQUESTS, COMPLETED
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
    # Check if there is any pending transaction, finish pending transaction and
    # change the transactin id to correct value.
    # Send current log list to new master to make sure it catches up with previous
    # master before starting to process new request.
    if new_living[prev_master] == 0:
        print('enter 207')
        new_master = prev_master
        while new_living[new_master] == 0:
            new_master = (new_master + 1) % len(new_living)
            MASTER = new_master
        print(MASTER)
        master_ip = SERVER_IP_LIST[MASTER]
        for i,transaction_record in enumerate(REQ_RECORD):
            if COMPLETED[i] == "pending":
                finish_pending(ip, i, transaction_record['id'], transaction_record['type'], transaction_record['number'])
        # Only when the master has changed, new master need to catch up with log list first.
        send_checkpoint(master_ip)

    # No matter if the master has changed, pending transaction needs to be processed first.
    # Possible situation: Master dies and comes back during a heaartbeat interval.
    else:    
        master_ip = SERVER_IP_LIST[MASTER]
        for i,transaction_record in enumerate(REQ_RECORD):
            if COMPLETED[i] == "pending":
                finish_pending(ip, i, transaction_record['id'], transaction_record['type'], transaction_record['number'])

    

    # Let previous dead now alive server catch up with local checkpoint file.
    for i in range(len(new_living)):
        pre, now = prev_living[i], new_living[i]
        if pre == 0 and now == 1:
            catchup(SERVER_IP_LIST[i])
            print("Reviving server: %s catched up!" % SERVER_IP_LIST[i])
    
    LOCK.release()
    return JsonResponse({'alive_count': str(alive_count), 'dead_count': str(dead_count), 
        'alive_IP': alive_IP, 'dead_IP': dead_IP, 'master': MASTER})


# Finish pending transaction in the log in heartbeat
# Modify log's transaction ID and put results into UPDATES (client identifier: result)
def finish_pending(ip, i, id, product_type, product_number):
    global SQL_CONFIG, REQ_RECORD, COMPLETED,UPDATES, REQUESTS
    # Modify REQ_RECORD transation ID and change REQUESTS corresponding slot to None.
    payload = {'product_type':product_type, 'product_number':product_number, 'server_ip':ip}
    try:
        max_id = get_maxid(SQL_CONFIG.get(ip))
        if id != max_id:
            response = requests.post(ip+'/make_transaction', data=payload)
            json_res = response.json()
            new_record = {'type':product_type, 'number':product_number, 'id':json_res["transaction_id"]}
            
            new_response = {}
            new_response["shoes_number"] = json_res["shoes_number"]
            new_response["pants_number"] = json_res["pants_number"]
            new_response["message"] = 'Transaction %s: %s of %s Succeeded!' % (new_record['id'], product_number, product_type)
        else:
            new_record = {'type':product_type, 'number':product_number, 'id':id}
            new_response = {}
            new_response["shoes_number"] = get_remains("shoes", SQL_CONFIG.get(server_ip))
            new_response["pants_number"] = get_remains("pants", SQL_CONFIG.get(server_ip))
            new_response["message"] = 'Transaction %s: %s of %s Succeeded!' % (new_record['id'], product_number, product_type)

        REQ_RECORD[i] = new_record
        COMPLETED[i] = "completed"
        identifier = REQUESTS[i]
        UPDATES[identifier] = new_response
        print("Finish pending transaction succeded!")
        # return render(request, 'proxy_server/index.html', context)
    except:
        print("Finish pending transaction failed!")


# Frontend AJAX call this function when the message is showing "Transaction Pending..."
# to update frontend relevant fields with updated value after finishing pending transaction.
def update_pending(request):
    global UPDATES,LOCK
    LOCK.acquire()
    identifier = request.META["REMOTE_ADDR"]+"_"+request.META["HTTP_USER_AGENT"]
    # If the updated transaction results is available.
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

# Send transaction records to designated ip and 
# let server update their database.
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
        print("server: "+ip+" update succeded!")
    except:
        print("server: "+ip+" update failed!")

# When a previous dead server revives, it needs to catch up with current checkpoint
# by updating records inside checkpoint csv files. Catchup is done in heartbeat.
def catchup(ip):
    global CHECKPOINT_FILE
    payload = {'server_ip':ip}
    response = requests.post(ip+'/get_current_record', data=payload)
    json_res = response.json()
    max_id = str(json_res['max_id'])
    if max_id == 1000:
        return 
    req_record = []
    with open(CHECKPOINT_FILE, 'r') as f:
        line = f.readline().strip()
        if (line == ""):
            return 
        transaction_id = str(line.split(',')[0])
        # Find the start line of record to begin catching up.
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






