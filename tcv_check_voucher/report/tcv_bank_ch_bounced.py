# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description: Report parser for: tcv_bank_ch_bounced
#
#
##############################################################################
#~ import time
#~ import pooler
from report import report_sxw
from tools.translate import _


class parser_tcv_bank_ch_bounced(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        context = context or {}
        super(parser_tcv_bank_ch_bounced, self).__init__(
            cr, uid, name, context=context)
        self.localcontext.update({
            })
        self.localcontext.update({
            'get_sel_str': self._get_sel_str,
            })
        self.context = context

    def _get_sel_str(self, type, val):
        if not type or not val:
            return ''
        values = {'state': {'draft': _('Draft'),
                            'posted': _('Posted'),
                            }}
        return values[type].get(val, '')

report_sxw.report_sxw(
    'report.tcv.bank.ch.bounced.report',
    'tcv.bank.ch.bounced',
    'addons/tcv_check_voucher/report/tcv_bank_ch_bounced.rml',
    parser=parser_tcv_bank_ch_bounced,
    header=False
    )
