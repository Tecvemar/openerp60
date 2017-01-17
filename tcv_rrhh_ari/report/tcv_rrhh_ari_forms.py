# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description: Report parser for: tcv_rrhh_ari_forms
#
#
##############################################################################
#~ import time
#~ import pooler
from report import report_sxw
#~ from tools.translate import _


class parser_tcv_rrhh_ari_forms(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        context = context or {}
        super(parser_tcv_rrhh_ari_forms, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            })
        self.context = context

report_sxw.report_sxw('report.tcv.rrhh.ari.forms.report',
                      'tcv.rrhh.ari.forms',
                      'addons/tcv_rrhh_ari/report/tcv_rrhh_ari_forms.rml',
                      parser=parser_tcv_rrhh_ari_forms,
                      header=False
                      )
