# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description: Report parser for: tcv_mrp_gangsaw_order
#
#
##############################################################################
#~ import time
#~ import pooler
from report import report_sxw
from tools.translate import _


##------------------------------------------------ parser_tcv_mrp_gangsaw_order

class parser_tcv_mrp_gangsaw_order(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        context = context or {}
        super(parser_tcv_mrp_gangsaw_order, self).__init__(
            cr, uid, name, context=context)
        self.localcontext.update({
            'get_sel_str': self._get_sel_str,
            'get_summary': self._get_summary,
            'get_hardness_params': self._get_hardness_params,
            })
        self.context = context

    def _get_sel_str(self, type, val):
        if not type or not val:
            return ''
        values = {'state': {'draft': _('Draft'),
                            'to_produce': _('To produce'),
                            'in_progress': _('In progress'),
                            'done': _('Done'),
                            'cancel': _('Cancel'),
                            }
                  }
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

    def _get_hardness_params(self, obj):
        hardness = 0
        for l in obj.line_ids:
            if hardness < l.product_id.hardness:
                hardness = l.product_id.hardness
        res = {'cut_down_feed': 0, 'interval': 0}
        if hardness:
            for p in obj.params_id.params_ids:
                if p.hardness == hardness:
                    res['cut_down_feed'] = p.cut_down_feed
                    res['interval'] = p.interval
        return res


report_sxw.report_sxw(
    'report.tcv.mrp.gangsaw.order.report',
    'tcv.mrp.gangsaw.order',
    'addons/tcv_mrp/report/tcv_mrp_gangsaw_order.rml',
    parser=parser_tcv_mrp_gangsaw_order,
    header=False
    )
