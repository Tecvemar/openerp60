# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description: Report parser for: tcv_mrp_gangsaw_control_form
#
#
##############################################################################
#~ import time
#~ import pooler
from report import report_sxw
#~ from tools.translate import _


##----------------------------------------- parser_tcv_mrp_gangsaw_control_form


class parser_tcv_mrp_gangsaw_control_form(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        context = context or {}
        super(parser_tcv_mrp_gangsaw_control_form, self).__init__(
            cr, uid, name, context=context)
        self._page_n = 0
        self.localcontext.update({
            'get_summary': self._get_summary,
            'get_hours': self._get_hours,
            'empty_lines': self._empty_lines,
            'get_blocks_lines': self._get_blocks_lines,

            })
        self.context = context

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

    def _get_hours(self, start=0, end=-1):
        res = [('07:00', '10:00', '13:00'),
               ('16:00', '19:00', '21:00'),
               ('00:00', '03:00', '05:00')]
        return [{'time0': x[0], 'time1': x[1], 'time2': x[2]}
                for x in list(res * 10)[start:end]]

    def _empty_lines(self, obj):
        '''
        Add n empty lines at bottom of form's block list

        '''
        total_lines = 3
        empty_lines = total_lines - len(obj.line_ids)
        res = [] if empty_lines <= 0 else [x for x in range(empty_lines)]
        return res

    def _get_blocks_lines(self, obj):
        res = []
        for l in obj.line_ids:
            data = {
                'product_name': l.product_id.name,
                'prod_lot_name': l.prod_lot_id.name,
                'block_ref': l.block_ref,
                'length': l.length,
                'heigth': l.heigth,
                'width': l.width,
                'thickness': l.thickness,
                'lot_factor': l.lot_factor,
                }
            res.append(data)
        res.extend(range(3 - len(res)))
        return res


report_sxw.report_sxw(
    'report.tcv.mrp.gangsaw.control.form.report',
    'tcv.mrp.gangsaw.order',
    'addons/tcv_mrp/report/tcv_mrp_gangsaw_control_form.rml',
    parser=parser_tcv_mrp_gangsaw_control_form,
    header=False
    )
