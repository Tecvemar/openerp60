# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description: Report parser for: tcv_liquidity_report_wizard
#
#
##############################################################################
#~ import time
#~ import pooler
from report import report_sxw
#~ from tools.translate import _


class parser_tcv_liquidity_report_wizard(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        context = context or {}
        super(parser_tcv_liquidity_report_wizard, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            })
        self.context = context

report_sxw.report_sxw('report.tcv.liquidity.report.wizard.report',
                      'tcv.liquidity.report.wizard',
                      'addons/tcv_account/report/tcv_liquidity_report_wizard.rml',
                      parser=parser_tcv_liquidity_report_wizard,
                      header=False
                      )
