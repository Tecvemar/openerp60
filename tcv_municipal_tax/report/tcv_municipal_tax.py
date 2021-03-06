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
from tools.translate import _


class parser_tcv_municipal_tax(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        context = context or {}
        super(parser_tcv_municipal_tax, self).__init__(
            cr, uid, name, context=context)
        self.localcontext.update({
            'get_summary': self._get_summary,
            'get_taxes': self._get_taxes,
            'get_dates': self._get_dates,
            'get_amount': self._get_amount,
            'get_tax': self._get_tax,
            'get_totals': self._get_totals,
            'get_min_tax': self._get_min_tax,
            })
        self.context = context

    def _get_summary(self, obj_lines, *args):
        '''
        obj_lines: an obj.line_ids (lines to be totalized)
        args: [string] with csv field names to be totalized

        Use in rml:
        [[ repeatIn(get_summary(o.line_ids, ('fld_1', 'fld_2'..)), 't') ]]
        '''
        totals = {}
        field_list = args[0][0]
        fields = field_list.split(',')
        for key in fields:
            totals[key] = 0
        for line in obj_lines:
            for key in fields:
                totals[key] += line[key]
        return [totals]

    def _get_taxes(self, o):
        obj_tax = self.pool.get('tcv.municipal.tax')
        data = obj_tax.get_municipal_taxes(
            self.cr, self.uid, o.id, context=self.context)
        return data

    def _get_dates(self, date_fld):
        return _(self.context.get(date_fld))

    def _get_amount(self, o):
        period = self.context.get('tax_period')
        if period:
            if period == 'year':
                fld = 'amount'
                fld2 = 'total_sales'
            else:
                fld = 'amount_' + period
                fld2 = 'total_' + period
            if type(o) != dict:
                res = getattr(o, fld)
            else:
                res = o.get(fld, o.get(fld2, 0.0))
        else:
            res = 0
        return res

    def _get_tax(self, o):
        period = self.context.get('tax_period')
        if period:
            if period == 'year':
                fld = 'total_tax'
            else:
                fld = 'tax_' + period
            if type(o) != dict:
                res = getattr(o, fld)
            else:
                res = o.get(fld, 0.0)
        else:
            res = 0
        return res

    def _get_totals(self, obj):
        data = self._get_taxes(obj)
        amount = 0.0
        tax = 0.0
        for item in data:
            amount += self._get_amount(item)
            tax += (self._get_amount(item) * item.get('tax_amount')) / 100
        return [{'amount': amount, 'tax': tax}]

    def _get_min_tax(self, o):
        obj_cfg = self.pool.get('tcv.municipal.taxes.config')
        obj_ut = self.pool.get('l10n.ut')
        ut = obj_ut.get_amount_ut(self.cr, self.uid, o.date_stop) or 1
        cfg_ids = obj_cfg.search(
            self.cr, self.uid, [('activity', '=', True)], order='code')
        res = []
        for item in obj_cfg.browse(self.cr, self.uid, cfg_ids, context={}):
            res.append({
                'code': item.code,
                'name': item.name,
                'tax_amount': item.tax_amount,
                'min_tax': item.min_tax,
                'amount': item.min_tax * ut,
                })
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
