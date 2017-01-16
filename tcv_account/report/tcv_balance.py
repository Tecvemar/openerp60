# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description: Report parser for: tcv_balance
#
#
##############################################################################
from report import report_sxw
from tools.translate import _
from datetime import datetime
from osv import fields, osv
#~ import pooler
import decimal_precision as dp
import time
#~ import netsvc


__TOTAL_CODE__ = 'z' * 20


class parser_tcv_balance(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        context = context or {}
        super(parser_tcv_balance, self).__init__(
            cr, uid, name, context=context)
        self.localcontext.update({
            'get_name': self._get_name,
            })
        self.context = context

    def _get_name(self, o):
        name = _('Situational balance') if o.type == 'balance' \
            else _('Result balance')
        return name

report_sxw.report_sxw(
    'report.tcv.balance.report',
    'tcv.balance',
    'addons/tcv_account/report/tcv_balance.rml',
    parser=parser_tcv_balance,
    header=False
    )


##----------------------------------------------------------------- tcv_balance


class tcv_balance(osv.osv_memory):

    _name = 'tcv.balance'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def default_get(self, cr, uid, fields, context=None):
        data = super(tcv_balance, self).\
            default_get(cr, uid, fields, context)
        year = datetime.now().year
        if not data.get('date_from'):
            data['date_from'] = '%s-01-01' % (year)
        if not data.get('date_to'):
            data['date_to'] = time.strftime('%Y-%m-%d')
        data.update({'loaded': False})
        return data

    def _compute_result(self, atype, lines):
        res = 0
        for l in lines:
            if l.account_id.level == 1:
                if atype == 'balance':
                    res += l.balance
                else:
                    res += l.amount_period
        return res

    def _add_account(self, account, balance, level):
        res = []
        if account.type == 'view' and \
                account.level < level:
            res.append({
                'code': account.code,
                'account_id': account.id,
                })
            code_tot = '%s%s' % (account.code, __TOTAL_CODE__)
            res.append({
                'code': code_tot,
                'account_id': account.id,
                'total': True,
                'debit': balance if balance >= 0 else 0,
                'credit': abs(balance) if balance < 0 else 0,
                })
        else:
            res.append({
                'code': account.code,
                'account_id': account.id,
                'debit': balance if balance >= 0 else 0,
                'credit': abs(balance) if balance < 0 else 0,
                })
        return res

    def _add_result_accounts(self, cr, uid, acc_id, result,
                             level, balance_id):
        result_acc_ids = []
        result_codes = []
        res = []
        obj_tbl = self.pool.get('tcv.trial.balance.lines')
        obj_acc = self.pool.get('account.account')
        acc = obj_acc.browse(cr, uid, acc_id, context=None)
        while acc.parent_id and acc.parent_id.level >= 0:
            result_acc_ids.append(acc.id)
            acc = acc.parent_id
        for acc_id in result_acc_ids:
            acc = obj_acc.browse(cr, uid, acc_id, context=None)
            if not obj_tbl.search(cr, uid, [('account_id', '=', acc_id),
                                            ('line_id', '=', balance_id)]):
                if acc.level <= level:
                    lines = self._add_account(acc, 0, level)
                    result_codes.append(lines[-1]['code'])
                    res.extend(lines)
            else:
                if acc.level < level:
                    result_codes.append(acc.code + __TOTAL_CODE__)
                elif acc.level == level:
                    result_codes.append(acc.code)
        return res, result_codes

    ##--------------------------------------------------------- function fields

    _columns = {
        'type': fields.selection(
            [('balance', 'Situational balance'),
             ('profit_loss', 'Result balance')],
            string='Type', required=True, readonly=False),
        'date_from': fields.date(
            'Date from', required=False),
        'date_to': fields.date(
            'Date to', required=True),
        'line_ids': fields.one2many(
            'tcv.balance.lines', 'line_id', 'Account balance',
            readonly=True),
        'loaded': fields.boolean(
            'Loaded'),
        'non_zero': fields.boolean(
            'No zero lines', help="Hide 0 balance accounts"),
        'show_code': fields.boolean(
            'Show code', help="Show accounts code"),
        'use_ident': fields.boolean(
            'Use ident', help="Use identation"),
        'level': fields.integer(
            'Account level', help="0=All levels"),
        'print_cols': fields.selection(
            [(1, '1'), (2, '2')], string='Print columns', required=True),
        'company_id': fields.many2one(
            'res.company', 'Company', required=True, readonly=True,
            ondelete='restrict'),
        }

    _defaults = {
        'type': lambda *a: 'balance',
        'loaded': lambda *a: False,
        'non_zero': lambda *ad: True,
        'show_code': lambda *a: False,
        'use_ident': lambda *a: True,
        'print_cols': lambda *a: 1,
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company').
        _company_default_get(cr, uid, self._name, context=c),
        }

    _sql_constraints = [
        ('level_range', 'CHECK(level between 0 and 9)',
         'The level must be in 0-9 range!'),
        ('print_cols_range', 'CHECK(print_cols between 1 and 2)',
         'The Print columns must be 1 or 2!'),
        ('date_to_gt_date_from', 'CHECK (date_to>=date_from)',
         'The from date must be < the to date'),
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    def clear_wizard_lines(self, cr, uid, item, context):
        unlink_ids = []
        for l in item.line_ids:
            unlink_ids.append(l.id)
        obj_lin = self.pool.get('tcv.balance.lines')
        if unlink_ids:
            obj_lin.unlink(cr, uid, unlink_ids, context=context)
        return unlink_ids

    ##-------------------------------------------------------- buttons (object)

    def load_wizard_lines(self, cr, uid, ids, context):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        obj_per = self.pool.get('account.period')
        obj_tba = self.pool.get('tcv.trial.balance')
        obj_tbl = self.pool.get('tcv.trial.balance.lines')
        obj_acc = self.pool.get('account.account')
        #~ tot_23 = 0
        lines = []
        for item in self.browse(cr, uid, ids, context={}):
            self.clear_wizard_lines(cr, uid, item, context)
            period_id = obj_per.find(cr, uid, item.date_to)[0]
            period = obj_per.browse(cr, uid, period_id, context=context)
            # Create trial balance
            values = {
                'date_from': period.date_start if item.type == 'balance' else
                item.date_from,
                'date_to': item.date_to,
                'non_zero': item.non_zero,
                'total_view': True,
                'level': item.level or None,
                }
            tba_id = obj_tba.create(cr, uid, values, context=None)
            obj_tba.load_wizard_lines(cr, uid, tba_id, context=None)
            level = item.level or 99
            # Get ids from trial balance lines
            balance_acc_ids = obj_acc.search(cr, uid, [('code', '<', '4')])
            balance_ids = obj_tbl.search(
                cr, uid, [('account_id', 'in', balance_acc_ids),
                          ('line_id', '=', tba_id)])
            result_ids = obj_tbl.search(
                cr, uid, [('account_id', 'not in', balance_acc_ids),
                          ('line_id', '=', tba_id)])
            # Add trial balance & totals lines
            report_ids = balance_ids if item.type == 'balance' else result_ids
            for l in obj_tbl.browse(cr, uid, report_ids, context=None):
                amount = l.balance if item.type == 'balance' else \
                    l.amount_period
                lines.extend(self._add_account(
                    l.account_id, amount, level))

            # Add extra lines
            result_acc_id = obj_acc.search(
                cr, uid, [('type', '=', 'consolidation'),
                          ('company_id', '=', item.company_id.id)])[0]
            result = self._compute_result(
                item.type, obj_tbl.browse(cr, uid, result_ids, context=None))
            if item.type == 'balance':
                if result or not item.non_zero:
                    result_lines, result_codes = self._add_result_accounts(
                        cr, uid, result_acc_id, result, level, tba_id)
                    lines.extend(result_lines)
                    if level == 1:
                        tot_23_codes = ('2', '3')
                    else:
                        tot_23_codes = ('2' + __TOTAL_CODE__,
                                        '3' + __TOTAL_CODE__)
                    tot_23 = 0
                    for l in lines:
                        if l['code'] in result_codes:
                            balance = l['debit'] - l['credit'] + result
                            l.update({
                                'debit': balance if balance >= 0 else 0,
                                'credit': abs(balance) if balance < 0 else 0,
                                })
                        if l['code'] in tot_23_codes:
                            tot_23 += l['debit'] - l['credit']
                    lines.append({
                        'code': __TOTAL_CODE__ + __TOTAL_CODE__,
                        'total': True,
                        'debit': tot_23 if tot_23 >= 0 else 0,
                        'credit': abs(tot_23) if tot_23 < 0 else 0,
                        })
            else:
                lines.append({
                    'code': __TOTAL_CODE__,
                    'total': True,
                    'debit': result if result >= 0 else 0,
                    'credit': abs(result) if result < 0 else 0,
                    })
            line_ids = sorted(lines, key=lambda k: k['code'])
            self.write(cr, uid, [item.id], {
                'line_ids': [(0, 0, x) for x in line_ids],
                'loaded': True}, context=None)
        return True

    ##------------------------------------------------------------ on_change...

    def on_change_data(self, cr, uid, ids, loaded):
        res = {}
        res.update({'loaded': False})
        return {'value': res}

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_balance()


class tcv_balance_lines(osv.osv_memory):

    _name = 'tcv.balance.lines'

    _description = ''

    _order = 'code'

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    def _compute_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for item in self.browse(cr, uid, ids, context=context):
            if item.line_id.show_code:
                acc_name = '[%s] %s' % (item.account_id.code,
                                        item.account_id.name)
            else:
                acc_name = item.account_id.name
            ident = ' ' * 8 if item.line_id.use_ident else ''

            if item.total:
                acc_name = _('TOTAL %s') % acc_name

            if item.code == __TOTAL_CODE__:
                res[item.id] = {'acc_name': _('Profit and loss result')}
            elif item.code == __TOTAL_CODE__ + __TOTAL_CODE__:
                res[item.id] = {'acc_name': _('TOTAL PASIVE AND PATRIM')}
            else:
                res[item.id] = {
                    'acc_name': '%s%s' % (ident * (item.account_id.level - 1),
                                          acc_name),
                    }
            res[item.id].update({'balance': item.debit - item.credit})
        return res

    ##-------------------------------------------------------------------------

    _columns = {
        'line_id': fields.many2one(
            'tcv.balance', 'String', required=True, ondelete='cascade'),
        'code': fields.char(
            'Code', size=64, required=False, readonly=False),
        'account_id': fields.many2one(
            'account.account', 'Account', required=False, ondelete='restrict'),
        'acc_name': fields.function(
            _compute_all, method=True, type='char', size=128,
            string='Account', multi='all'),
        'total': fields.float(
            'Total'),
        'type': fields.related(
            'account_id', 'type', type='char', size=16, store=False),
        'debit': fields.float(
            'Debit', digits_compute=dp.get_precision('Account'),
            required=True),
        'credit': fields.float(
            'Credit', digits_compute=dp.get_precision('Account'),
            required=True),
        'balance': fields.function(
            _compute_all, method=True, type='float',
            string='Balance', multi='all'),
        }

    _defaults = {
        'total': lambda *a: False,
        'debit': lambda *a: 0,
        'credit': lambda *a: 0,
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_balance_lines()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
