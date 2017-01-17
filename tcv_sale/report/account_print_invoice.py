# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
from report import report_sxw
#~ import pooler
import numero_a_texto2 as nat


class account_invoice(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(account_invoice, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'get_address': self._get_address,
            'get_conditions': self._get_conditions,
            'get_conditions_proforma': self._get_conditions_proforma,
            'get_invoice_lines': self._get_invoice_lines,
            'get_pieces': self._get_pieces,
            'amount_text': self._amount_text,
            'get_currency_rate': self._get_currency_rate,
        })

    def _get_address(self, address):
        """This address must be a res.partner.address instance"""
        return self.pool.get('res.partner').\
            get_partner_address(self.cr, self.uid, address)

    def _get_conditions(self, obj):
        cfg = self.pool.get('tcv.sale.order.config').\
            get_config(self.cr, self.uid)
        return cfg.invoice_cond

    def _get_conditions_proforma(self, obj):
        cfg = self.pool.get('tcv.sale.order.config').\
            get_config(self.cr, self.uid)
        return cfg.proforma_cond

    def _get_tax(self, obj):
        tax = obj.invoice_line_tax_id[0].amount * 100
        return '%4.0f%s' % (tax, '%')

    def _get_invoice_lines(self, obj):
        res = {}
        for line in obj.invoice_line:
            pr_id = '%s%s' % (line.product_id.id, line.price_unit)
            if res.get(pr_id):
                res[pr_id].update(
                    {'quantity': res[pr_id]['quantity'] + line.quantity,
                     'pieces': res[pr_id]['pieces'] + line.pieces,
                     'items': res[pr_id]['items'] + 1,
                     'price_subtotal': res[pr_id]['price_subtotal'] +
                        line.price_subtotal,
                     })
            else:
                res.update({pr_id: {'name': line.name,
                                    'quantity': line.quantity,
                                    'product_uom': line.uos_id.name,
                                    'pieces': line.pieces,
                                    'items': 1,
                                    'tax': self._get_tax(line),
                                    'price_unit': line.price_unit,
                                    'price_subtotal': line.price_subtotal,
                                    'symbol': obj.currency_id.symbol}})
        return res.values()

    def _get_pieces(self, line):
        return '%s/%s' % (line['pieces'], line['items']) \
            if line['pieces'] else '---'

    def _amount_text(self, amount):
        if not amount:
            return ''
        return nat.Numero_a_Texto(amount)

    def _get_currency_rate(self, obj):
        #~ obj: self.pool.get('account.invoice').browse
        obj_inv = self.pool.get('account.invoice')
        # implemented in tcv_purchase
        rate = obj_inv.get_invoice_currency_rate(
            self.cr, self.uid, obj)
        return rate


report_sxw.report_sxw(
    'report.tcv.account.invoice',
    'account.invoice',
    'addons/tcv_sale/report/account_print_invoice.rml',
    parser=account_invoice
)

report_sxw.report_sxw(
    'report.tcv.account.proforma',
    'account.invoice',
    'addons/tcv_sale/report/account_print_proforma.rml',
    parser=account_invoice
)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
