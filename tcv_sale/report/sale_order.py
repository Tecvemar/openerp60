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
from tools.translate import _


class sale_order_parser(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        super(sale_order_parser, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'get_sel_str': self._get_sel_str,
            'get_address': self._get_address,
            'get_conditions': self._get_conditions,
            'get_user': self._get_user,
        })

    def _get_sel_str(self, type, val):
        if not type or not val:
            return ''
        values = {'picking_policy': {'direct': _('Partial Delivery'),
                                     'one': _('Complete Delivery')},
                  'order_policy': {'prepaid': _('Payment Before Delivery'),
                                   'manual': _('Shipping & Manual Invoice'),
                                   'postpaid': _('Invoice On Order After Delivery'),
                                   'picking': _('Invoice From The Picking')},
                  'state': {'draft': _('Quotation'),
                            'waiting_date': _('Waiting Schedule'),
                            'manual': _('Manual In Progress'),
                            'progress': _('In Progress'),
                            'shipping_except': _('Shipping Exception'),
                            'invoice_except': _('Invoice Exception'),
                            'done': _('Done'),
                            'cancel': _('Cancelled')}}
        return values[type].get(val, '')

    def _get_address(self, address):
        """This address must be a res.partner.address instance"""
        return self.pool.get('res.partner').\
            get_partner_address(self.cr, self.uid, address)

    def _get_conditions(self,obj):
        cfg = self.pool.get('tcv.sale.order.config').\
            get_config(self.cr, self.uid)
        if obj.state == 'draft':
            return cfg.quotation_cond
        else:
            return cfg.sale_order_cond

    def _get_user(self, obj):
        if obj:
            if obj.signature:
                return obj.signature
            elif obj.name:
                return obj.name
        return ''

report_sxw.report_sxw('report.tcv.sale.order',
                      'sale.order',
                      'addons/tcv_sale/report/sale_order.rml',
                      parser=sale_order_parser, header=False)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
