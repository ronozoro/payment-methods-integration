import json
import urllib
import urllib2
import urlparse

from odoo import models, fields, api
from odoo.http import request


class AcquirerHyperpay(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('hyperpay', 'HyperPay')])
    hyperpay_seller_account = fields.Char(required_if_provider='hyperpay', string='User ID', groups='base.group_user')
    hyperpay_api_username = fields.Char(required_if_provider='hyperpay', string='Entity ID', groups='base.group_user')
    hyperpay_api_password = fields.Char(required_if_provider='hyperpay', string='Password', groups='base.group_user')
    hyperpay_payment_type = fields.Char(required_if_provider='hyperpay', string='Payment Type',
                                        groups='base.group_user')

    @api.multi
    def _get_hyperpay_urls(self):
        if self.environment == 'prod':
            return {
                'hyperpay_form_url': 'https://oppwa.com/',
            }
        else:
            return {
                'hyperpay_form_url': 'https://test.oppwa.com/',
            }

    def _get_providers(self, cr, uid, context=None):
        providers = super(AcquirerHyperpay, self)._get_providers(cr, uid, context=context)
        providers.append(['hyperpay', 'HyperPay'])
        return providers

    _defaults = {
        'fees_active': False,
        'fees_dom_fixed': 0.35,
        'fees_dom_var': 3.4,
        'fees_int_fixed': 0.35,
        'fees_int_var': 3.9
    }

    @api.multi
    def hyperpay_form_generate_values(self, values):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        acquirer = self
        responseData = ''
        request.session['website_payment_acquirer_id'] = acquirer.id
        givenName = ''
        email = ''
        phone = ''
        mobile = ''
        companyName = ''
        street = ''
        city = ''
        sale_order_id = request.session.get('sale_last_order_id')
        if sale_order_id:
            order = self.env['sale.order'].sudo().browse(sale_order_id)
            givenName = order.partner_id.name
            email = order.partner_id.email
            phone = order.partner_id.phone
            mobile = order.partner_id.mobile
            street = order.partner_id.street
            street2 = order.partner_id.street2
            city = order.partner_id.city
        if not order.partner_id.is_company:
            companyName = order.partner_id.parent_id.name

        data = {
            'authentication.entityId': acquirer.hyperpay_seller_account,
            'authentication.password': acquirer.hyperpay_api_password,
            'authentication.userId': acquirer.hyperpay_api_username,
            'paymentType': acquirer.hyperpay_payment_type,
            'merchantTransactionId': order.id,
            # 'customer.email':email,
            'billing.street1': street or street,
            'billing.city': city,
            'billing.state': order.partner_id.state_id.name,
            'billing.country': order.partner_id.country_id.code,
            'billing.postcode': order.partner_id.zip,
            # 'customer.givenName': givenName,
            'customer.surname': givenName,

        }
        print(data)
        url = acquirer._get_hyperpay_urls()['hyperpay_form_url'] + "v1/checkouts"
        if acquirer.environment == 'test':
            data['amount'] = int(values['amount'])
            data['testMode'] = 'EXTERNAL'
            data['currency'] = 'SAR'
        else:
            data['amount'] = values['amount']
            data['currency'] = values['currency'] and values['currency'].name or ''
        try:
            opener = urllib2.build_opener(urllib2.HTTPHandler)
            query = urllib2.Request(url, data=urllib.urlencode(data))
            query.get_method = lambda: 'POST'
            response = opener.open(query)
            responseData = json.loads(response.read())
        except urllib2.HTTPError, e:
            responseData = str(e.code)

        script_src = ''

        if 'id' in responseData:
            script_src = acquirer._get_hyperpay_urls()['hyperpay_form_url'] + 'v1/paymentWidgets.js?checkoutId=' + \
                         responseData['id']

        hyperpay_tx_values = dict(values)
        hyperpay_tx_values.update({
            'script_src': script_src,
            'my_url': urlparse.urljoin(base_url, '/shop/confirmation'),
            'givenName': givenName,
            'email': email,
            'phone': phone,
            'mobile': mobile,
            'companyName': companyName,
            'street': street,
            'city': city
        })
        return hyperpay_tx_values

    @api.multi
    def hyperpay_get_form_action_url(self):
        return self._get_hyperpay_urls()['hyperpay_form_url']


AcquirerHyperpay()


class TxHyperpay(models.Model):
    _inherit = 'payment.transaction'

    hyperpay_txn_type = fields.Char('Transaction type')
    hyperpay_txn_details = fields.Char('Transaction Details')

    @api.multi
    def paypal_compute_fees(self, amount, currency_id, country_id):
        if not self.fees_active:
            return 0.0
        country = self.env['res.country'].browse(country_id)
        if country and self.company_id.country_id.id == country.id:
            percentage = self.fees_dom_var
            fixed = self.fees_dom_fixed
        else:
            percentage = self.fees_int_var
            fixed = self.fees_int_fixed
        fees = (percentage / 100.0 * amount + fixed) / (1 - percentage / 100.0)
        return fees


TxHyperpay()
