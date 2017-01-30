# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description: Report parser for: name_
#
#
##############################################################################
#~ import time
#~ import pooler
from report import report_sxw
#~ from tools.translate import _


class parser_list_wh_islr_report(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        context = context or {}
        super(parser_list_wh_islr_report, self).__init__(
            cr, uid, name, context=context)
        self.localcontext.update({
            'get_invoice_number': self._get_invoice_number,
            'get_concept_list': self._get_concept_list,
            })
        self.context = context

    def _get_invoice_number(self, number):
        return number if number and number != '0' else 'N/A'

    def _get_concept_list(self, obj):
        res = {}
        for line in obj.xml_ids:
            code = line.concept_code
            if not res.get(code):
                res.update({
                    code: {
                        'code': code,
                        'name': line.concept_id.name,
                        'base': 0,
                        'qty': 0,
                        'wh': 0,
                        }
                    })
            res[code]['base'] += line.base
            res[code]['qty'] += 1
            res[code]['wh'] += line.wh
        return sorted(res.values(), key=lambda k: k['code'])

report_sxw.report_sxw(
    'report.tcv_list_wh_islr_report',
    'islr.xml.wh.doc',
    'addons/tcv_fiscal_report/report/list_wh_islr_report.rml',
    parser=parser_list_wh_islr_report,
    header=False
    )
