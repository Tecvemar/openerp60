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
from tools.translate import _


class parser_tcv_block_cost(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        if context is None:
            context = {}
        super(parser_tcv_block_cost, self).__init__(cr, uid, name,
                                                    context=context)
        self.localcontext.update({
            'get_rif': self._get_rif,
            'get_type': self._get_type,
            })
        self.context = context

    def _get_rif(self, vat=''):
        if not vat:
            return []
        return vat[2:].replace(' ', '')

    def _get_type(self, type=''):
        if not type:
            return []
        obj_bc = self.pool.get('tcv.block.cost')
        return _(obj_bc._method_types.get(type, ''))

report_sxw.report_sxw(
    'report.tcv_block_cost.tcv_block_cost_report',
    'tcv.block.cost',
    'addons/tcv_block_cost/report/tcv_block_cost.rml',
    parser=parser_tcv_block_cost,
    header=False
    )
