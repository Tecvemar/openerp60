# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description: Report parser for: tcv_invoice_report
#
#
##############################################################################
#~ import time
#~ import pooler
from report import report_sxw
from tools.translate import _


class parser_tcv_invoice_report(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        context = context or {}
        super(parser_tcv_invoice_report, self).__init__(
            cr, uid, name, context=context)
        self.localcontext.update({
            'get_wh_number': self._get_wh_number,
            'get_currency_rate': self._get_currency_rate,
            'get_sel_str': self._get_sel_str,
            'get_summary': self._get_summary,
            'get_wh_lines': self._get_wh_lines,
            'get_wh_move': self._get_wh_move,
            })
        self.context = context

    def _get_wh_number(self, obj, wh_type):
        number = ''
        if wh_type == 'islr':
            awil_obj = self.pool.get('islr.wh.doc.line')
            awil_ids = awil_obj.search(
                self.cr, self.uid, [('invoice_id', '=', obj.id)], context=None)
            awil_brws = awil_obj.browse(
                self.cr, self.uid, awil_ids, context=None)
            number = awil_brws and awil_brws[0].islr_wh_doc_id and \
                awil_brws[0].islr_wh_doc_id.number or ''
        elif wh_type == 'iva':
            awil_obj = self.pool.get('account.wh.iva.line')
            awil_ids = awil_obj.search(
                self.cr, self.uid, [('invoice_id', '=', obj.id)], context=None)
            awil_brws = awil_obj.browse(
                self.cr, self.uid, awil_ids, context=None)
            print awil_brws
            number = awil_brws and awil_brws[0].retention_id and \
                awil_brws[0].retention_id.number or ''
        return number

    def _get_currency_rate(self, obj):
        #~ obj: self.pool.get('account.invoice').browse
        obj_inv = self.pool.get('account.invoice')
        # implemented in tcv_purchase
        rate = obj_inv.get_invoice_currency_rate(
            self.cr, self.uid, obj)
        return rate

    def _get_sel_str(self, type, val):
        if not type or not val:
            return ''
        values = {'state': {'draft': _('Draft'),
                            'done': _('Done'),
                            'posted': _('Posted'),
                            'open': _('Open'),
                            'paid': _('Paid'),
                            'cancel': _('Cancelled')},
                  'type': {'transfer': _('Transfer'),
                           'dbn': _('Db/N'),
                           'crn': _('Cr/N')}}
        return values[type].get(val, '')

    def _get_summary(self, obj_lines, fields):
        '''
        obj_lines: an obj.line_ids (lines to be totalized)
        fields: tuple with totalized field names

        Use in rml:
        [[ repeatIn(get_summary(o.line_ids, ('fld_1', 'fld_2'..)), 't') ]]
        '''
        totals = {}
        for key in fields:
            totals[key] = 0
        for line in obj_lines:
            for key in fields:
                totals[key] += line[key]
        return [totals]

    def _get_wh_lines(self, obj):
        res = []
        # Withholding ISLR
        obj_wdi = self.pool.get('islr.wh.doc.invoices')
        obj_whd = self.pool.get('islr.wh.doc')
        wdi_ids = obj_wdi.search(
            self.cr, self.uid, [('invoice_id', '=', obj.id)])
        if wdi_ids:
            for item in obj_wdi.browse(self.cr, self.uid, wdi_ids,
                                       context=None):
                islr = obj_whd.browse(self.cr, self.uid,
                                      item.islr_wh_doc_id.id,
                                      context=None)
                res.append({
                    'type': 'ISLR',
                    'number': islr.number,
                    'date': islr.date_ret,
                    'amount': item.amount_islr_ret,
                    'move': item.move_id and item.move_id.name,
                    'move_id': item.move_id,
                    })
        # Withholding IVA
        obj_wil = self.pool.get('account.wh.iva.line')
        obj_awi = self.pool.get('account.wh.iva')
        wil_ids = obj_wil.search(
            self.cr, self.uid, [('invoice_id', '=', obj.id)])
        if wil_ids:
            for item in obj_wil.browse(self.cr, self.uid, wil_ids,
                                       context=None):
                iva = obj_awi.browse(self.cr, self.uid,
                                     item.retention_id.id,
                                     context=None)
                res.append({
                    'type': 'IVA',
                    'number': iva.number,
                    'date': iva.date_ret,
                    'amount': item.amount_tax_ret,
                    'move': item.move_id and item.move_id.name,
                    'move_id': item.move_id,
                    })
        return res

    def _get_wh_move(self, move_id):
        obj_mov = self.pool.get('account.move')
        move = obj_mov.browse(self.cr, self.uid, move_id, context=None)
        res = {
            'date': move.date}
        print res
        return res

report_sxw.report_sxw('report.tcv.invoice.report',
                      'account.invoice',
                      'addons/tcv_account/report/tcv_invoice_report.rml',
                      parser=parser_tcv_invoice_report,
                      header=False
                      )
