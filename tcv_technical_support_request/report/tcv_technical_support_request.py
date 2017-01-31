# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description: Report parser for: tcv_technical_support_request
#
#
##############################################################################
#~ import time
#~ import pooler
from report import report_sxw
#~ from tools.translate import _


class parser_tcv_technical_support_request(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        context = context or {}
        super(parser_tcv_technical_support_request, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            })
        self.context = context

report_sxw.report_sxw('report.tcv.technical.support.request.report',
                      'tcv.technical.support.request',
                      'addons/tcv_technical_support_request/report/tcv_technical_support_request.rml',
                      parser=parser_tcv_technical_support_request,
                      header=False
                      )
