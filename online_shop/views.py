from django.shortcuts import render
from online_shop.forms import *
from online_shop.rds_mysql_apis import * 

# Database APIs waiting to be implemented.
# Create your views here.
def home(request):
	transaction_form = TransactionForm()
	remain_shoes_number = get_remains("shoes")
	remain_pants_number = get_remains("pants")
	context = {}
	context["form"] = transaction_form
	context["remain_shoes_number"] = remain_shoes_number
	context["remain_pants_number"] = remain_pants_number
	return render(request, 'online_shop/index.html', context)

def make_transaction(request):
	if request.method == 'POST':
		form = TransactionForm(request.POST)
		if form.is_valid():
			transaction_row = {}
			transaction_row['transaction_id'] = get_maxid() + 1
			
			product_type, number = form.cleaned_data['product_type'], form.cleaned_data['product_number']
			transaction_row['product_type'] = product_type
			transaction_row['number'] = int(number)
			response = insert_transaction(transaction_row)
			
			remain_shoes_number = get_remains("shoes")
			remain_pants_number = get_remains("pants")
			context = {}
			context["form"] = TransactionForm()
			context["remain_shoes_number"] = remain_shoes_number
			context["remain_pants_number"] = remain_pants_number
			
			if response['number'] == -1:
				context["message"] = 'Database Error: Insertion Failed!'
			else:
				context["message"] = 'Transaction: %s of %s Succeeded!' % \
				(number, product_type)
			return render(request, 'online_shop/index.html', context)


