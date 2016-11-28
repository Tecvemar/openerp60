# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description: Report parser for: tcv_stock_changes
#
#
##############################################################################
#~ import time
#~ import pooler
from report import report_sxw
from tools.translate import _


class parser_tcv_stock_changes(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        context = context or {}
        super(parser_tcv_stock_changes, self).\
            __init__(cr, uid, name, context=context)
        self.localcontext.update({
            'get_sel_str': self._get_sel_str,
            'get_lot_size': self._get_lot_size,
            'get_summary': self._get_summary,
            })
        self.context = context

    def _get_sel_str(self, type, val):
        if not type or not val:
            return ''
        values = {'state': {'draft': _('Draft'),
                            'posted': _('Posted'),
                            'confirm': _('Confirmed'),
                            'done': _('Done'),
                            'cancel': _('Cancelled'),
                            'auto': _('Waiting'),
                            'confirmed': _('Confirmed'),
                            'assigned': _('Available'),
                            }}
        return values[type].get(val, '')

    def _get_lot_size(self, stock_driver, l, h, w):
        if stock_driver in ('tile', 'slab'):
            name = '%sx%s' % (l, h)
        elif stock_driver == 'block':
            name = '%sx%sx%s' % (l, h, w)
        else:
            name = ''
        return name.replace('.', ',')

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

report_sxw.report_sxw('report.tcv.stock.changes.report',
                      'tcv.stock.changes',
                      'addons/tcv_stock/report/tcv_stock_changes.rml',
                      parser=parser_tcv_stock_changes,
                      header=False
                      )
