# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description: Report parser for: tcv_bank_moves
#
#
##############################################################################
#~ import time
#~ import pooler
from report import report_sxw
from tools.translate import _


class parser_tcv_bank_moves(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        context = context or {}
        super(parser_tcv_bank_moves, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'get_sel_str': self._get_sel_str,
            'get_summary': self._get_summary,
            })
        self.context = context

    def _get_sel_str(self, type, val):
        if not type or not val:
            return ''
        values = {'state': {'draft': _('Draft'),
                            'done': _('Done'),
                            'posted': _('Posted'),
                            'cancel': _('Cancelled')},
                  'type': {'transfer': _('Transfer'),
                           'dbn': _('Db/N'),
                           'crn': _('Cr/N')}}
        return values[type].get(val, '')

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

report_sxw.report_sxw('report.tcv.bank.moves.report',
                      'tcv.bank.moves',
                      'addons/tcv_bank_deposit/report/tcv_bank_moves.rml',
                      parser=parser_tcv_bank_moves,
                      header=False
                      )
