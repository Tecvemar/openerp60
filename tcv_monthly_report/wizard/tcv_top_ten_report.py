# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2014-11-03
#    Version: 0.0.0.1
#
#    Description:
#
#
##############################################################################

#~ from datetime import datetime
from osv import fields, osv
#~ from tools.translate import _
#~ import pooler
#~ import decimal_precision as dp
import time
#~ import netsvc


##---------------------------------------------------------- tcv_top_ten_report


class tcv_top_ten_report(osv.osv_memory):

    _name = 'tcv.top.ten.report'

    _description = ''

    ##-------------------------------------------------------------------------

    def default_get(self, cr, uid, fields, context=None):
        data = super(tcv_top_ten_report, self).default_get(
            cr, uid, fields, context)
        data.update({
            'date_start': time.strftime('%Y-01-01'),
            'date_end': time.strftime('%Y-12-31'),
            })
        return data

    ##------------------------------------------------------- _internal methods

    def _get_sql_params(self, item, context=None):
        return {'date_start': '%s 00:00:00' % item.date_start,
                'date_end': '%s 23:59:59' % item.date_end,
                'limit': item.top_qty,
                'comany_id': item.company_id.id,
                }

    def _clear_lines(self, cr, uid, ids, context):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        unlink_ids = []
        for item in self.browse(cr, uid, ids, context={}):
            for l in item.line_ids:
                unlink_ids.append((2, l.id))
            self.write(
                cr, uid, ids, {'line_ids': unlink_ids, 'loaded': False},
                context=context)
        return True

    def _change_year(self, cr, uid, ids, value, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        for item in self.browse(cr, uid, ids, context={}):
            date = time.strptime(item.date_end, '%Y-%m-%d')
            year = date.tm_year + value
            data = {'date_start': '%4i-01-01' % (year),
                    'date_end': '%4i-12-31' % (year)
                    }
            data.update(self.on_change_date(
                cr, uid, ids, data.get('date_start'), data.get('date_end'),
                item.type).get('value'))
            self.write(cr, uid, [item.id], data, context=context)

        return False

    ##--------------------------------------------------------- function fields

    _columns = {
        'company_id': fields.many2one(
            'res.company', 'Company', required=True, readonly=True,
            ondelete='restrict'),
        'name': fields.char(
            'Name', size=64, required=False, readonly=True),
        'date_start': fields.date(
            'From', required=True, select=True),
        'date_end': fields.date(
            'To', required=True, select=True),
        'loaded': fields.boolean(
            'Loaded'),
        'top_qty': fields.selection(
            [(5, '5'), (10, '10'), (25, '25'), (50, '50'), (100, '100')],
            string='Top qty', required=True),
        'remove_zero': fields.boolean(
            'Remove zero'),
        'type': fields.selection(
            [('', '')], string='Type', required=True,
            readonly=False),
        'line_ids': fields.one2many(
            'tcv.top.ten.report.lines', 'line_id', 'Lines', readonly=True),
        'add_summary': fields.boolean(
            'Summary', required=True, help="Add summary at report's bottom"),
        }

    _defaults = {
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company').
        _company_default_get(cr, uid, self._name, context=c),
        'top_qty': lambda *a: 10,
        'add_summary': lambda *a: True,
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    def load_report_data(self, cr, uid, item, context):
        '''
            Replace in inheriteds models
        '''
        return []

    ##-------------------------------------------------------- buttons (object)

    def button_load_top_ten_lines(self, cr, uid, ids, context=None):
        '''
            Load data in line's model
        '''
        self._clear_lines(cr, uid, ids, context)
        for item in self.browse(cr, uid, ids, context={}):
            data = self.load_report_data(cr, uid, item, context)
            data.update({'loaded': True})
            self.write(cr, uid, [item.id], data, context=context)
        return True

    def button_print(self, cr, uid, ids, context=None):
        return False

    def button_prev_year(self, cr, uid, ids, context=None):
        return self._change_year(cr, uid, ids, -1, context)

    def button_next_year(self, cr, uid, ids, context=None):
        return self._change_year(cr, uid, ids, 1, context)

    ##------------------------------------------------------------ on_change...

    def on_change_date(self, cr, uid, ids, date_start, date_end, atype):
        res = {}
        self._clear_lines(cr, uid, ids, context=None)
        res.update({'loaded': False, 'line_ids': []})
        return {'value': res}

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow


tcv_top_ten_report()


##---------------------------------------------------- tcv_top_ten_report_lines


class tcv_top_ten_report_lines(osv.osv_memory):

    _name = 'tcv.top.ten.report.lines'

    _description = ''

    _order = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'line_id': fields.many2one(
            'tcv.top.ten.report', 'Line', required=True,
            ondelete='cascade'),
        'name': fields.char(
            'Name', size=128, required=False, readonly=True),
        'quantity': fields.float(
            'Quantity', digits=(14, 2), readonly=True),
        'amount': fields.float(
            'Amount', digits=(14, 2), readonly=True),
        }

    _defaults = {
        'quantity': lambda *a: 0,
        'amount': lambda *a: 0,
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow


tcv_top_ten_report_lines()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
