# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description: Report parser for: tcv_payroll_import
#
#
##############################################################################
#~ import time
#~ import pooler
from report import report_sxw
from tools.translate import _


class parser_tcv_payroll_import(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        context = context or {}
        super(parser_tcv_payroll_import, self).\
            __init__(cr, uid, name, context=context)
        self.localcontext.update({
            'get_sel_str': self._get_sel_str,
            'get_moves_summary': self._get_moves_summary,
            'get_summary': self._get_summary,
            })
        self.context = context

    def _get_sel_str(self, type, val):
        if not type or not val:
            return ''
        values = {'state': {'draft': _('Draft'),
                            'posted': _('Posted'),
                            'cancel': _('Cancelled')}}
        return values[type].get(val, '')

    def _get_moves_summary(self, obj):
        res = []
        move_ids = []
        for r in obj.receipt_ids:
            if r.move_id:
                move_ids.append(r.move_id.id)
        if move_ids:
            #~ move_ids = str(move_ids)[1:-1]. replace('L', '')
            self.cr.execute('''
                select ml.account_id, a.code, a.name as account_name,
                       '' as concept, sum(ml.debit) as debit,
                       sum(ml.credit) as credit, count(ml.id) as receipts
                from account_move_line ml
                left join account_account a on ml.account_id = a.id
                where ml.move_id in %(move_ids)s
                group by ml.account_id, a.code, a.name
                order by a.code desc''', {'move_ids': tuple(move_ids)})
            res = self.cr.fetchall()
            debit, credit = 0, 1
            total = [0, 0]
            for line in res:
                total[debit] += line[4]
                total[credit] += line[5]
            res.append(('', '', '', _('Totals'),
                        total[debit], total[credit], '',))
        return res

    def _get_summary(self, obj_lines, fields):
        '''
        obj_lines: an obj.line_ids (lines to be totalized)
        fields: tuple with totalized field names

        Use in rml:
        [[ repeatIn(get_summary(o.line_ids, ('fld_1', 'fld_2'..)), 't') ]]
        '''
        totals = {}
        for key in fields:
            totals[key] = 0
        for line in obj_lines:
            for key in fields:
                totals[key] += line[key]
        return [totals]


report_sxw.report_sxw(
    'report.tcv.payroll.import.report',
    'tcv.payroll.import',
    'addons/tcv_payroll_import/report/tcv_payroll_import.rml',
    parser=parser_tcv_payroll_import,
    header=False,
    )
