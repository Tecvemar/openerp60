# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description: Report parser for: tcv_stock_book_detail
#
#
##############################################################################
from report import report_sxw
#~ from datetime import datetime
from osv import fields, osv
#~ from tools.translate import _
#~ import pooler
import decimal_precision as dp
#~ import time
#~ import netsvc


##------------------------------------------------ parser_tcv_stock_book_detail


class parser_tcv_stock_book_detail(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        context = context or {}
        super(parser_tcv_stock_book_detail, self).__init__(
            cr, uid, name, context=context)
        self.localcontext.update({
            'get_summary': self._get_summary,
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

report_sxw.report_sxw(
    'report.tcv.stock.book.detail.report',
    'tcv.stock.book.detail',
    'addons/tcv_stock_book/report/tcv_stock_book_detail.rml',
    parser=parser_tcv_stock_book_detail,
    header=False
    )


##------------------------------------------------------- tcv_stock_book_detail


class tcv_stock_book_detail(osv.osv_memory):

    _name = 'tcv.stock.book.detail'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def default_get(self, cr, uid, fields, context=None):
        data = super(tcv_stock_book_detail, self).default_get(
            cr, uid, fields, context)
        line_ids = []
        for item in context.get('report_data', []):
            line2_ids = []
            for item2 in item.get('lines_sort', []):
                line2_ids.append({
                    'name': item2['name'],
                    'name_ro': item2['name'],
                    'amount': item2['amount'],
                    'amount_ro': item2['amount'],
                    })
            line_ids.append({
                'name': '[%s] %s' % (item['code'], item['name']),
                'name_ro': '[%s] %s' % (item['code'], item['name']),
                'amount_total': item['amount_total'],
                'amount_total_ro': item['amount_total'],
                'line2_ids': line2_ids,
                })
        data.update({'line_ids': line_ids})
        return data

    ##--------------------------------------------------------- function fields

    _columns = {
        'name': fields.char(
            'Name', size=64, required=False, readonly=False),
        'company_id': fields.many2one(
            'res.company', 'Company', required=True, readonly=True,
            ondelete="restrict"),
        'period_id': fields.many2one(
            'account.period', 'Period', required=True, readonly=True,
            ondelete="restrict"),
        'line_ids': fields.one2many(
            'tcv.stock.book.detail.lines', 'line_id', 'String'),
        }

    _defaults = {
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    def button_print(self, cr, uid, ids, context=None):

        return True

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_stock_book_detail()


##------------------------------------------------- tcv_stock_book_detail_lines


class tcv_stock_book_detail_lines(osv.osv_memory):

    _name = 'tcv.stock.book.detail.lines'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'line_id': fields.many2one(
            'tcv.stock.book.detail', 'String', required=True,
            ondelete='cascade'),
        'name': fields.char(
            'Name', size=64, required=False, readonly=False),
        'name_ro': fields.char(
            'Name', size=64, required=False, readonly=True),
        'amount_total': fields.float(
            'Amount total', digits_compute=dp.get_precision('Account'),
            readonly=False),
        'amount_total_ro': fields.float(
            'Amount total', digits_compute=dp.get_precision('Account'),
            readonly=True),
        'line2_ids': fields.one2many(
            'tcv.stock.book.detail.lines2', 'line2_id', 'String',
            readonly=False),
        }

    _defaults = {
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    def create(self, cr, uid, vals, context=None):
        vals.update({
            'name_ro': vals.get('name'),
            'amount_total_ro': vals.get('amount_total'),
            })
        res = super(tcv_stock_book_detail_lines, self).create(
            cr, uid, vals, context)
        return res

    ##---------------------------------------------------------------- Workflow

tcv_stock_book_detail_lines()


##------------------------------------------------ tcv_stock_book_detail_lines2


class tcv_stock_book_detail_lines2(osv.osv_memory):

    _name = 'tcv.stock.book.detail.lines2'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'line2_id': fields.many2one(
            'tcv.stock.book.detail.lines', 'String', required=True,
            ondelete='cascade'),
        'name': fields.char(
            'Name', size=64, required=False, readonly=False),
        'amount': fields.float(
            'Amount', digits_compute=dp.get_precision('Account'),
            readonly=False),
        'name_ro': fields.char(
            'Name', size=64, required=False, readonly=True),
        'amount_ro': fields.float(
            'Amount', digits_compute=dp.get_precision('Account'),
            readonly=True),
        }

    _defaults = {
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    def create(self, cr, uid, vals, context=None):
        vals.update({
            'name_ro': vals.get('name'),
            'amount_ro': vals.get('amount'),
            })
        res = super(tcv_stock_book_detail_lines2, self).create(
            cr, uid, vals, context)
        return res

    ##---------------------------------------------------------------- Workflow

tcv_stock_book_detail_lines2()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
