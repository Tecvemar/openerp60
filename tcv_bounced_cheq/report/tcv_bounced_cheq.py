# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description: Report parser for: tcv_bounced_cheq
#
#
##############################################################################
#~ import time
#~ import pooler
from report import report_sxw
from tools.translate import _


class parser_tcv_bounced_cheq(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        context = context or {}
        super(parser_tcv_bounced_cheq, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'get_sel_str': self._get_sel_str,
            })
        self.context = context

    def _get_sel_str(self, type, val):
        if not type or not val:
            return ''
        values = {'state': {'draft': _('Draft'),
                            'posted': _('Posted'),
                            'cancel': _('Cancelled'),
                            'open': _('Open'),
                            'paid': _('Paid'),
                            }}
        return values[type].get(val, '')


report_sxw.report_sxw('report.tcv.bounced.cheq.report',
                      'tcv.bounced.cheq',
                      'addons/tcv_bounced_cheq/report/tcv_bounced_cheq.rml',
                      parser=parser_tcv_bounced_cheq,
                      header=False
                      )
