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

##---------------------------------------------------------- tcv_monthly_report


class tcv_monthly_report(osv.osv_memory):
    '''
    This is a base report for all monthly report, must be inherit by any
    module before use.
    the rml and wizard files are common, only need to override:
        __..._ANUAL_REPORT_TYPES__:
            list with report's types
        button_load_monthly_lines:
            Caller to "data load" process
        type (field):
            Must be overited with __..._ANUAL_REPORT_TYPES__
        default_get:
            Overwrite to set report's name
        params:
            Report parameters, see get_report_default_params

    Samples:
        tcv_mrp/report/tcv_mrp_anual_report
        tcv_sale/report/tcv_sale_anual_report
    '''

    _name = 'tcv.monthly.report'

    _description = ''

    ##-------------------------------------------------------------------------

    def default_get(self, cr, uid, fields, context=None):
        data = super(tcv_monthly_report, self).default_get(
            cr, uid, fields, context)
        data.update({
            'date_start': time.strftime('%Y-01-01'),
            'date_end': time.strftime('%Y-12-31'),
            'pct_type': self._get_pct_type(data.get('type')) or 'none',
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

    def _get_pct_type(self, type):
        return 'none'

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
        'remove_zero': fields.boolean(
            'Remove zero'),
        'line_ids': fields.one2many(
            'tcv.monthly.report.lines', 'line_id', 'Lines',
            readonly=True),
        'line_p_ids': fields.one2many(
            'tcv.monthly.report.lines', 'line_id', 'Lines pct',
            readonly=True),
        'line_q_ids': fields.one2many(
            'tcv.monthly.report.lines', 'line_id', 'Lines qt',
            readonly=True),
        'line_pq_ids': fields.one2many(
            'tcv.monthly.report.lines', 'line_id', 'Lines pct qt',
            readonly=True),
        'add_summary': fields.boolean(
            'Summary', required=True, help="Add summary at bottom"),
        'digits': fields.integer(
            'Digits', help='Decimals in report'),
        'show_m': fields.boolean(
            'Show monthlys values', required=True,
            help="Show monthlys values in report"),
        'show_q': fields.boolean(
            'Show quarters values', required=True,
            help="Show quarters values in report"),
        'show_p': fields.boolean(
            'Show pct values', required=True,
            help="Show pct values in report"),
        'type': fields.selection(
            [('', '')], string='Type', required=True,
            readonly=False),
        'pct_type': fields.selection(
            [('none', 'None'), ('row', 'Row'), ('col', 'Col')],
            string='Pct type', required=True,
            readonly=True),
        }

    _defaults = {
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company').
        _company_default_get(cr, uid, self._name, context=c),
        'remove_zero': lambda *a: True,
        'add_summary': lambda *a: False,
        'digits': lambda *a: 2,
        'show_m': lambda *a: True,
        'show_p': lambda *a: True,
        'show_q': lambda *a: True,
        'pct_type': lambda *a: 'none',
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    def get_report_default_params(self, cr, uid, ids, brw):
        '''
        Set default parameter for anual report
        '''
        params = {
            'name': brw.name,
            'date_start': brw.date_start,
            'date_end': brw.date_end,
            'type': brw.type,
            'remove_zero': brw.remove_zero,
            'company_id': brw.company_id.id,
            'add_summary': False,  # Show totals at report's bottom
            'digits': 2,  # Decimal places on print
            }
        return params

    def load_report_data(self, cr, uid, ids, lines_ord, data, params, context):
        '''
        Load report data from inherited models
            lines_ord: list with lines "names" order criteria
            data: data lines, for tcv.monthly.report.lines model
            params: global params for report (see get_report_default_params)
        '''
        ids = isinstance(ids, (int, long)) and [ids] or ids
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
        item = self.browse(cr, uid, ids, context=context)[0]
        data = {'line_ids': lines,
                'loaded': bool(lines),
                'add_summary': params.get('add_summary'),
                'digits': params.get('digits'),
                'pct_type': self._get_pct_type(item.type),
                }
        self.write(cr, uid, ids, data, context=context)
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

    def button_load_monthly_lines(self, cr, uid, ids, context=None):
        '''
            Replace in inheriteds models
        '''
        return True

    def button_print(self, cr, uid, ids, context=None):
        return False

    def button_prev_year(self, cr, uid, ids, context=None):
        return self._change_year(cr, uid, ids, -1, context)

    def button_next_year(self, cr, uid, ids, context=None):
        return self._change_year(cr, uid, ids, 1, context)

    ##------------------------------------------------------------ on_change...

    def on_change_date(self, cr, uid, ids, date_start, date_end, type):
        res = {}
        self._clear_lines(cr, uid, ids, context=None)
        res.update({'loaded': False,
                    'line_ids': [],
                    'pct_type': self._get_pct_type(type)})
        return {'value': res}

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_monthly_report()


##---------------------------------------------------- tcv_monthly_report_lines


class tcv_monthly_report_lines(osv.osv_memory):

    _name = 'tcv.monthly.report.lines'

    _description = ''

    _order = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def _compute_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        pct_type = 'none'
        tot_col = {}
        tot_col_q = {}
        for i in range(1, 13):
            tk = 't%02d' % i
            tot_col.update({tk: 0})
            if i < 5:  # Quarter pct
                tot_col_q.update({tk: 0})
        for item in self.browse(cr, uid, ids, context=context):
            pct_type = item.line_id.pct_type
            total = 0
            q1 = item.m01 + item.m02 + item.m03
            q2 = item.m04 + item.m05 + item.m06
            q3 = item.m07 + item.m08 + item.m09
            q4 = item.m10 + item.m11 + item.m12
            total = q1 + q2 + q3 + q4
            res[item.id] = {
                'total': total,
                'q1': q1,
                'q2': q2,
                'q3': q3,
                'q4': q4,
                }
            for i in range(1, 13):  # Monthly pct
                pk = 'p%02d' % i
                res[item.id][pk] = 0
                if i < 5:  # Quarter pct
                    pqk = 'pq%d' % i
                    res[item.id][pqk] = 0
            for i in range(1, 13):  # Monthly pct
                mk = 'm%02d' % i
                qk = 'q%d' % i
                pk = 'p%02d' % i
                pqk = 'pq%d' % i
                tk = 't%02d' % i
                if pct_type == 'row':
                    res[item.id][pk] = item[mk] * 100 / total if total else 0
                elif pct_type == 'col':
                    tot_col[tk] += item[mk]
                if i < 5:  # Quarter pct
                    if pct_type == 'row':
                        res[item.id][pqk] = (item[mk] * 100) \
                            / total if total else 0
                    elif pct_type == 'col':
                        tot_col_q[tk] += res[item.id][qk]
        if pct_type == 'col':
            for item in self.browse(cr, uid, ids, context=context):
                for i in range(1, 13):  # Monthly pct
                    mk = 'm%02d' % i
                    qk = 'q%d' % i
                    pk = 'p%02d' % i
                    pqk = 'pq%d' % i
                    tk = 't%02d' % i
                    res[item.id][pk] = (item[mk] * 100) \
                        / tot_col[tk] if tot_col[tk] else 0
                    if i < 5:  # Quarter pct
                        res[item.id][pqk] = (res[item.id][qk] * 100) \
                            / tot_col_q[tk] if tot_col_q[tk] else 0
        return res

    ##--------------------------------------------------------- function fields

    _columns = {
        'line_id': fields.many2one(
            'tcv.monthly.report', 'Line', required=True,
            ondelete='cascade'),
        'name': fields.char(
            'Name', size=128, required=False, readonly=True),
        'format': fields.char(
            'Name', size=16, required=False, readonly=False),
        'p01': fields.function(
            _compute_all, method=True, type='float', string='%01',
            digits=(5, 1), multi='all'),
        'p02': fields.function(
            _compute_all, method=True, type='float', string='%02',
            digits=(5, 1), multi='all'),
        'p03': fields.function(
            _compute_all, method=True, type='float', string='%03',
            digits=(5, 1), multi='all'),
        'p04': fields.function(
            _compute_all, method=True, type='float', string='%04',
            digits=(5, 1), multi='all'),
        'p05': fields.function(
            _compute_all, method=True, type='float', string='%05',
            digits=(5, 1), multi='all'),
        'p06': fields.function(
            _compute_all, method=True, type='float', string='%06',
            digits=(5, 1), multi='all'),
        'p07': fields.function(
            _compute_all, method=True, type='float', string='%07',
            digits=(5, 1), multi='all'),
        'p08': fields.function(
            _compute_all, method=True, type='float', string='%08',
            digits=(5, 1), multi='all'),
        'p09': fields.function(
            _compute_all, method=True, type='float', string='%09',
            digits=(5, 1), multi='all'),
        'p10': fields.function(
            _compute_all, method=True, type='float', string='%10',
            digits=(5, 1), multi='all'),
        'p11': fields.function(
            _compute_all, method=True, type='float', string='%11',
            digits=(5, 1), multi='all'),
        'p12': fields.function(
            _compute_all, method=True, type='float', string='%12',
            digits=(5, 1), multi='all'),
        'pq1': fields.function(
            _compute_all, method=True, type='float', string='%Q1',
            digits=(5, 1), multi='all'),
        'pq2': fields.function(
            _compute_all, method=True, type='float', string='%Q2',
            digits=(5, 1), multi='all'),
        'pq3': fields.function(
            _compute_all, method=True, type='float', string='%Q3',
            digits=(5, 1), multi='all'),
        'pq4': fields.function(
            _compute_all, method=True, type='float', string='%Q4',
            digits=(5, 1), multi='all'),
        'm01': fields.float(
            '01', digits=(14, 2), readonly=True),
        'm02': fields.float(
            '02', digits=(14, 2), readonly=True),
        'm03': fields.float(
            '03', digits=(14, 2), readonly=True),
        'm04': fields.float(
            '04', digits=(14, 2), readonly=True),
        'm05': fields.float(
            '05', digits=(14, 2), readonly=True),
        'm06': fields.float(
            '06', digits=(14, 2), readonly=True),
        'm07': fields.float(
            '07', digits=(14, 2), readonly=True),
        'm08': fields.float(
            '08', digits=(14, 2), readonly=True),
        'm09': fields.float(
            '09', digits=(14, 2), readonly=True),
        'm10': fields.float(
            '10', digits=(14, 2), readonly=True),
        'm11': fields.float(
            '11', digits=(14, 2), readonly=True),
        'm12': fields.float(
            '12', digits=(14, 2), readonly=True),
        'q1': fields.function(
            _compute_all, method=True, type='float', string='Q1',
            digits=(14, 2), multi='all'),
        'q2': fields.function(
            _compute_all, method=True, type='float', string='Q2',
            digits=(14, 2), multi='all'),
        'q3': fields.function(
            _compute_all, method=True, type='float', string='Q3',
            digits=(14, 2), multi='all'),
        'q4': fields.function(
            _compute_all, method=True, type='float', string='Q4',
            digits=(14, 2), multi='all'),
        'total': fields.function(
            _compute_all, method=True, type='float', string='Total',
            digits=(14, 2), multi='all'),
        }

    _defaults = {
        'm01': lambda *a: 0,
        'm02': lambda *a: 0,
        'm03': lambda *a: 0,
        'm04': lambda *a: 0,
        'm05': lambda *a: 0,
        'm06': lambda *a: 0,
        'm07': lambda *a: 0,
        'm08': lambda *a: 0,
        'm09': lambda *a: 0,
        'm10': lambda *a: 0,
        'm11': lambda *a: 0,
        'm12': lambda *a: 0,
        'q01': lambda *a: 0,
        'q02': lambda *a: 0,
        'q03': lambda *a: 0,
        'q04': lambda *a: 0,
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_monthly_report_lines()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
