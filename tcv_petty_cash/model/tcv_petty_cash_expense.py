# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2014-01-27
#    Version: 0.0.0.1
#
#    Description:
#
#
##############################################################################

#~ from datetime import datetime
from osv import fields, osv
from tools.translate import _
#~ import pooler
import decimal_precision as dp
import time
#~ import netsvc

##-------------------------------------------------- tcv_petty_cash_expense_acc


class tcv_petty_cash_expense_acc(osv.osv):

    _name = 'tcv.petty.cash.expense.acc'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'ref': fields.char('Ref', size=32, required=False, readonly=False),
        'name': fields.char('Name', size=64, required=True, readonly=False),
        'company_id': fields.many2one('res.company', 'Company', required=True,
                                      readonly=True, ondelete='restrict'),
        'account_id': fields.many2one('account.account', 'Account',
                                      required=True, ondelete='restrict'),
        'active': fields.boolean('Active', required=True),
        }

    _defaults = {
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company').
        _company_default_get(cr, uid, self._name, context=c),
        'active': lambda *a: True,
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_petty_cash_expense_acc()


##------------------------------------------------------ tcv_petty_cash_expense


class tcv_petty_cash_expense(osv.osv):

    _name = 'tcv.petty.cash.expense'

    _description = ''

    _order = 'ref desc'

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def _gen_account_move_line(self, company_id, partner_id, account_id, name,
                               debit, credit):
        return (0, 0,
                {'auto': True,
                 'company_id': company_id,
                 'partner_id': partner_id,
                 'account_id': account_id,
                 'name': name,
                 'debit': debit,
                 'credit': credit,
                 'reconcile': False,
                 })

    def _gen_account_move(self, cr, uid, ids, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        so_brw = self.browse(cr, uid, ids, context={})
        obj_move = self.pool.get('account.move')
        move_id = None
        for exp in so_brw:
            move = {'ref': exp.ref,
                    'journal_id': exp.petty_cash_id.journal_id.id,
                    'date': exp.date,
                    'company_id': exp.company_id.id,
                    'state': 'draft',
                    'to_check': False,
                    'narration': '',
                    }
            lines = []
            lines.append(self._gen_account_move_line(
                exp.company_id.id,
                False,
                exp.petty_cash_id.journal_id.default_credit_account_id.id,
                exp.name,
                0,
                exp.amount))
            lines.append(self._gen_account_move_line(
                exp.company_id.id,
                False,
                exp.expense_id.account_id.id,
                exp.name,
                exp.amount,
                0))
            move.update({'line_id': lines})
            move_id = obj_move.create(cr, uid, move, context)
            if move_id:
                self.write(cr, uid, [exp.id], {'move_id': move_id},
                           context=context)
                obj_move.post(cr, uid, [move_id], context=context)
        return move_id

    ##--------------------------------------------------------- function fields

    _columns = {
        'ref': fields.char('Reference', size=32, required=False,
                           readonly=True),
        'date': fields.date('Date', required=True, readonly=True,
                            states={'draft': [('readonly', False)]},
                            select=True),
        'name': fields.char(
            'Description', size=64, required=False, readonly=True,
            states={'draft': [('readonly', False)]}),
        'expense_id': fields.many2one('tcv.petty.cash.expense.acc', 'Expense',
                                      required=True, ondelete='restrict',
                                      readonly=True,
                                      states={'draft': [('readonly', False)]},
                                      ),
        'petty_cash_id': fields.many2one(
            'tcv.petty.cash.config.detail', 'Petty cash', required=True,
            ondelete='restrict',
            readonly=True,
            states={'draft': [('readonly', False)]}),
        'amount': fields.float('Amount',
                               digits_compute=dp.get_precision('Account'),
                               readonly=True,
                               states={'draft': [('readonly', False)]}),
        'move_id': fields.many2one('account.move', 'Account move',
                                   ondelete='restrict',
                                   select=True, readonly=True,
                                   help="The move of this entry line."),
        'user_id': fields.many2one('res.users', 'User', readonly=True,
                                   select=True, ondelete='restrict'),
        'company_id': fields.many2one('res.company', 'Company', required=True,
                                      readonly=True, ondelete='restrict'),
        'state': fields.selection([('draft', 'Draft'),
                                   ('done', 'Done'),
                                   ('cancel', 'Cancelled')],
                                  string='State', required=True,
                                  readonly=True),
        'narration': fields.text(
            'Notes', readonly=False),
        }

    _defaults = {
        'ref': lambda *a: '/',
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company').
        _company_default_get(cr, uid, self._name, context=c),
        'user_id': lambda s, c, u, ctx: u,
        'state': lambda *a: 'draft',
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        }

    _sql_constraints = [
        ]

    ##-----------------------------------------------------

    ##----------------------------------------------------- public methods

    ##----------------------------------------------------- buttons (object)

    ##----------------------------------------------------- on_change...

    ##----------------------------------------------------- create write unlink

    def create(self, cr, uid, vals, context=None):
        if not vals.get('ref') or vals.get('ref') == '/':
            vals.update({'ref': self.pool.get('ir.sequence').
                         get(cr, uid, 'tcv.petty.cash.expense')})
        res = super(tcv_petty_cash_expense, self).create(cr, uid, vals,
                                                         context)
        return res

    def unlink(self, cr, uid, ids, context=None):
        so_brw = self.browse(cr, uid, ids, context={})
        unlink_ids = []
        for exp in so_brw:
            if exp.state in ('draft', 'cancel'):
                unlink_ids.append(exp.id)
            else:
                raise osv.except_osv(
                    _('Invalid action !'),
                    _('Cannot delete a petty cash expense that are '
                      'already done!'))
        super(tcv_petty_cash_expense, self).unlink(
            cr, uid, unlink_ids, context)
        return True

    ##----------------------------------------------------- Workflow

    def button_draft(self, cr, uid, ids, context=None):
        vals = {'state': 'draft', 'move_id': False}
        return self.write(cr, uid, ids, vals, context)

    def button_done(self, cr, uid, ids, context=None):
        vals = {'state': 'done',
                'move_id': self._gen_account_move(cr, uid, ids, context)}
        return self.write(cr, uid, ids, vals, context)

    def button_cancel(self, cr, uid, ids, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        pce_brw = self.browse(cr, uid, ids, context={})[0]
        move_id = pce_brw.move_id and pce_brw.move_id.id
        vals = {'state': 'cancel', 'move_id': False}
        res = self.write(cr, uid, ids, vals, context)
        if move_id:
            obj_move = self.pool.get('account.move')
            obj_move.unlink(cr, uid, [move_id])
        return res

    def test_draft(self, cr, uid, ids, *args):
        return True

    def test_done(self, cr, uid, ids, *args):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        for item in self.browse(cr, uid, ids, context={}):
            if not item.amount > 0:
                raise osv.except_osv(
                    _('Error!'),
                    _('You must indicate an amount > 0. (%s)') %
                    (item.ref))
        return True

    def test_cancel(self, cr, uid, ids, *args):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        for item in self.browse(cr, uid, ids, context={}):
            if item.move_id and item.move_id.state != 'draft':
                raise osv.except_osv(
                    _('Error!'),
                    _('You cant revert posted or reconcilied entries. (%s)') %
                    (item.ref))
        return True

tcv_petty_cash_expense()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
