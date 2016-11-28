# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description: Report parser for: tcv_mrp_abrasive_durability
#
#
##############################################################################
#~ import time
#~ import pooler
from report import report_sxw
#~ from tools.translate import _


class parser_tcv_mrp_abrasive_durability(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        context = context or {}
        super(parser_tcv_mrp_abrasive_durability, self).__init__(
            cr, uid, name, context=context)
        self.localcontext.update({
            'get_total_cost': self._get_total_cost,
            })
        self.context = context

    def _get_total_cost(self, obj):
        total_cost_m2 = 0
        for line in obj.line_ids:
            total_cost_m2 += line.price_m2
        return total_cost_m2

report_sxw.report_sxw('report.tcv.mrp.abrasive.durability.report',
                      'tcv.mrp.abrasive.durability',
                      'addons/tcv_mrp/report/tcv_mrp_abrasive_durability.rml',
                      parser=parser_tcv_mrp_abrasive_durability,
                      header=False
                      )
