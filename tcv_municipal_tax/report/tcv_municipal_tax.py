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
        super(parser_tcv_municipal_tax, self).__init__(
            cr, uid, name, context=context)
        self.localcontext.update({
            'get_taxes': self._get_taxes,
            'get_dates': self._get_dates,
            'get_amount': self._get_amount,
            'get_tax': self._get_tax,
            })
        self.context = context

    def _get_taxes(self, o):
        obj_tax = self.pool.get('tcv.municipal.tax')
        data = obj_tax.get_municipal_taxes(
            self.cr, self.uid, o.id, context=self.context)
        return data

    def _get_dates(self, date_fld):
        return self.context.get(date_fld)

    def _get_amount(self, o):
        period = self.context.get('tax_period')
        if period:
            if period == 'year':
                res = getattr(o, 'amount')
            else:
                res = getattr(o, 'amount_' + period)
        else:
            res = 0
        return res

    def _get_tax(self, o):
        period = self.context.get('tax_period')
        if period:
            if period == 'year':
                res = getattr(o, 'total_tax')
            else:
                res = getattr(o, 'tax_' + period)
        else:
            res = 0
        return res


report_sxw.report_sxw(
    'report.tcv.municipal.tax.report',
    'tcv.municipal.tax',
    'addons/tcv_municipal_tax/report/tcv_municipal_tax.rml',
    parser=parser_tcv_municipal_tax,
    header=False
    )

report_sxw.report_sxw(
    'report.tcv.municipal.tax.invoice.report',
    'tcv.municipal.tax',
    'addons/tcv_municipal_tax/report/tcv_municipal_tax_invoice.rml',
    parser=parser_tcv_municipal_tax,
    header=False
    )

report_sxw.report_sxw(
    'report.tcv.municipal.tax.products.report',
    'tcv.municipal.tax',
    'addons/tcv_municipal_tax/report/tcv_municipal_tax_products.rml',
    parser=parser_tcv_municipal_tax,
    header=False
    )
