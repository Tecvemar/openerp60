# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description:
#
#
##############################################################################
#~ import time
#~ import pooler
from report import report_sxw
#~ from tools.translate import _


class parser_slabs_process_control_sheet(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        if context is None:
            context = {}
        super(parser_slabs_process_control_sheet, self).__init__(
            cr, uid, name, context=context)
        self.localcontext.update({
            'get_prefix': self._get_prefix,
            'get_slab_list': self._get_slab_list,
            'get_slab_list2': self._get_slab_list2,
            })
        self.context = context

    def _get_prefix(self, obj):
        lot_prefix = obj.product_id.lot_prefix
        lot_name = obj.prod_lot_id.name.split('-')
        if len(lot_name) == 1:
            lot_name = lot_name[0]
        else:
            lot_name = lot_name[1]
        lot_name = ('000000%s' % lot_name.strip())[-6:]
        prefix = '%s%s' % (lot_prefix, lot_name)
        return prefix

    def _get_slab_list(self, obj):
        res = map(
            lambda x: {'name': x, 'size': '', 'thickness': ''}, range(1, 61))
        for r in res:
            if int(r['name']) <= int(obj.slab_qty):
                r.update({'size': '%.3f x %.3f' % (
                    obj.net_length, obj.net_heigth),
                    'thickness': '%s' % obj.thickness})
        return res

    def _get_slab_list2(self, max):
        return map(lambda x: 1 + (x * 6), range(0, max))


report_sxw.report_sxw(
    'report.tcv_mrp.slabs_process_control_sheet',
    'tcv.mrp.gangsaw',
    'addons/tcv_mrp/report/slabs_process_control_sheet.rml',
    parser=parser_slabs_process_control_sheet,
    header=False
    )
