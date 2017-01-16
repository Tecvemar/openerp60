# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2014-08-01
#    Version: 0.0.0.1
#
#    Description:
#
#
##############################################################################

from datetime import datetime
from osv import fields, osv
from tools.translate import _
#~ import pooler
import decimal_precision as dp
import time
#~ import netsvc

##------------------------------------------------- tcv_trial_balance


class tcv_trial_balance(osv.osv_memory):

    _name = 'tcv.trial.balance'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def default_get(self, cr, uid, fields, context=None):
        data = super(tcv_trial_balance, self).\
            default_get(cr, uid, fields, context)
        year = datetime.now().year
        month = datetime.now().month
        if not data.get('date_from'):
            data['date_from'] = '%s-%s-01' % (year, month)
        if not data.get('date_to'):
            data['date_to'] = time.strftime('%Y-%m-%d')
        data.update({'loaded': False})
        return data

    def _get_accounts_and_balance(self, cr, uid, params, context):
        '''
        params is a dict with keys: {
            'acc_from': ,  # acc code
            'acc_to': ,  # acc code
            'date_from': ,
            'date_to': ,
            'company_id': ,
            }
        to be passed as params to sql query
        '''
        cr.execute('''
select a.code, a.id, a.type, a.level,
       sum(b.initial) as initial,
       sum(b.debit) as debit,
       sum(b.credit) as credit,
       sum(b.debit) - sum(b.credit) as amount_period,
       sum(b.initial) + sum(b.debit) - sum(b.credit) as balance
from account_account a
left join (
    select a.id,
case when l.date < '%(date_from)s' then debit-credit else 0 end as initial,
case when l.date >= '%(date_from)s' then debit else 0 end as debit,
case when l.date >= '%(date_from)s' then credit else 0 end as credit
    FROM account_move_line l
    left join account_move m on l.move_id = m.id
    left join account_account a on l.account_id = a.id
    WHERE l.date <= '%(date_to)s' AND
  m.state = 'posted' and m.company_id = %(company_id)s
    ) as b on a.id = b.id
where a.company_id = %(company_id)s and
      a.code between '%(acc_from)s' AND '%(acc_to)s'
group by a.code, a.id, a.type, a.level
having sum(initial) != 0 or sum(debit) != 0 or sum(credit) != 0 or
       a.type = 'view'
order by a.code
            ''' % (params))
        res = cr.dictfetchall()
        #~ res_tot = []
        if params.get('total_view'):
            totals = {}
            for item in res:
                code = item['code']
                if item['type'] == 'view':
                    totals.update(
                        {code: {
                            'initial': 0,
                            'debit': 0,
                            'credit': 0,
                            'amount_period': 0,
                            'balance': 0}})
                else:
                    codes = [code[0], code[0:2], code[0:3], code[0:5]]
                    for key in codes:
                        for amount_key in ('initial', 'debit',
                                           'credit', 'amount_period',
                                           'balance'):
                            if totals.get(key):
                                totals[key][amount_key] += item[amount_key]
            #~ res_tot = []
            if totals:
                for item in res:
                    if item['type'] == 'view':
                        item.update(totals[item['code']])
        return res

    ##--------------------------------------------------------- function fields

    _columns = {
        'acc_from_id': fields.many2one(
            'account.account', 'Account From', ondelete='restrict'),
        'acc_to_id': fields.many2one(
            'account.account', 'Account To', ondelete='restrict'),
        'date_from': fields.date(
            'Date from', required=True),
        'date_to': fields.date(
            'Date to', required=True),
        'line_ids': fields.one2many(
            'tcv.trial.balance.lines', 'line_id', 'Account balance',
            readonly=True),
        'company_id': fields.many2one(
            'res.company', 'Company', required=True, readonly=True,
            ondelete='restrict'),
        'initial': fields.float(
            'Initial', digits_compute=dp.get_precision('Account'),
            readonly=True),
        'debit': fields.float(
            'Debit', digits_compute=dp.get_precision('Account'),
            readonly=True),
        'credit': fields.float(
            'Credit', digits_compute=dp.get_precision('Account'),
            readonly=True),
        'amount_period': fields.float(
            'Period Mov.', digits_compute=dp.get_precision('Account'),
            readonly=True),
        'balance': fields.float(
            'Balance', digits_compute=dp.get_precision('Account'),
            readonly=True),
        'loaded': fields.boolean(
            'Loaded'),
        'no_view': fields.boolean(
            'No view account', help="Hide view type accounts"),
        'non_zero': fields.boolean(
            'No zero lines', help="Hide 0 balance accounts"),
        'total_view': fields.boolean(
            'Totals on view accounts',
            help="Show total amount in view type accounts"),
        'level': fields.integer(
            'Account level', help="0=All levels"),
        'print_cols': fields.selection(
            [(4, '4'), (5, '5')], string='Print columns', required=True),
        'show_code': fields.boolean(
            'Show code', help="Show accounts code"),
        'use_ident': fields.boolean(
            'Use ident', help="Use identation"),
        }

    _defaults = {
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company').
        _company_default_get(cr, uid, self._name, context=c),
        'no_view': lambda *a: False,
        'non_zero': lambda *a: False,
        'total_view': lambda *a: False,
        'level': lambda *a: 0,
        'print_cols': lambda *a: 5,
        'show_code': lambda *a: False,
        'use_ident': lambda *a: True,
        }

    _sql_constraints = [
        ('level_range', 'CHECK(level between 0 and 9)',
         'The level must be in 0-9 range!'),
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    def clear_wizard_lines(self, cr, uid, item, context):
        unlink_ids = []
        for l in item.line_ids:
            unlink_ids.append(l.id)
        obj_lin = self.pool.get('tcv.trial.balance.lines')
        if unlink_ids:
            obj_lin.unlink(cr, uid, unlink_ids, context=context)
        return unlink_ids

    def load_wizard_lines(self, cr, uid, ids, context):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        totals = {'initial': 0,
                  'debit': 0,
                  'credit': 0,
                  'amount_period': 0,
                  'balance': 0}
        lines = []
        for item in self.browse(cr, uid, ids, context={}):
            self.clear_wizard_lines(cr, uid, item, context)
            params = {
                'acc_from': item.acc_from_id and item.acc_from_id.code or '1',
                'acc_to': item.acc_to_id and item.acc_to_id.code or '9' * 10,
                'date_from': item.date_from,
                'date_to': item.date_to,
                'company_id': item.company_id.id,
                'total_view': item.total_view,
                }
            for account in self._get_accounts_and_balance(
                    cr, uid, params, context):
                line = {
                    'account_id': account['id'],
                    'initial': account['initial'] or 0,
                    'debit': account['debit'] or 0,
                    'credit': account['credit'] or 0,
                    'amount_period': account['amount_period'] or 0,
                    'balance': account['balance'] or 0,
                    }
                if item.non_zero and not account['balance']:
                    False
                elif item.no_view and account['type'] == 'view':
                    False
                elif not item.no_view and item.level and \
                        account['level'] > item.level:
                    False
                else:
                    lines.append((0, 0, line))
                if account['type'] != 'view':
                    totals['initial'] += account['initial'] or 0
                    totals['debit'] += account['debit'] or 0
                    totals['credit'] += account['credit'] or 0
                    totals['amount_period'] += account['amount_period'] or 0
                    totals['balance'] += account['balance'] or 0
            totals.update({'line_ids': lines, 'loaded': True})
            self.write(cr, uid, [item.id], totals, context=context)
        return True

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    def on_change_account_id(self, cr, uid, ids):
        res = {}
        res.update({'loaded': False})
        return {'value': res}

    def on_change_no_view(self, cr, uid, ids, no_view):
        res = {}
        if no_view:
            res.update({'total_view': False, 'level': 0,
                        'use_ident': False, 'loaded': False})
        return {'value': res}

    def on_change_level(self, cr, uid, ids, level):
        res = {'loaded': False}
        if level < 0:
            res.update({'level': 0})
        elif level > 0:
            res.update({'total_view': True})
        return {'value': res}

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_trial_balance()


##----------------------------------------------------- tcv_trial_balance_lines


class tcv_trial_balance_lines(osv.osv_memory):

    _name = 'tcv.trial.balance.lines'

    _description = ''

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
            use_ident = item.line_id.use_ident and not item.line_id.no_view
            ident = ' ' * 8 if use_ident else ''
            res[item.id] = {
                'amount_period': item.debit - item.credit,
                'acc_name': '%s%s' % (ident * (item.account_id.level - 1),
                                      acc_name),
                }
        return res

    ##-------------------------------------------------------------------------

    _columns = {
        'line_id': fields.many2one(
            'tcv.trial.balance', 'String', required=True, ondelete='cascade'),
        'account_id': fields.many2one(
            'account.account', 'Account', required=True, ondelete='restrict'),
        'acc_name': fields.function(
            _compute_all, method=True, type='char', size=128,
            string='Account', multi='all'),
        'type': fields.related(
            'account_id', 'type', type='char', size=16, store=False),
        'initial': fields.float(
            'Initial', digits_compute=dp.get_precision('Account')),
        'debit': fields.float(
            'Debit', digits_compute=dp.get_precision('Account')),
        'credit': fields.float(
            'Credit', digits_compute=dp.get_precision('Account')),
        'amount_period': fields.function(
            _compute_all, method=True, type='float', string='Period Mov.',
            digits_compute=dp.get_precision('Account'), multi='all'),
        'balance': fields.float(
            'Balance', digits_compute=dp.get_precision('Account')),
        }

    _defaults = {
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    def button_liquidity(self, cr, uid, ids, context=None):
        item = self.browse(cr, uid, ids[0], context={})
        if item.type == 'view':
            return {}
        return {'name': _('Liquidity report'),
                'type': 'ir.actions.act_window',
                'res_model': 'tcv.liquidity.report.wizard',
                'view_type': 'form',
                'view_id': False,
                'view_mode': 'form',
                'nodestroy': True,
                'target': 'current',
                'domain': "",
                'context': {
                    'default_account_id': item.account_id.id,
                    'default_date_from': item.line_id.date_from,
                    'default_date_to': item.line_id.date_to,
                    'do_autoload': True,
                    }}

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_trial_balance_lines()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
