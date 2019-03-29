# -*- coding: utf-8 -*-
import json
import urllib2
from urlparse import parse_qs

import odoo.addons.website_sale.controllers.main as main

from odoo import http
from odoo.http import request


class HyperPaySale(main.WebsiteSale):

    @http.route(['/shop/confirmation'], type='http', auth="public", website=True)
    def payment_confirmation(self, **post):
        acquirer_id = request.session.pop('website_payment_acquirer_id', False)
        acquirer = request.env['payment.acquirer'].sudo().browse(acquirer_id)
        if acquirer.name != 'HyperPay':
            sale_order_id = request.session.get('sale_last_order_id')
            if sale_order_id:
                order = request.env['sale.order'].sudo().browse(sale_order_id)
            else:
                return request.redirect('/shop')

            return request.render("website_sale.confirmation", {'order': order})
        else:
            order = request.website.sale_get_order()

            qs = parse_qs(request.httprequest.query_string)
            if not b'id' in qs:
                return request.render("website_sale.confirmation", {'order': order})

            id = qs[b'id'][0]

            if not order or not order.order_line or acquirer_id is None:
                return request.redirect("/shop")

            response = ''
            url = acquirer._get_hyperpay_urls()['hyperpay_form_url']
            url += "v1/checkouts/" + id.decode('utf-8') + "/payment"
            url += '?authentication.userId=' + acquirer.hyperpay_api_username
            url += '&authentication.password=' + acquirer.hyperpay_api_password
            url += '&authentication.entityId=' + acquirer.hyperpay_seller_account

            try:
                opener = urllib2.build_opener(urllib2.HTTPHandler)
                req = urllib2.Request(url, data='')
                req.get_method = lambda: 'GET'
                response = opener.open(req)
                response = json.loads(response.read())
            except urllib2.HTTPError, e:
                response = str(e.code)

            assert order.partner_id.id != request.website.partner_id.id

            info = {}
            state = 'draft'
            if 'result' in response:
                if 'description' in response['result']:
                    desc = response['result']['description']
                    if 'successfully processed' in desc:
                        info['options'] = 'Succesfully Processed'
                        state = 'done'
                    elif 'transaction declined' in desc:
                        info['options'] = 'Transaction Declined'
                        state = 'error'
                    elif 'request contains no' in desc:
                        info['options'] = 'Declined. Must Enter Cardholder Name'
                        state = 'error'
                    else:
                        info['options'] = desc
                        state = 'pending'

            if response == '400':
                info['options'] = 'Error Processing Transaction'
                state = 'pending'

                # find an already existing transaction
            transaction_obj = request.env['payment.transaction']
            tx = transaction_obj.sudo().search(['&', ('sale_order_id', '=', order.id), ('state', '=', 'done')])

            tx_id = transaction_obj.sudo().create({
                'acquirer_id': acquirer_id,
                'type': 'form',
                'amount': order.amount_total,
                'currency_id': order.pricelist_id.currency_id.id,
                'partner_id': order.partner_id.id,
                'partner_country_id': order.partner_id.country_id.id,
                'reference': request.env['payment.transaction'].get_next_reference(order.name),
                'sale_order_id': order.id,
                'hyperpay_txn_details': response,
                'state': state,
            })

            request.env['sale.order'].sudo().browse([order.id]).write({
                'payment_acquirer_id': acquirer_id,
                'payment_tx_id': tx_id.id
            })

            if tx and state == 'done':
                info['options'] = 'This should only happen in test environment'

            # confirm the quotation
            # clean context and session
            if state == 'done':
                request.env['sale.order'].sudo().browse([order.id]).with_context(send_email=True).action_confirm()
                request.website.sale_reset()

            if tx:
                state = 'done'
            return request.render("website_sale.confirmation", {'order': order, 'state': state})


HyperPaySale()
