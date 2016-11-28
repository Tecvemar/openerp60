# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description: Report parser for: tcv_municipal_tax_products
#
#
##############################################################################
#~ import time
#~ import pooler
from report import report_sxw
#~ from tools.translate import _


class parser_tcv_municipal_tax_products(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        context = context or {}
        super(parser_tcv_municipal_tax_products, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'get_taxes': self._get_taxes,
            })
        self.context = context

    def _get_taxes(self, o):
        obj_tax = self.pool.get('tcv.municipal.tax')
        data = obj_tax.get_municipal_taxes(
            self.cr, self.uid, o.id, context=None)
        return data

report_sxw.report_sxw(
    'report.tcv.municipal.tax.products.report',
    'tcv.municipal.tax',
    'addons/tcv_municipal_tax/report/tcv_municipal_tax_products.rml',
    parser=parser_tcv_municipal_tax_products,
    header=False
    )
