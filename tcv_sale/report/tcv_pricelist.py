# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description: Report parser for: tcv_rse
#
#
##############################################################################
#~ import time
#~ import pooler
from report import report_sxw
#~ from tools.translate import _


class parse_tcv_pricelist(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        context = context or {}
        super(parser_tcv_pricelist, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            })
        self.context = context

report_sxw.report_sxw('report.tcv.pricelist',
                      'tcv.pricelist',
                      'addons/tcv_sale/report/tcv_pricelist.rml',
                      parser=parse_tcv_pricelist, header=False)

report_sxw.report_sxw('report.tcv.pricelist.bss',
                      'tcv.pricelist',
                      'addons/tcv_sale/report/tcv_pricelist_bss.rml',
                      parser=parse_tcv_pricelist, header=False)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
