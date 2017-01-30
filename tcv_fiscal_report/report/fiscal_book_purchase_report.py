# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description: Report parser for: fiscal_book_sale_report
#
#
##############################################################################
#~ import time
#~ import pooler
from report import report_sxw
#~ from tools.translate import _
import textwrap
#~ import copy


class parser_fiscal_book_purchase_report(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        context = context or {}
        super(parser_fiscal_book_purchase_report, self).\
            __init__(cr, uid, name, context=context)
        self.localcontext.update({
            'split_str': self._split_str,
            'get_lines': self._get_lines,
            'get_groups': self._get_groups,
            'get_totals': self._get_totals,
            })
        self.context = context

    def _split_str(self, value, length):
        return value if len(value) <= length else \
            ' '.join(textwrap.wrap(value, length))

    def _add_book_report_line(self, item, data, res):
        typ = item.type
        tax_lines = int(item.vat_general_base and 1 or 0) + \
            int(item.vat_reduced_base and 1 or 0) + \
            int(item.vat_additional_base and 1 or 0)
        if item.doc_type == 'F/IMP' and item.invoice_id.dua_form_id:
            # import form show customs forms lines
            data.update({
                #~ 'doc_type': 'FACT',
                #~ 'void_form': '01-REG' ,
                'vat_exempt_tot': 0,
                'base_' + typ: 0,
                'tax_' + typ: 0,
                'rate_' + typ: 0,
                })
            partner_name = data['partner_name']
            if item.invoice_id.currency_id.id != \
                    item.invoice_id.company_id.currency_id.id:
                data.update({
                    'partner_name': '%s (%s)' % (
                        partner_name,
                        item.invoice_id.currency_id.symbol)})
            #~ res.append(data.copy())
            for f86 in item.invoice_id.dua_form_id.customs_form_ids:
                #~ data.update({
                    #~ 'rank': '"',
                    #~ 'doc_type': 'F/IMP',
                    #~ 'void_form': '02',
                    #~ 'total_with_iva': None,
                    #~ 'custom_statement': f86.name,
                    #~ 'vat_exempt_tot': 0,
                    #~ 'base_' + typ: 0,
                    #~ 'tax_' + typ: 0,
                    #~ 'rate_' + typ: 0,
                    #~ })
                for tax in f86.cfl_ids:
                    if tax.tax_code.vat_detail:
                        for l in tax.imex_tax_line:
                            data['base_' + typ] += l.base_amount
                            data['tax_' + typ] += l.tax_amount
                            data['rate_' + typ] += l.tax_id.amount * 100
                    #~ else:
                        #~ if tax.amount:
                            #~ data['vat_exempt_tot'] += tax.amount
                            #~ partner_tax = tax.tax_code.partner_id.name
                #~ data['partner_name'] = '%s (%s)' % (partner_name, partner_tax)
                #~ res.append(data.copy())
            res.append(data.copy())
        elif tax_lines == 1:
            # Only one tax is used show 1 line
            data.update({
                'base_' + typ: round(
                    item.vat_general_base + item.vat_reduced_base +
                    item.vat_additional_base, 2),
                'tax_' + typ: round(
                    item.vat_general_tax + item.vat_reduced_tax +
                    item.vat_additional_tax, 2),
                'rate_' + typ: round(
                    item.vat_general_rate + item.vat_reduced_rate +
                    item.vat_additional_rate, 2),
                })
            res.append(data)
        elif tax_lines > 1:
            # more than 1 tax show multipli lines
            data.update({
                'base_' + typ: round(item.vat_general_base, 2),
                'tax_' + typ: round(item.vat_general_tax, 2),
                'rate_' + typ: round(item.vat_general_rate, 2),
                })
            res.append(data)
            data_red = data.copy()
            data_red.update({
                'rank': '"',
                'void_form': '02-COM',
                'total_with_iva': None,
                'vat_exempt_tot': None,
                'wh_number': '',
                'wh_rate': None,
                'iwdl_id': False,
                })
            if item.vat_reduced_base:
                data_red.update({
                    'base_' + typ: round(item.vat_reduced_base, 2),
                    'tax_' + typ: round(item.vat_reduced_tax, 2),
                    'rate_' + typ: round(item.vat_reduced_rate, 2),
                    })
                res.append(data_red)
        elif item.check_total:
            data['vat_exempt_tot'] = item.check_total
            res.append(data)
        else:
            res.append(data)

    def _get_lines(self, obj, adjust=False, only_total=False):
        '''
        adjust = True Return adjust lines (item.emission_date < min_date)
        adjust = False Return period lines (item.emission_date >= min_date)
        '''
        res = []
        min_date = obj.period_id.date_start
        for item in obj.fbl_ids:
            if (adjust and item.emission_date < min_date) or (
                    not adjust and item.emission_date >= min_date):

                iwdl_id = bool(item.iwdl_id and item.wh_rate)
                data = {
                    'rank': item.rank,
                    'doc_type': item.doc_type,
                    'void_form': item.void_form,
                    'emission_date': item.emission_date,
                    'ctrl_number': item.ctrl_number,
                    'invoice_number': item.invoice_number,
                    'affected_invoice': item.affected_invoice,
                    'partner_vat': item.partner_vat,
                    'partner_name': item.partner_name,
                    'total_with_iva': item.total_with_iva,
                    'vat_exempt_tot': item.vat_sdcf + item.vat_exempt,
                    'imex_date': item.imex_date,
                    'custom_statement': item.custom_statement,
                    #~ 'vat_general_base_' + typ: item.vat_general_base,
                    #~ 'vat_reduced_base_' + typ: item.vat_reduced_base,
                    #~ 'vat_additional_base_' + typ: item.vat_additional_base,
                    #~ 'vat_general_tax_' + typ: item.vat_general_tax,
                    #~ 'vat_reduced_tax_' + typ: item.vat_reduced_tax,
                    #~ 'vat_additional_tax_' + typ: item.vat_additional_tax,
                    #~ 'vat_general_rate_' + typ: item.vat_general_rate,
                    #~ 'vat_reduced_rate_' + typ: item.vat_reduced_rate,
                    #~ 'vat_additional_rate_' + typ: item.vat_additional_rate,
                    'iwdl_id': item.iwdl_id,
                    'wh_number': (item.wh_number or '').replace('-', ''),
                    'wh_rate': item.wh_rate if iwdl_id else '',
                    'accounting_date': item.accounting_date if iwdl_id else '',
                    'get_wh_vat': item.get_wh_vat if iwdl_id else '',
                    }
                self._add_book_report_line(item, data, res)
        totals = {'total_with_iva': 0,
                  'vat_exempt_tot': 0,
                  'base_im': 0,
                  'tax_im': 0,
                  'base_do': 0,
                  'tax_do': 0,
                  'get_wh_vat': 0,
                  }
        for line in res:
            for key in totals:
                totals[key] += line.get(key, 0) or 0
        return [totals] if only_total else res or [{}]

    def _get_groups(self):
        return [
            {'name': 'Ajustes a los créditos fiscales de períodos anteriores',
             'is_adjust': True,
             'tot_name': 'Sub Total ajustes'},
            {'name': 'Créditos fiscales del período',
             'is_adjust': False,
             'tot_name': 'Sub Total Créditos fiscales'},
            ]

    def _get_totals(self, obj):
        obj_fb = self.pool.get('fiscal.book')
        return obj_fb._compute_purchase_book_totals(self.cr, self.uid, obj)

report_sxw.report_sxw(
    'report.tcv.fiscal.book.purchase',
    'fiscal.book',
    'addons/tcv_fiscal_report/report/fiscal_book_purchase_report.rml',
    parser=parser_fiscal_book_purchase_report,
    header=False
    )
