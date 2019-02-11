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

##------------------------------------------------- tcv_liquidity_report_wizard


class tcv_liquidity_report_wizard(osv.osv_memory):

    _name = 'tcv.liquidity.report.wizard'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def default_get(self, cr, uid, fields, context=None):
        data = super(tcv_liquidity_report_wizard, self).\
            default_get(cr, uid, fields, context)
        year = datetime.now().year
        month = datetime.now().month
        if not data.get('date_from'):
            data['date_from'] = '%s-%s-01' % (year, month)
        if not data.get('date_to'):
            data['date_to'] = time.strftime('%Y-%m-%d')
        data.update({'posted': True,
                     'loaded': False,
                     })
        return data

    def _get_account_balance(self, cr, uid, account_id, operator,
                             date_balance, posted, context):
        and_posted = "AND m.state = 'posted'" if posted else ''
        cr.execute('''
            select sum(debit-credit) as balance_in_currency
            FROM account_move_line l
            left join account_move m on l.move_id = m.id
            WHERE l.account_id = %s AND
                  l.date %s '%s' %s
            ''' % (account_id, operator, date_balance, and_posted))
        return cr.dictfetchone()['balance_in_currency'] or 0

    def _get_account_moves(self, cr, uid, account_id,
                           date_from, date_to, posted, context):
        and_posted = "AND m.state = 'posted'" if posted else ''
        cr.execute('''
            select l.id, l.move_id, l.ref, l.name, l.date, l.debit, l.credit,
                   l.partner_id
            FROM account_move_line l
            left join account_move m on l.move_id = m.id
            WHERE l.account_id = %s AND
                  l.date between '%s' and '%s' %s
            ORDER BY l.date, l.id
            ''' % (account_id, date_from, date_to, and_posted))
        return cr.dictfetchall()

    ##--------------------------------------------------------- function fields

    _columns = {
        'account_id': fields.many2one(
            'account.account', 'Account', required=True, ondelete='restrict'),
        'date_from': fields.date(
            'Date from', required=True),
        'date_to': fields.date(
            'Date to', required=True),
        'posted': fields.boolean(
            'Posted', help="Only posted entries"),
        'loaded': fields.boolean(
            'Loaded'),
        'line_ids': fields.one2many(
            'tcv.liquidity.report.wizard.lines', 'line_id', 'Account noves',
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
        'balance': fields.float(
            'Balance', digits_compute=dp.get_precision('Account'),
            readonly=True),

        }

    _defaults = {
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company').
        _company_default_get(cr, uid, self._name, context=c),
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    def clear_wizard_lines(self, cr, uid, item, context):
        unlink_ids = []
        for l in item.line_ids:
            unlink_ids.append(l.id)
        obj_lin = self.pool.get('tcv.liquidity.report.wizard.lines')
        if unlink_ids:
            obj_lin.unlink(cr, uid, unlink_ids, context=context)
        return unlink_ids

    def load_wizard_lines(self, cr, uid, ids, context):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        lines = []
        totals = {'initial': 0,
                  'debit': 0,
                  'credit': 0,
                  'balance': 0}
        for item in self.browse(cr, uid, ids, context={}):
            self.clear_wizard_lines(cr, uid, item, context)
            ini_bal = self._get_account_balance(
                cr, uid, item.account_id.id, '<', item.date_from, item.posted,
                context)
            line = {'name': _('Initial balance'),
                    'ref': '',
                    'date': item.date_from,
                    'debit': abs(ini_bal) if ini_bal > 0 else 0,
                    'credit': abs(ini_bal) if ini_bal < 0 else 0,
                    'balance': ini_bal,
                    }
            totals['initial'] = ini_bal
            lines.append((0, 0, line))
            balance = ini_bal
            for m in self._get_account_moves(cr, uid, item.account_id.id,
                                             item.date_from, item.date_to,
                                             item.posted, context):
                balance += m['debit'] - m['credit']
                line = {'name': m['name'],
                        'ref': m['ref'],
                        'date': m['date'],
                        'debit': m['debit'],
                        'credit': m['credit'],
                        'balance': balance,
                        'move_id': m['move_id'],
                        'move_line_id': m['id'],
                        'partner_id': m['partner_id'] and m['partner_id'] or 0,
                        }
                lines.append((0, 0, line))
                totals['debit'] += m['debit']
                totals['credit'] += m['credit']
            end_bal = self._get_account_balance(
                cr, uid, item.account_id.id, '<=', item.date_to, item.posted,
                context)
            line = {'name': _('End balance'),
                    'ref': '',
                    'date': item.date_to,
                    'debit': abs(end_bal) if end_bal > 0 else 0,
                    'credit': abs(end_bal) if end_bal < 0 else 0,
                    'balance': end_bal,
                    }
            lines.append((0, 0, line))
            totals['balance'] = balance
            totals.update({'line_ids': lines, 'loaded': True})
            self.write(cr, uid, [item.id], totals, context=context)
        return True

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    def on_change_account_id(self, cr, uid, ids, account_id):
        res = {}
        res.update({'loaded': False})
        return {'value': res}

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_liquidity_report_wizard()


##------------------------------------------- tcv_liquidity_report_wizard_lines


class tcv_liquidity_report_wizard_lines(osv.osv_memory):

    _name = 'tcv.liquidity.report.wizard.lines'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'line_id': fields.many2one(
            'tcv.liquidity.report.wizard', 'String', required=True,
            ondelete='cascade'),
        'ref': fields.char(
            'Ref', size=64, required=False, readonly=False),
        'name': fields.char(
            'Name', size=128, required=False, readonly=False),
        'date': fields.date(
            'Date', required=True, readonly=True,
            states={'draft': [('readonly', False)]}, select=True),
        'debit': fields.float(
            'Debit', digits_compute=dp.get_precision('Account')),
        'credit': fields.float(
            'Credit', digits_compute=dp.get_precision('Account')),
        'balance': fields.float(
            'Balance', digits_compute=dp.get_precision('Account')),
        'move_id': fields.many2one(
            'account.move', 'Accounting entries', ondelete='restrict',
            help="The move of this entry line.", select=True, readonly=True),
        'move_line_id': fields.many2one(
            'account.move.line', 'Accounting line', ondelete='restrict',
            help="The move line of this entry.", select=True, readonly=True),
        'partner_id': fields.many2one(
            'res.partner', 'Partner', readonly=True, ondelete='restrict'),

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

    ##---------------------------------------------------------------- Workflow

tcv_liquidity_report_wizard_lines()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
