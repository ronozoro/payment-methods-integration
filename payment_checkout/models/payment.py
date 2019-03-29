# coding: utf-8

import json
import logging

import requests

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

FULL_VALUE = ['BYR', 'BIF', 'DJF', 'GNF', 'ISK', 'KMF', 'XAF', 'CLF', 'XPF', 'JPY', 'PYG', 'RWF', 'KRW', 'VUV', 'VND',
              'XOF']

MULTI_BY_1000 = ['BHD', 'LYD', 'JOD', 'KWD', 'OMR', 'TND']


class AcquirerCheckout(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('checkout', 'Checkout.com')])
    checkout_secret_key = fields.Char(required_if_provider='checkout', string='Secret Key', groups='base.group_user')
    checkout_publishable_key = fields.Char(required_if_provider='checkout', string='Publishable Key',
                                           groups='base.group_user')

    @api.multi
    def checkout_form_generate_values(self, tx_values):
        self.ensure_one()
        payment_checkout_tx_values = dict(tx_values)
        temp_checkout_tx_values = {
            'company': self.company_id.name,
            'amount': tx_values.get('amount'),
            'currency': tx_values.get('currency') and tx_values.get('currency').name or '',
            'currency_id': tx_values.get('currency') and tx_values.get('currency').id or '',
            'address_line1': tx_values['partner_address'],
            'address_city': tx_values['partner_city'],
            'address_country': tx_values['partner_country'] and tx_values['partner_country'].name or '',
            'email': tx_values['partner_email'],
            'address_zip': tx_values['partner_zip'],
            'name': tx_values['partner_name'],
            'phone': tx_values['partner_phone'],
        }
        temp_checkout_tx_values['returndata'] = payment_checkout_tx_values.pop('return_url', '')
        payment_checkout_tx_values.update(temp_checkout_tx_values)
        return payment_checkout_tx_values

    @api.multi
    def _get_checkout_api_urls(self):
        if self.environment == 'test':
            return 'https://sandbox.checkout.com/api2/v2/charges/token'
        else:
            return 'https://api2.checkout.com/v2/charges/token'


AcquirerCheckout()


class PaymentTransactionCheckout(models.Model):
    _inherit = 'payment.transaction'

    @api.multi
    def create_checkout_charge(self, tokenid, values=None):
        amount = values.get('amount')
        if values.get('currency'):
            if values.get('currency') in FULL_VALUE:
                amount = amount
            elif values.get('currency') in MULTI_BY_1000:
                amount = str(float(amount) * 1000)
            else:
                amount = str(float(amount) * 100)
        data = {
            'autoCapTime': '24',
            "autoCapture": "Y",
            "chargeMode": 1,
            "email": values.get('email'),
            "value": amount,
            "currency": values.get('currency'),
            "cardToken": tokenid,
            'trackId': self.reference,
            "transactionIndicator": "1",
            "udf1": values.get('phone'),
        }
        params = str(json.dumps(data))
        headers = {
            'Authorization': self.acquirer_id.checkout_secret_key,
            'Content-Type': 'application/json;charset=UTF-8',
        }
        response = requests.post(self.acquirer_id._get_checkout_api_urls(), headers=headers, data=params)
        return response


PaymentTransactionCheckout()
