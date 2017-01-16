# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description: Report parser for: account_move
#
#
##############################################################################
#~ import time
#~ import pooler
from report import report_sxw
from tools.translate import _


class parser_account_move(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        context = context or {}
        super(parser_account_move, self).__init__(cr, uid, name,
                                                  context=context)
        self.localcontext.update({
            'get_sel_str': self._get_sel_str,
            'get_totals': self._get_totals,
            'get_ref_name': self._get_ref_name,
            'get_moves_summary': self._get_moves_summary,
            })
        self.context = context

    def _get_sel_str(self, type, val):
        if not type or not val:
            return ''
        values = {'state': {'draft': _('Draft'),
                            'posted': _('Posted'),
                            'cancel': _('Cancelled'),
                            }}
        return values[type].get(val, '')

    def _get_totals(self, obj, type):
        values = {'debit': 0,
                  'credit': 0,
                  'count': 0,
                  }
        for l in obj.line_id:
            values['debit'] += l.debit
            values['credit'] += l.credit
            values['count'] += 1
        values.update({'dif': values['debit'] - values['credit']})
        return values.get(type, 0)

    def _get_ref_name(self, str1, str2):
        return ' - '.join([str1, str2])

    def _get_moves_summary(self, obj):
        res = []
        move_ids = [x.id for x in obj.line_id]
        if move_ids:
            #~ move_ids = str(move_ids)[1:-1]. replace('L', '')
            self.cr.execute('''
                select ml.account_id, a.code, a.name as account_name,
                       sum(ml.debit) as debit,
                       sum(ml.credit) as credit, count(ml.id) as lines
                from account_move_line ml
                left join account_account a on ml.account_id = a.id
                where ml.id in %(move_ids)s
                group by ml.account_id, a.code, a.name
                order by a.code desc''', {'move_ids': tuple(move_ids)})
            res = self.cr.fetchall()
        return res


report_sxw.report_sxw('report.account.move.report',
                      'account.move',
                      'addons/tcv_account/report/account_move.rml',
                      parser=parser_account_move,
                      header=False
                      )


report_sxw.report_sxw('report.account.move.lite.report',
                      'account.move',
                      'addons/tcv_account/report/account_move_lite.rml',
                      parser=parser_account_move,
                      header=False
                      )
