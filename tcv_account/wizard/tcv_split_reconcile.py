# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2014-05-26
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
#~ import time
#~ import netsvc
#~ import logging
#~ logger = logging.getLogger('server')

##--------------------------------------------------------- tcv_split_reconcile


class tcv_split_reconcile(osv.osv_memory):

    _name = 'tcv.split.reconcile'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def _validate_split(self, cr, uid, ids, context):
        for item in self.browse(cr, uid, ids, context={}):
            if not item.debit:
                raise osv.except_osv(
                    _('Error!'),
                    _('Please select some debits'))
            if not item.credit:
                raise osv.except_osv(
                    _('Error!'),
                    _('Please select some credits'))
            sel_count, split_count, not_sel = 0, 0, 0
            for line in item.line_ids:
                if line.select:
                    sel_count += 1
                else:
                    not_sel += 1
                if line.split:
                    split_count += 1
                    if line.move_line_id.invoice:
                        raise osv.except_osv(
                            _('Error!'),
                            _('Can\'t split a line related to invoice'))
                    if line.move_line_id.period_id.state != 'draft':
                        raise osv.except_osv(
                            _('Error!'),
                            _('Can\'t split lines while accounting period ' +
                              'is closed (%s)') %
                              line.move_line_id.period_id.name)
                    if not line.select:
                        raise osv.except_osv(
                            _('Error!'),
                            _('Must select line to be splited'))
                    if (item.balance > 0 and line.debit < item.balance) or \
                            (item.balance < 0 and line.credit > item.balance):
                        raise osv.except_osv(
                            _('Error!'),
                            _('Invalid line to split'))
            if not not_sel:
                raise osv.except_osv(
                    _('Error!'),
                    _('Can\'t select all lines'))
            if sel_count < 1:
                raise osv.except_osv(
                    _('Error!'),
                    _('Must select at least 2 lines'))
            if split_count > 1:
                raise osv.except_osv(
                    _('Error!'),
                    _('Can\'t split more than 1 line'))
            if split_count == 1 and not item.balance:
                raise osv.except_osv(
                    _('Error!'),
                    _('No amount to split'))
            if split_count == 0 and item.balance:
                raise osv.except_osv(
                    _('Error!'),
                    _('Must select one line to split'))
        return True

    def _compute_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for item in self.browse(cr, uid, ids, context=context):
            debit, credit, balance = 0, 0, 0
            for line in item.line_ids:
                if line.select:
                    debit += line.debit
                    credit += line.credit
                    balance += line.balance
            res[item.id] = {
                'debit': debit, 'credit': credit, 'balance': round(balance, 4)}
        return res

    def _split_account_move_line(self, cr, uid, aml, split_amount, context):
        data = {
            'move_id': aml.move_id and aml.move_id.id or 0,
            'name': aml.name,
            'ref': aml.ref,
            'partner_id': aml.partner_id and aml.partner_id.id or 0,
            'journal_id': aml.journal_id and aml.journal_id.id or 0,
            'period_id': aml.period_id and aml.period_id.id or 0,
            'company_id': aml.company_id and aml.company_id.id or 0,
            'account_id': aml.account_id and aml.account_id.id or 0,
            'invoice': aml.invoice and aml.invoice.id or 0,
            'debit': aml.debit,
            'credit': aml.credit,
            'balance': aml.balance,
            'invoice': aml.statement_id and aml.statement_id.id or 0,
            'quantity': aml.quantity,
            'date': aml.date,
            'date_maturity': aml.date_maturity,
            'date_created': aml.date_created,
            'followup_line_id': aml.followup_line_id and
            aml.followup_line_id.id or 0,
            'followup_date': aml.followup_date,
            'tax_code_id': aml.tax_code_id and aml.tax_code_id.id or 0,
            'tax_amount': aml.tax_amount,
            'account_tax_id': aml.account_tax_id and
            aml.account_tax_id.id or 0,
            'currency_id': aml.currency_id and aml.currency_id.id or 0,
            'amount_currency': aml.amount_currency,
            'amount_residual': aml.amount_residual,
            'amount_currency': aml.amount_currency,
            'amount_residual_currency': aml.amount_residual_currency,
            'amount_to_pay': aml.amount_to_pay,
            'reconcile_id': aml.reconcile_id and aml.reconcile_id.id or 0,
            'reconcile_partial_id': aml.reconcile_partial_id and
            aml.reconcile_partial_id.id or 0,
            'state': aml.state,
            'blocked': aml.blocked,
            'analytic_account_id': aml.analytic_account_id and
            aml.analytic_account_id.id or 0,
            'narration': aml.narration,
            'centralisation': aml.centralisation,
            'product_id': aml.product_id and aml.product_id.id or 0,
            'product_uom_id': aml.product_uom_id and
            aml.product_uom_id.id or 0,
            }
        aml_fld = 'debit' if aml.debit else 'credit'
        move_posted = aml.move_id.state == 'posted'
        obj_mov = self.pool.get('account.move')
        obj_aml = self.pool.get('account.move.line')
        if move_posted:
            obj_mov.button_cancel(cr, uid, [aml.move_id.id], context=context)
        sql = "update account_move_line set " + \
              aml_fld + " = %(amount)s " + \
              "where id = %(aml_id)s"
        cr.execute(sql, {'amount': abs(split_amount[0]),
                         'aml_id': aml.id})
        data.update({aml_fld: abs(split_amount[1])})
        new_aml_id = obj_aml.create(cr, uid, data, context)
        if move_posted:
            obj_mov.post(cr, uid, [aml.move_id.id], context=context)
        return new_aml_id

    ##--------------------------------------------------------- function fields

    _columns = {
        'reconcile_id': fields.many2one(
            'account.move.reconcile', 'Reconcile', readonly=False,
            ondelete='set null', select=2),
        'create_date': fields.date(
            'Date', required=False, readonly=True,
            help="Reconciliation's date"),
        'account_id': fields.many2one(
            'account.account', 'Account', readonly=True,
            ondelete='restrict'),
        'line_ids': fields.one2many(
            'tcv.split.reconcile.lines', 'line_id', 'String'),
        'debit': fields.function(
            _compute_all, method=True, type='float', string='Debits',
            digits_compute=dp.get_precision('Account'), multi='all'),
        'credit': fields.function(
            _compute_all, method=True, type='float', string='Credits',
            digits_compute=dp.get_precision('Account'), multi='all'),
        'balance': fields.function(
            _compute_all, method=True, type='float', string='Balance',
            digits_compute=dp.get_precision('Account'), multi='all'),
        }

    _defaults = {
        'type': lambda *a: 'reconcile',
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    def clear_wizard_lines(self, cr, uid, item, context):
        unlink_ids = []
        for l in item.line_ids:
            unlink_ids.append(l.id)
        obj_lin = self.pool.get('tcv.split.reconcile.lines')
        if unlink_ids:
            obj_lin.unlink(cr, uid, unlink_ids, context=context)
        return unlink_ids

    ##-------------------------------------------------------- buttons (object)

    def load_wizard_lines(self, cr, uid, ids, context):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        for item in self.browse(cr, uid, ids, context={}):
            self.clear_wizard_lines(cr, uid, item, context)
            lines = []
            account_id = 0
            for line in (item.reconcile_id.line_id or
                         item.reconcile_id.line_partial_ids):
                lines.append({
                    'move_line_id': line.id,
                    'date': line.date,
                    'name': line.name,
                    'ref': line.ref,
                    'invoice_id': line.invoice and line.invoice.id or 0,
                    'partner_id': line.partner_id and line.partner_id.id or 0,
                    'move_id': line.move_id and line.move_id.id or 0,
                    'debit': line.debit,
                    'credit': line.credit,
                    'balance': line.debit - line.credit,
                    })
                if not account_id and line.account_id:
                    account_id = line.account_id.id
            if lines:
                data = {
                    'account_id': account_id,
                    'line_ids': [(0, 0, x) for x in lines],
                    'create_date': item.reconcile_id.create_date,
                    }
                self.write(cr, uid, [item.id], data, context=context)
        return True

    def button_compute(self, cr, uid, ids, context):
        return True

    def button_split(self, cr, uid, ids, context):
        obj_arc = self.pool.get('account.move.reconcile')
        obj_inv = self.pool.get('account.invoice')
        if self._validate_split(cr, uid, ids, context):
            for item in self.browse(cr, uid, ids, context={}):
                reconcile_ids = []
                invoice_ids = []
                split_id = 0
                split_brw = False
                split_amount = [0, 0]
                for line in item.line_ids:
                    if line.invoice_id:
                        invoice_ids.append(line.invoice_id.id)
                    if line.select:
                        if line.split:
                            split_id = line.move_line_id.id
                            split_brw = line.move_line_id
                            split_amount[0] = item.balance
                            split_amount[1] = line.balance - item.balance
                        else:
                            reconcile_ids.append(line.move_line_id.id)
            if split_id and split_brw:
                new_aml_id = self._split_account_move_line(
                    cr, uid, split_brw, split_amount, context)
                reconcile_ids.append(new_aml_id)
            new_rec_id = obj_arc.create(cr, uid, {
                'type': item.reconcile_id.type}, context)
            obj_aml = self.pool.get('account.move.line')
            obj_aml.write(cr, uid, reconcile_ids, {
                'reconcile_id': new_rec_id,
                'reconcile_partial_id': 0}, context=context)
            for inv_id in invoice_ids:
                if obj_inv.test_paid(cr, uid, [inv_id]):
                    obj_inv.confirm_paid(cr, uid, [inv_id])
        self.load_wizard_lines(cr, uid, ids, context)
        return {'name': _('Split reconcile wizard'),
                'type': 'ir.actions.act_window',
                'res_model': self._name,
                'view_type': 'form',
                'view_id': False,
                'view_mode': 'form',
                'nodestroy': True,
                'target': 'current',
                'domain': "",
                'context': {'default_reconcile_id': new_rec_id}}

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_split_reconcile()


##--------------------------------------------------- tcv_split_reconcile_lines


class tcv_split_reconcile_lines(osv.osv_memory):

    _name = 'tcv.split.reconcile.lines'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'line_id': fields.many2one(
            'tcv.split.reconcile.lines', 'String', required=True,
            ondelete='cascade'),
        'move_line_id': fields.many2one(
            'account.move.line', 'Accounting entrie line', ondelete='restrict',
            select=True, readonly=True),
        'date': fields.date(
            'Date', required=True, readonly=True),
        'name': fields.char(
            'Name', size=64, required=False, readonly=True),
        'ref': fields.char(
            'Reference', size=64, required=False, readonly=True),
        'invoice_id': fields.many2one(
            'account.invoice', 'Invoice', ondelete='restrict', readonly=True),
        'partner_id': fields.many2one(
            'res.partner', 'Partner', change_default=True,
            readonly=True, ondelete='restrict'),
        'move_id': fields.many2one(
            'account.move', 'Accounting entries', ondelete='restrict',
            help="The move of this entry line.", select=True, readonly=True),
        'debit': fields.float(
            'Debit', digits_compute=dp.get_precision('Account'),
            readonly=True),
        'credit': fields.float(
            'Credit', digits_compute=dp.get_precision('Account'),
            readonly=True),
        'balance': fields.float(
            'Balance', digits_compute=dp.get_precision('Account'),
            readonly=True),
        'select': fields.boolean(
            'Select', required=True),
        'split': fields.boolean(
            'Split', required=True),

        }

    _defaults = {
        'select': lambda *a: False,
        'split': lambda *a: False,
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_split_reconcile_lines()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
