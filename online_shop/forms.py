from django import forms

PRODUCT_CHOICES= [
    ('shoes', 'Shoes'),
    ('pants', 'Pants')
    ]

class TransactionForm(forms.Form):
    product_type= forms.CharField(label='What do you want to buy?', 
    	widget=forms.Select(choices=PRODUCT_CHOICES))
    product_number= forms.IntegerField(label='How many do you want to buy', max_length=5)

