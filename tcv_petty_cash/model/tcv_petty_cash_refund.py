# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Gabriel Gamez
#    Creation Date: 07/06/2012
#    Version: 0.0.0.1
#
#    Description:
#
#
##############################################################################
#~ from datetime import datetime
from osv import fields, osv
from tools.translate import _
import decimal_precision as dp
import time


local_petty_cash_refund_data = {}


class tcv_petty_cash_refund(osv.osv):

    _name = 'tcv.petty.cash.refund'

    _description = 'Modulo de gestion de reposicion de caja chica'

    _order = 'name desc'

    STATE_SELECTION = [
        ('draft', 'Draft'),
        ('solicited', 'Solicited'),
        ('refunded', 'Refunded'),
        ('cancel', 'Cancelled')
        ]

    def _total_refund(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for dep in self.browse(cr, uid, ids, context=context):
            res[dep.id] = {
                'amount_total': 0.0,
            }
            for line in dep.line_ids:
                res[dep.id]['amount_total'] += line.amount
        return res

    _columns = {
        'name': fields.char('Reference', size=32, readonly=True),
        'petty_cash_id': fields.many2one('tcv.petty.cash.config.detail',
                                         'Petty cash',
                                         required=True,
                                         readonly=True, ondelete='restrict',
                                         states={'draft': [('readonly',
                                                            False)]}),
        'rel_journal': fields.related('petty_cash_id', 'journal_id',
                                      type='many2one',
                                      relation='account.journal',
                                      string='Journal name',
                                      store=False, readonly=True),
        'user_id': fields.related('petty_cash_id', 'user_id', type='many2one',
                                  relation='res.users', string='Custodian',
                                  store=True, readonly=True),
        'currency_id': fields.related('petty_cash_id', 'currency_id',
                                      type='many2one', relation='res.currency',
                                      string='Currency', store=False,
                                      readonly=True),
        'date': fields.date('Date', required=True, readonly=True,
                            states={'draft': [('readonly', False)]},
                            select=True),
        'date_solicited': fields.datetime('Date solicited', required=False,
                                          readonly=True, select=True),
        'date_refund': fields.datetime('Date refund', required=False,
                                       readonly=True, select=True),
        'company_id': fields.many2one('res.company', 'Company', required=True,
                                      readonly=True, ondelete='restrict',
                                      states={'draft': [('readonly', False)]}),
        'move_id': fields.many2one('account.move', 'Account move',
                                   ondelete='restrict',
                                   help="The move of this entry line.",
                                   select=2, readonly=True),
        'state': fields.selection(STATE_SELECTION, string='State',
                                  required=True, readonly=True),
        'line_ids': fields.one2many('tcv.petty.cash.refund.line', 'line_id',
                                    'Details', ondelete='cascade'),
        'amount_total': fields.function(
            _total_refund, method=True,
            digits_compute=dp.get_precision('Account'),
            string='Total', store=True, multi='all'),
        'narration': fields.text('Notes', readonly=False),
        'reconcile_id': fields.many2one('account.move.reconcile', 'Reconcile',
                                        readonly=True, ondelete='set null',
                                        select=2),
        'voucher_id': fields.many2one('account.voucher', 'Refund voucher',
                                      readonly=True, ondelete='set null',
                                      select=2),
        }

    _defaults = {
        'name': lambda *a: '/',
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company').
        _company_default_get(cr, uid, 'tcv_petty_cash_refund', context=c),
        'state': 'draft',
        }

    _sql_constraints = []

    def button_compute_click(self, cr, uid, ids, context=None):
        return True

    def button_refund_pay(self, cr, uid, ids, context=None):
        if not ids:
            return []
        item = self.browse(cr, uid, ids[0], context=context)

        return {
            'name': _("Petty cash refund"),
            'view_mode': 'form',
            'view_id': self.pool.get('ir.ui.view').
            search(cr, uid, [('model', '=', 'account.voucher'),
                             ('name', '=', 'account.voucher.payment.form')]),
            'view_type': 'form',
            'res_model': 'account.voucher',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'domain': '[]',
            'context': {
                'default_partner_id': item.company_id.partner_id.id,
                'default_amount': item.amount_total,
                'default_reference': item.name,
                'default_name': _("Petty cash refund"),
                'close_after_process': True,
                'default_type': 'payment',
                'default_voucher_type': 'normal',
                'default_payment_doc': 'cash',
                'petty_cash_refund_id': item.id,
                }
        }

    def on_change_petty_cash_id(self, cr, uid, ids, petty_cash_id):
        global local_petty_cash_refund_data
        res = {}
        if petty_cash_id:
            org = self.pool.get('tcv.petty.cash.config.detail').\
                browse(cr, uid, petty_cash_id, context=None)
            res = {'value': {'rel_journal': org.journal_id.id,
                             'user_id': org.user_id.id,
                             'currency_id': org.currency_id.id}}
            local_petty_cash_refund_data.update(
                {'rel_journal': org.journal_id.id,
                 'rel_account': org.journal_id.default_credit_account_id.id})
        return res

    def action_view_add_multi_lines(self, cr, uid, ids, context):
        return True

    def _gen_account_move_line(self, company_id, partner_id, account_id,
                               name, debit, credit):
        return (0, 0, {'auto': True,
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
        obj_move = self.pool.get('account.move')
        obj_per = self.pool.get('account.period')
        move_id = None
        for rfd in self.browse(cr, uid, ids, context={}):
            move = {'ref': '%s' % (context.get('refund_reference', 'rcch')),
                    'journal_id': rfd.rel_journal.id,
                    'date': rfd.date,
                    'period_id': obj_per.find(cr, uid, rfd.date)[0],
                    'company_id': rfd.company_id.id,
                    'state': 'draft',
                    'to_check': False,
                    'narration': '',
                    }
            lines = []
            move_name = _('Petty cash refund: %s') % \
                (context.get('refund_reference', 'rcch'))
            lines.append(self._gen_account_move_line(
                rfd.company_id.id,
                False,
                rfd.petty_cash_id.journal_id.default_debit_account_id.id,
                move_name,
                rfd.amount_total,
                0))
            lines.append(self._gen_account_move_line(
                rfd.company_id.id,
                rfd.company_id.partner_id.id,
                rfd.petty_cash_id.acc_petty_cash_refund.id,
                move_name,
                0,
                rfd.amount_total))
            lines.reverse()
            move.update({'line_id': lines})
            move_id = obj_move.create(cr, uid, move, context)
            if move_id:
                self.do_reconcile(cr, uid, rfd, move_id, context)
        return move_id

    def do_unreconcile(self, cr, uid, ids, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        res = []
        for rfd in self.browse(cr, uid, ids, context={}):
            if rfd.state == 'solicited':
                if rfd.move_id:
                    move_id = rfd.move_id.id
                    obj_move = self.pool.get('account.move')
                    if rfd.move_id.state == 'draft':
                        recon_id = 0
                        for line in rfd.line_ids:
                            if line.move_line and not recon_id and \
                                    line.move_line.reconcile_id.id:
                                recon_id = line.move_line.reconcile_id.id
                        if recon_id:
                            obj_lines = self.pool.get('account.move.line')
                            rec_ids = obj_lines.search(
                                cr, uid, [('reconcile_id', '=', recon_id)])
                            obj_lines._remove_move_reconcile(
                                cr, uid, rec_ids, context=context)
                        obj = self.pool.get('tcv.petty.cash.refund')
                        vals = {'move_id': 0, 'reconcile_id': 0}
                        res = obj.write(cr, uid, ids, vals, context)
                        obj_move.unlink(cr, uid, [move_id])
        return res

    def unlink(self, cr, uid, ids, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        unlink_ids = []
        for dep in self.browse(cr, uid, ids, context={}):
            if dep.state in ('draft', 'cancel'):
                unlink_ids.append(dep['id'])
            else:
                raise osv.except_osv(
                    _('Invalid action !'),
                    _('Cannot delete a petty cash refund that are ' +
                      'already doned!'))
        super(tcv_petty_cash_refund, self).unlink(cr, uid, unlink_ids, context)
        return True

    def button_solicited(self, cr, uid, ids, context=None):
        context = context or {}
        if len(ids) != 1:
            raise osv.except_osv(_('Error!'),
                                 _('Multiplies validations not allowed.'))
        for rfd in self.browse(cr, uid, ids, context={}):
            if rfd.name != '/':
                name = rfd.name
            else:
                name = self.pool.get('ir.sequence').\
                    get(cr, uid, 'petty.cash.refund')
            date_solicited = time.strftime('%Y-%m-%d %H:%M:%S')
            context.update({'refund_reference': name,
                            'date_solicited': date_solicited})
            obj = self.pool.get('tcv.petty.cash.refund')
            vals = {'state': 'solicited',
                    'date_solicited': date_solicited,
                    'name': name,
                    'move_id': self._gen_account_move(cr, uid, ids, context),
                    }
            res = obj.write(cr, uid, ids, vals, context)
        return res

    def test_draft(self, cr, uid, ids, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        for rfd in self.browse(cr, uid, ids, context={}):
            if rfd.move_id.state != 'draft':
                raise osv.except_osv(
                    _('Error!'),
                    _('You cant revert posted or reconcilied entries.'))
        return True

    def test_solicited(self, cr, uid, ids, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        for rfd in self.browse(cr, uid, ids, context={}):
            if time.strptime(rfd.date, '%Y-%m-%d') > time.localtime():
                raise osv.except_osv(_('Invalid date!'),
                                     _('The date must be <= today.'))
            if not rfd.amount_total:
                raise osv.except_osv(_('Invalid amount!'),
                                     _('The total must be > 0'))
            if rfd.amount_total > rfd.petty_cash_id.amount:
                raise osv.except_osv(_('Invalid amount!'),
                                     _('The total must be < %.2f') %
                                     rfd.petty_cash_id.amount)
            if rfd.petty_cash_id.user_id.id != uid:
                raise osv.except_osv(
                    _('Invalid user!'),
                    _('Only the petty cash custodian can solicite this ' +
                      'refund.'))
            for l in rfd.line_ids:
                if rfd.date < l.move_line.date:
                    raise osv.except_osv(
                        _('Error!'),
                        _('You can\'t solicite the refund of move whith a ' +
                          'date after refund\'s date. (%s)') % l.move_line.ref)
        return True

    def test_refunded(self, cr, uid, ids, context=None):
        return True

    def button_refunded(self, cr, uid, ids, context=None):
        context = context or {}
        if len(ids) != 1:
            raise osv.except_osv(
                _('Error!'),
                _('Multiplies validations not allowed.'))
        for rfd in self.browse(cr, uid, ids, context={}):
            date_refund = time.strftime('%Y-%m-%d %H:%M:%S')
            obj = self.pool.get('tcv.petty.cash.refund')
            vals = {'state': 'refunded',
                    'date_refund': date_refund,
                    }
            res = obj.write(cr, uid, ids, vals, context)
        return res

    def do_reconcile(self, cr, uid, rfd, move_id, context):
        obj_move = self.pool.get('account.move')
        move = obj_move.browse(cr, uid, move_id, context)
        # Post (Approve) account.move
        obj_move.post(cr, uid, [move_id], context=context)
        rec_ids = []
        for line in rfd.line_ids:
            if line.move_line.id:
                rec_ids.append(line.move_line.id)
        for line in move.line_id:
            if line.account_id.id == \
                    rfd.rel_journal.default_credit_account_id.id:
                rec_ids.append(line.id)
        if rec_ids:
            obj_move_line = self.pool.get('account.move.line')
            r_id = obj_move_line.reconcile(cr, uid, rec_ids, context=context)
            vals = {'reconcile_id': r_id}
            self.write(cr, uid, [rfd.id], vals, context)
        return True

tcv_petty_cash_refund()


class tcv_petty_cash_refund_line(osv.osv):

    _name = 'tcv.petty.cash.refund.line'

    _description = ''

    _columns = {
        'line_id': fields.many2one('tcv.petty.cash.refund',
                                   'Deposit lines', required=True,
                                   ondelete='cascade'),
        'rel_journal': fields.many2one('account.journal', 'Rel journal',
                                       readonly=True, store=False,
                                       ondelete='restrict'),
        'rel_account': fields.many2one('account.account',
                                       'Journal account', readonly=True,
                                       store=False, ondelete='restrict'),
        'move_line': fields.many2one('account.move.line', 'Move',
                                     ondelete='restrict'),
        'name': fields.related('move_line', 'name', type='char',
                               string='Name', size=64, store=False,
                               readonly=True),
        'partner_id': fields.related('move_line', 'partner_id',
                                     type='many2one', relation='res.partner',
                                     string='Partner', store=False,
                                     readonly=True),
        'amount_move': fields.related('move_line', 'credit', type='float',
                                      string='Move amount', store=False),
        'amount': fields.float('Amount',
                               digits_compute=dp.get_precision('Account')),
        }

    _defaults = {'rel_journal': 0,
                 'rel_account': 0,
                 }

    def on_change_move_line(self, cr, uid, ids, move_line):
        res = {}
        if move_line:
            move = self.pool.get('account.move.line').\
                browse(cr, uid, move_line, context=None)
            res = {'value': {'amount_move': move.credit,
                             'amount': move.credit,
                             'partner_id': move.partner_id.id,
                             'name': move.name}}
        return res

    def create(self, cr, uid, vals, context=None):
        if not 'amount' in vals and 'amount_move' in vals:
            vals.update({'amount': vals['amount_move']})
        return super(tcv_petty_cash_refund_line, self).\
            create(cr, uid, vals, context)

    def default_get(self, cr, uid, fields, context=None):
        global local_petty_cash_refund_data
        context = context or {}
        res = super(tcv_petty_cash_refund_line, self).\
            default_get(cr, uid, fields, context=context)
        if local_petty_cash_refund_data:
            res.update(local_petty_cash_refund_data)
        return res

tcv_petty_cash_refund_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
