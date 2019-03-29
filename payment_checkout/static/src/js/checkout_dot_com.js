odoo.define('payment_checkout.checkout_dot_com', function (require) {
    "use strict";
    var ajax = require('web.ajax');
    var paymentForm = document.getElementById('checkout-payment-form');
    paymentForm.addEventListener('submit', function (event) {
        event.preventDefault();
        var $inputs = $('#checkout-payment-form :input');
        var values = {};
        $inputs.each(function () {
            values[this.name] = $(this).val();
        });
        var my_values = $("#checkout-payment-form").serialize();
        Frames.submitCard()
            .then(function (data1) {
                Frames.addCardToken(paymentForm, data1.cardToken);
                if (data1.cardToken) {
                    ajax.jsonRpc('/shop/payment/transaction/' + values.acquirer, 'call', values).then(function (test) {
                    });
                }
                paymentForm.submit();
                window.location.href = '/shop/payment/validate?' + my_values + '&token=' + data1.cardToken + '&my_checkout=' + '1'
            }).catch(function (err) {


        });
    });

});
