# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description: Report parser for: tcv_partner_balance
#
#
##############################################################################
#~ import time
#~ import pooler
from report import report_sxw
from tools.translate import _


class parser_tcv_partner_balance(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        context = context or {}
        super(parser_tcv_partner_balance, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'get_sel_str': self._get_sel_str,
            'get_summary': self._get_summary,
            })
        self.context = context

    def _get_sel_str(self, type, val):
        if not type or not val:
            return ''
        values = {
            'invoice_type': {
                'in_invoice,in_refund': _('Supplier balance'),
                'out_invoice,out_refund': _('Customer balance'),
                },
            'invoice_state': {
                'open': _('Open'),
                'paid': _('Paid'),
                'open,paid': _('All'),
                },
            'doc_type': {
                'Inv': _('Inv'),
                'N/C': _('N/C'),
                },
            }
        return values[type].get(val, '')

    def _get_summary(self, obj_lines, *args):
        '''
        obj_lines: an obj.line_ids (lines to be totalized)
        args: List, see below

        Use in rml:
        [[ repeatIn(get_summary(o.line_ids, ['fields in csv string']), 't') ]]
        '''
        totals = {}
        field_list = args[0][0]
        fields = field_list.split(',')
        for key in fields:
            totals[key] = 0
        for line in obj_lines:
            for key in fields:
                totals[key] += line[key]
        return [totals]

report_sxw.report_sxw(
    'report.tcv.partner.balance.report',
    'tcv.partner.balance',
    'addons/tcv_account/report/tcv_partner_balance.rml',
    parser=parser_tcv_partner_balance,
    header=False
    )
