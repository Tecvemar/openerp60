# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Gabriel Gamez.
#    Creation Date: 17/03/2015
#    Version: 0.0.0.1
#
#    Description: Report parser for: tcv_sale_commission
#
#
##############################################################################
#~ import time
#~ import pooler
from report import report_sxw
from tools.translate import _


class parser_tcv_sale_commission(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        context = context or {}
        super(parser_tcv_sale_commission, self).__init__(cr, uid, name,
                                                       context=context)
        self.localcontext.update({
            'get_sel_str': self._get_sel_str,
            })
        self.context = context

    def _get_sel_str(self, type, val):
        if not type or not val:
            return ''
        values = {'state': {'draft': _('Draft'),
                            'confirmed': _('Confirmed'),
                            'paid': _('Paid')}}
        return values[type].get(val, '')


report_sxw.report_sxw('report.tcv.sale.commission.report',
                      'tcv.sale.commission',
                      'addons/tcv_sale_commission/report/tcv_sale_commission.rml',
                      parser=parser_tcv_sale_commission,
                      header=False
                      )
