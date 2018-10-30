from django.shortcuts import render
from forms import *
from rds_mysql_apis import * 

# Database APIs waiting to be implemented.
# Create your views here.
def home(request):
	transaction_form = TransactionForm()
	remain_shoes_number = 10
	remain_pants_number = 10
	context = {}
	context["form"] = transaction_form
	context["remain_shoes_number"] = remain_shoe_number
	context["remain_pants_number"] = remain_pants_number
	return render(request, 'online_shop/index.html', context)

def make_transaction(request):
	if request.method == 'POST':
		new_form = TransactionForm(request.POST)
		if form.is_valid():
			transaction_row = {}
			transaction_row['transaction_id'] = getMaxId() + 1
			transaction_row['product_type'] = form.cleaned_data['product_type']
			transaction_row['number'] = form.cleaned_data['product_number']
			response = insert_transaction(transaction_row)
			
			context = {}
			context["form"] = TransactionForm()
			context["remain_shoes_number"] = remain_shoe_number
			context["remain_pants_number"] = remain_pants_number
			
			if response == '0':
				context["message"] = 'Database Error: Insertion Failed!'
			else:
				context["message"] = 'Transaction: %d of %s Succeeded!' % 
				(form.cleaned_data['product_number'], form.cleaned_data['product_type'])
			return render(request, 'online_shop/index.html', context)


