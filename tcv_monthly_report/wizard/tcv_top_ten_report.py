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

    def _clear_lines(self, cr, uid, ids, context):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        unlink_ids = []
        for item in self.browse(cr, uid, ids, context={}):
            for l in item.line_ids:
                unlink_ids.append((2, l.id))
            self.write(cr, uid, ids, {'line_ids': unlink_ids}, context=context)
        return True

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
        'top_qty': fields.integer(
            'Top qty'),
        'remove_zero': fields.boolean(
            'Remove zero'),
        'line_ids': fields.one2many(
            'tcv.top.ten.report.lines', 'line_id', 'Lines', readonly=True),
        }

    _defaults = {
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company').
        _company_default_get(cr, uid, self._name, context=c),
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    def load_report_data(self, cr, uid, ids, lines_ord, data, params, context):
        res = {}
        for row in data:
            row_month = 'm%02d' % row[1]
            #~ row_seq = row[2]
            row_name = row[3]
            row_area = row[4]
            if row_name:
                if not res.get(row_name):
                    res[row_name] = {'name': row_name}
                res[row_name].update({row_month: row_area})
        lines = []
        for key in lines_ord:
            lines.append((0, 0, res.get(key, {'name': key})))
        self._clear_lines(cr, uid, ids, context)
        self.write(cr, uid, ids, {'line_ids': lines,
                                  'loaded': bool(lines)}, context=context)
        if params.get('remove_zero'):
            for item in self.browse(cr, uid, ids, context={}):
                unlink_ids = []
                for line in item.line_ids:
                    if not line.total:
                        unlink_ids.append((2, line.id))
                if unlink_ids:
                    self.write(cr, uid, [item.id], {'line_ids': unlink_ids},
                               context=context)
        return True

    ##-------------------------------------------------------- buttons (object)

    def button_load_top_ten_lines(self, cr, uid, ids, context=None):
        '''
            Replace in inheriteds models
        '''
        return True

    def button_print(self, cr, uid, ids, context=None):
        return False

    ##------------------------------------------------------------ on_change...

    def on_change_date(self, cr, uid, ids, date_start, date_en):
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
