# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2014-05-09
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

##-------------------------------------------------------------- tcv_bank_moves


class tcv_bank_moves(osv.osv):

    _name = 'tcv.bank.moves'

    _description = ''

    ##-------------------------------------------------------------------------

    def copy(self, cr, uid, id, default={}, context=None, done_list=[],
             local=False):
        item = self.browse(cr, uid, id, context=context)
        default = default or {}
        default = default.copy()
        default.update({'number': (item.number or '') + '(copy)',
                        'ref': '/',
                        'name': '',
                        'narration': '',
                        'state': 'draft',
                        'move_id': False,
                        })
        return super(tcv_bank_moves, self).copy(cr, uid, id, default,
                                                context=context)

    ##------------------------------------------------------- _internal methods

    def default_get(self, cr, uid, fields, context=None):
        data = super(tcv_bank_moves, self).\
            default_get(cr, uid, fields, context)
        obj_com = self.pool.get('res.company')
        company_id = obj_com._company_default_get(cr, uid, 'tcv.bank.moves',
                                                  context=context)
        if company_id:
            com_brw = obj_com.browse(cr, uid, company_id, context=context)
            data.update({'partner_id': com_brw.partner_id.id})
        return data

    def _gen_account_move_line(self, it, account_id, name,
                               debit, credit, amount_currency):
        res = {'auto': True,
               'company_id': it.company_id.id,
               'partner_id': it.partner_id.id,
               'account_id': account_id,
               'name': name,
               'debit': debit,
               'credit': credit,
               'reconcile': False,
               }
        if (it.company_id.currency_id.id != it.currency_id.id and
            account_id in (it.bank_journal_id.default_debit_account_id.id,
                           it.bank_journal_id.default_credit_account_id.id,
                           )):
            res.update({'currency_id': it.currency_id.id,
                        'amount_currency': (
                            amount_currency if debit else -amount_currency)})
        return (0, 0, res)

    def _compute_currency_amount(self, cr, uid, item):
        if item.company_id.currency_id.id == item.currency_id.id:
            return item.amount, item.comission, item.wh_amount
        else:
            obj_cur = self.pool.get('res.currency')
            amount = obj_cur.compute(
                cr, uid, item.currency_id.id, item.company_id.currency_id.id,
                item.amount, context={'date': item.date})
            comission = obj_cur.compute(
                cr, uid, item.currency_id.id, item.company_id.currency_id.id,
                item.comission, context={'date': item.date})
            wh_amount = obj_cur.compute(
                cr, uid, item.currency_id.id, item.company_id.currency_id.id,
                item.wh_amount, context={'date': item.date})
            return amount, comission, wh_amount

    def _gen_account_move(self, cr, uid, ids, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        obj_move = self.pool.get('account.move')
        obj_per = self.pool.get('account.period')
        move_id = None
        for item in self.browse(cr, uid, ids, context={}):
            move = {
                'ref': u'%s Nº %s ' % (_(item.type), item.number),
                'journal_id': item.bank_journal_id.id,
                'date': item.date,
                'period_id': obj_per.find(cr, uid, item.date)[0],
                'company_id': item.company_id.id,
                'state': 'draft',
                'to_check': False,
                'narration': item.narration,
                }
            lines = []
            name = u'%s Nº %s, %s ' % (_(item.type), item.number, item.name)
            amount, comission, wh_amount = self._compute_currency_amount(
                cr, uid, item)
            if item.type == 'transfer':
                #  in transfer de credit line & commision line's
                lines.append(self._gen_account_move_line(
                    item,
                    item.bank_dest_journal_id.default_debit_account_id.id,
                    name,
                    amount,
                    0,
                    item.amount,
                    ))
                if item.comission:
                    lines.append(self._gen_account_move_line(
                        item,
                        item.expense_acc_id.id,
                        name,
                        comission,
                        0,
                        item.comission,
                        ))
                    lines.append(self._gen_account_move_line(
                        item,
                        item.bank_journal_id.default_credit_account_id.id,
                        name,
                        0,
                        comission,
                        item.comission,
                        ))
            else:  # Db/N or Cr/N
                lines.append(self._gen_account_move_line(
                    item,
                    item.bank_journal_id.default_debit_account_id.id if
                    item.type == 'crn' else
                    item.bank_journal_id.default_credit_account_id.id,
                    name,
                    amount if item.type == 'crn' else 0,
                    amount if item.type == 'dbn' else 0,
                    item.amount,
                    ))
            if item.type == 'transfer':
                lines.append(self._gen_account_move_line(
                    item,
                    item.bank_journal_id.default_credit_account_id.id,
                    name,
                    0,
                    amount,
                    item.amount,
                    ))
            else:
                lines.append(self._gen_account_move_line(
                    item,
                    item.expense_acc_id.id if
                    item.type != 'crn' else
                    item.income_acc_id.id,
                    name,
                    amount if item.type != 'crn' else 0,
                    amount if item.type == 'crn' else 0,
                    item.amount,
                    ))
            if item.type == 'crn' and item.wh_amount:
                lines.append(self._gen_account_move_line(
                    item,
                    item.wh_acc_id.id,
                    name,
                    wh_amount,
                    0,
                    item.wh_amount,
                    ))
                lines.append(self._gen_account_move_line(
                    item,
                    item.bank_journal_id.default_credit_account_id.id,
                    name,
                    0,
                    wh_amount,
                    item.wh_amount,
                    ))
            if item.type in ('transfer', 'crn'):
                lines.reverse()
            move.update({'line_id': lines})
            move_id = obj_move.create(cr, uid, move, context)
            obj_move.post(cr, uid, [move_id], context=context)
        return move_id

    ##--------------------------------------------------------- function fields

    def _compute_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for item in self.browse(cr, uid, ids, context=context):
            value = self.on_change_amount(cr, uid, [item.id],
                                          item.type,
                                          item.amount,
                                          item.comission,
                                          item.wh_amount)
            res[item.id] = {
                'amount_total': value['value'].get('amount_total')}
        return res

    _order = 'ref desc'

    _columns = {
        'ref': fields.char(
            'Ref', size=16, readonly=True),
        'number': fields.char(
            'Number', size=16, required=True, readonly=True,
            states={'draft': [('readonly', False)]}, ),
        'name': fields.char(
            'Name', size=64, required=False, readonly=True,
            states={'draft': [('readonly', False)]}, ),
        'date': fields.date(
            'Date', required=True, readonly=True,
            states={'draft': [('readonly', False)]}, select=True),
        'company_id': fields.many2one(
            'res.company', 'Company', required=True, readonly=True,
            ondelete='restrict'),
        'state': fields.selection(
            [('draft', 'Draft'), ('done', 'Done'), ('cancel', 'Cancelled')],
            string='State', required=True, readonly=True),
        'bank_journal_id': fields.many2one(
            'account.journal', 'Bank journal', required=True, readonly=True,
            states={'draft': [('readonly', False)]}, ondelete='restrict',
            domain=[('type', '=', 'bank')]),
        'bank_dest_journal_id': fields.many2one(
            'account.journal', 'Dest. bank', required=False, readonly=True,
            states={'draft': [('readonly', False)]}, ondelete='restrict',
            domain=[('type', '=', 'bank')]),
        'amount': fields.float(
            'Amount', digits_compute=dp.get_precision('Account'),
            required=True, readonly=True,
            states={'draft': [('readonly', False)]}),
        'comission': fields.float(
            'Comission', digits_compute=dp.get_precision('Account'),
            readonly=True, states={'draft': [('readonly', False)]}),
        'wh_amount': fields.float(
            'Wh amount (-)', digits_compute=dp.get_precision('Account'),
            readonly=True, states={'draft': [('readonly', False)]}),
        'amount_total': fields.function(
            _compute_all, method=True, type='float', string='Total amount',
            digits_compute=dp.get_precision('Account'), multi='all'),
        'type': fields.selection(
            [('transfer', 'Transfer'), ('dbn', 'Db/N'), ('crn', 'Cr/N')],
            string='Type', required=True, readonly=True,
            states={'draft': [('readonly', False)]}),
        'move_id': fields.many2one(
            'account.move', 'Account move', ondelete='restrict',
            help="The move of this entry line.", select=True, readonly=True),
        'expense_acc_id': fields.many2one(
            'account.account', 'Expense account', required=False,
            ondelete='restrict', readonly=True,
            domain="[('type','!=','view')]",
            states={'draft': [('readonly', False)]}),
        'income_acc_id': fields.many2one(
            'account.account', 'Income account', required=False,
            ondelete='restrict', readonly=True,
            domain="[('type','!=','view')]",
            states={'draft': [('readonly', False)]}),
        'wh_acc_id': fields.many2one(
            'account.account', 'Wh account', required=False,
            ondelete='restrict', readonly=True,
            domain="[('type','!=','view')]",
            states={'draft': [('readonly', False)]}),
        'currency_id': fields.many2one(
            'res.currency', 'Currency', readonly=True,
            states={'draft': [('readonly', False)]}),
        'narration': fields.text(
            'Notes', readonly=False),
        'partner_id': fields.many2one(
            'res.partner', 'Partner', readonly=True, required=True,
            states={'draft': [('readonly', False)]}, ondelete='restrict'),
        }

    _defaults = {
        'ref': lambda *a: '/',
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company').
        _company_default_get(cr, uid, self._name, context=c),
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        'state': lambda *a: 'draft',
        'type': lambda *a: 'transfer',
        'partner_id': lambda *a: 1,
        'currency_id': lambda self, cr, uid, c: self.pool.get('res.users').
        browse(cr, uid, uid, c).company_id.currency_id.id,
        }

    _sql_constraints = [
        ('bank_journal_distinct',
         'CHECK(bank_journal_id != bank_dest_journal_id)',
         'The bank journals must be distinct!'),
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    def on_change_amount(self, cr, uid, ids, type,
                         amount, comission, wh_amount):
        res = {}
        if type == 'transfer':
            res.update({'amount_total': amount + comission})
        elif type == 'dbn':
            res.update({'amount_total': amount})
        elif type == 'crn':
            res.update({'amount_total': amount - wh_amount})

        return {'value': res}

    ##----------------------------------------------------- create write unlink

    def create(self, cr, uid, vals, context=None):
        res = super(tcv_bank_moves, self).create(cr, uid, vals, context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        if vals.get('type') in ('dbn', 'crn'):
            vals.update({'bank_dest_journal_id': False,
                         'comission': 0})

        res = super(tcv_bank_moves, self).write(cr, uid, ids, vals, context)
        return res

    ##---------------------------------------------------------------- Workflow

    def button_draft(self, cr, uid, ids, context=None):
        vals = {'state': 'draft'}
        return self.write(cr, uid, ids, vals, context)

    def button_done(self, cr, uid, ids, context=None):
        vals = {'state': 'done',
                'move_id': self._gen_account_move(cr, uid, ids, context)}
        for item in self.browse(cr, uid, ids, context={}):
            if not item.ref or item.ref == '/':
                vals.update({'ref': self.pool.get('ir.sequence').get(
                    cr, uid, 'tcv.bank.moves')})
        return self.write(cr, uid, ids, vals, context)

    def button_cancel(self, cr, uid, ids, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        bm_brw = self.browse(cr, uid, ids, context={})[0]
        move_id = bm_brw.move_id and bm_brw.move_id.id
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
            if time.strptime(item.date, '%Y-%m-%d') > time.localtime():
                raise osv.except_osv(
                    _('Invalid date!'),
                    _('The date must be <= today.'))
            elif not item.amount_total:
                raise osv.except_osv(
                    _('No valid amount!'),
                    _('The total must be > 0'))
            if (item.type == 'transfer' and not item.expense_acc_id and
                item.comission) or \
                    (item.type == 'dbn' and not item.expense_acc_id):
                raise osv.except_osv(
                    _('Error!'),
                    _('You must specicy an expense account'))
            if item.type in ('crn', ):
                if not item.income_acc_id:
                    raise osv.except_osv(
                        _('Error!'),
                        _('You must specicy an income account'))
                if not item.wh_acc_id and item.wh_amount:
                    raise osv.except_osv(
                        _('Error!'),
                        _('You must specicy an whitholding account'))
        return True

    def test_cancel(self, cr, uid, ids, *args):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        for item in self.browse(cr, uid, ids, context={}):
            if item.move_id and item.move_id.state == 'posted':
                    raise osv.except_osv(
                        _('Error!'),
                        _('You can not cancel a bank move while the account ' +
                          'move is posted.'))
        return True

tcv_bank_moves()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
