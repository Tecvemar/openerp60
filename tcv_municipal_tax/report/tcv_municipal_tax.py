# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description: Report parser for: tcv_municipal_tax
#
#
##############################################################################
#~ import time
#~ import pooler
from report import report_sxw
#~ from tools.translate import _


class parser_tcv_municipal_tax(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        context = context or {}
        super(parser_tcv_municipal_tax, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            })
        self.context = context

report_sxw.report_sxw(
    'report.tcv.municipal.tax.report',
    'tcv.municipal.tax',
    'addons/tcv_municipal_tax/report/tcv_municipal_tax.rml',
    parser=parser_tcv_municipal_tax,
    header=False
    )
