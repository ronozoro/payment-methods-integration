# -*- coding: utf-8 -*-
import json
import logging

from odoo.addons.website_sale.controllers.main import WebsiteSale

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class WebsiteSaleInherit(WebsiteSale):

    @http.route('/shop/payment/validate', type='http', auth="public", website=True)
    def payment_validate(self, transaction_id=None, sale_order_id=None, **post):
        res = super(WebsiteSaleInherit, self).payment_validate(transaction_id=transaction_id,
                                                               sale_order_id=sale_order_id, **post)
        if transaction_id is None and sale_order_id is None and post.get('my_checkout'):
            tx = request.website.sale_get_transaction()
            order = request.website.sale_get_order()
            if not tx:
                Transaction = request.env['payment.transaction'].sudo()
                tx = Transaction.search([('sale_order_id', '=', order.id)],order='id asc')[0]
                response = tx.sudo().create_checkout_charge(tokenid=post.get('token'), values=post)
                if response.text:
                    response = json.loads(response.text)
                    responseCode = response.get('responseCode', False)
                    if responseCode not in ('10000','10200') or not responseCode:
                        for record in Transaction.search([('sale_order_id', '=', order.id)],order='id asc'):
                            record.sudo().unlink()
                        return res
                    else:
                        tx_ids= Transaction.search([('sale_order_id', '=', order.id)],order='id asc')._ids
                        if tx_ids:
                            tx_ids=tx_ids[1:]
                            for tx_new in  Transaction.browse(tx_ids):
                                tx_new.sudo().unlink()
                        order.sudo().with_context(send_email=True).action_confirm()
                        tx.write({'state': 'done'})
                        request.website.sale_reset()
                        return request.redirect('/shop/confirmation')
                else:
                    return res
            return res
        else:
            return res


WebsiteSaleInherit()
