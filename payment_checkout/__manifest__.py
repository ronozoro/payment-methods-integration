# -*- coding: utf-8 -*-

{
    'name': 'Checkout Payment Acquirer',
    'author':'Mostafa Mohamed',
    'website':'https://www.linkedin.com/in/mostafa-mohamed-449a8786/',
    'category': 'Accounting',
    'summary': 'Payment Acquirer: Checkout.com',
    'version': '1.0',
    'description': 'Checkout Payment Acquirer',
    'depends': ['payment'],
    'data': [
        'views/payment_views.xml',
        'views/payment_checkout_templates.xml',
        'data/payment_acquirer_data.xml',
    ],
    'installable': True,
}
