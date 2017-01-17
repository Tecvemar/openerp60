# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description: Report parser for: tcv_sale_proforma
#
#
##############################################################################
#~ import time
#~ import pooler
from report import report_sxw
from tools.translate import _


class parser_tcv_sale_proforma(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        context = context or {}
        super(parser_tcv_sale_proforma, self).\
            __init__(cr, uid, name, context=context)
        self.localcontext.update({
            'get_sel_str': self._get_sel_str,
            'get_address': self._get_address,
            'get_conditions': self._get_conditions,
            })
        self.context = context

    def _get_sel_str(self, type, val):
        if not type or not val:
            return ''
        values = {'state': {'draft': _('Draft'),
                            'done': _('Done'),
                            'cancel': _('Cancelled')}}
        return values[type].get(val, '')

    def _get_address(self, address):
        """This address must be a res.partner.address instance"""
        return self.pool.get('res.partner').\
            get_partner_address(self.cr, self.uid, address)

    def _get_conditions(self, obj):
        return _('''Quantity may vary ± 15%.
                  The payment term depends on BANCOEX approval.
                  The reservation of the material for this proforma will be valid for a maximun of 15 days. After this period, without confirmation, the material will be released for sale.''')

report_sxw.report_sxw('report.tcv.sale.proforma.report',
                      'tcv.sale.proforma',
                      'addons/tcv_sale/report/tcv_sale_proforma.rml',
                      parser=parser_tcv_sale_proforma,
                      header=False
                      )
