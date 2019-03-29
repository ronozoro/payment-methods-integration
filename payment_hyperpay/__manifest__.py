# -*- coding: utf-8 -*-
{
    'name': 'HyperPay Payment Acquirer',
    'category': 'Hidden',
    'summary': 'Payment Acquirer: HyperPay Implementation',
    'version': '1.4',
    'description': """HyperPay Payment Acquirer""",
    'depends': ['payment'],
    'application': True,
    'data': [
        'views/templates.xml',
        'views/payment_acquirer.xml',
        'data/hyperpay.xml',
    ],
    'installable': True,
}
