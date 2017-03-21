# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description: Report parser for: tcv_mrp_production_supplies
#
#
##############################################################################
#~ import time
#~ import pooler
from report import report_sxw
from tools.translate import _


##--------------------------------------------------------------- parser_tcv_mrp_production_supplies
class parser_tcv_mrp_production_supplies(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        context = context or {}
        super(parser_tcv_mrp_production_supplies, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'get_sel_str': self._get_sel_str,
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


    def _get_summary(self, obj_lines, *args):
        '''
        obj_lines: an obj.line_ids (lines to be totalized)
        args: [string] with csv field names to be totalized

        Use in rml:
        [[ repeatIn(get_summary(o.line_ids, ('fld_1,fld_2,...')), 't') ]]
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
    'report.tcv.mrp.production.supplies.report',
    'tcv.mrp.production.supplies',
    'addons/tcv_mrp_production_supplies/report/tcv_mrp_production_supplies.rml',
    parser=parser_tcv_mrp_production_supplies,
    header=False
    )
