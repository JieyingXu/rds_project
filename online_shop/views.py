from django.shortcuts import render
from online_shop import *

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
			transaction_row['id'] = getMaxId() + 1
			transaction_row['product_type'] = form.cleaned_data['product_type']
			transaction_row['product_number'] = form.cleaned_data['product_number']
			add_record()