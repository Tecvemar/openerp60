# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description: Report parser for: tcv_voucher_advance
#
#
##############################################################################
#~ import time
#~ import pooler
from report import report_sxw
from tools.translate import _


class parser_tcv_voucher_advance(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        if context is None:
            context = {}
        super(parser_tcv_voucher_advance, self).\
            __init__(cr, uid, name, context=context)
        self.localcontext.update({
            'get_sel_str': self._get_sel_str,
            })
        self.context = context

    def _get_sel_str(self, type, val):
        if not type or not val:
            return ''
        values = {'state': {'draft': _('Draft'),
                            'posted': _('Posted'),
                            'done': _('Done'),
                            'cancel': _('Cancelled'),
                            },
                  'type': {'advance': _('Apply customer advance'),
                           'prepaid': _('Apply supplier advance'),
                           }
                           }
        return values[type].get(val, '')

report_sxw.report_sxw('report.tcv.voucher.advance.report',
                      'tcv.voucher.advance',
                      'addons/tcv_advance/report/tcv_voucher_advance.rml',
                      parser=parser_tcv_voucher_advance,
                      header=False
                      )
