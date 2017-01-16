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

##--------------------------------------------------------- tcv_partner_balance


class tcv_partner_balance(osv.osv_memory):

    _name = 'tcv.partner.balance'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def default_get(self, cr, uid, fields, context=None):
        data = super(tcv_partner_balance, self).\
            default_get(cr, uid, fields, context)
        return data

    def _get_account_balance(self, cr, uid, item, context=None):
        if item.invoice_type == 'in_invoice,in_refund':  # Supplier
            acc_id = item.partner_id.property_account_payable.id
            sign = -1
        else:
            acc_id = item.partner_id.property_account_receivable.id
            sign = 1
        obj_tbl = self.pool.get('tcv.trial.balance')
        data = {
            'date_from': item.date,
            'date_to': item.date,
            'acc_from_id': acc_id,
            'acc_to_id': acc_id,
            }
        tbl_id = obj_tbl.create(cr, uid, data, context)
        obj_tbl.load_wizard_lines(cr, uid, tbl_id, context)
        tbl_brw = obj_tbl.browse(cr, uid, tbl_id, context)
        return tbl_brw.balance * sign, acc_id

    def _load_invoices(self, cr, uid, item, context=None):
        obj_inv = self.pool.get('account.invoice')
        inv_ids = obj_inv.search(
            cr, uid, [('partner_id', '=', item.partner_id.id),
                      ('date_invoice', '<=', item.date),
                      ('type', 'in', item.invoice_type.split(',')),
                      ('state', 'in', ('open', 'paid')),  # Valid invoices
                      ('company_id', '=', item.company_id.id),
                      ])
        invoice_ids = []
        invoices_amount = 0
        for inv in obj_inv.browse(cr, uid, inv_ids, context=context):
            detail = {
                'payments': {'journals': [20, 22, 23, 25, 27, 29, 30, 32,
                                          33, 36, 37, 38, 41, 275, 11, 14,
                                          12, 43, 44, 282], 'amount': 0},
                'advances': {'journals': [9, 10], 'amount': 0},
                'wh_iva': {'journals': [2, 3], 'amount': 0},
                'wh_islr': {'journals': [4, 5], 'amount': 0},
                'amount_other': {'journals': [], 'amount': 0},
                }
            tot_detail = 0
            amount_total = inv.amount_total if 'invoice' in inv.type \
                else -inv.amount_total
            sign = 1 if item.invoice_type == 'out_invoice,out_refund' \
                else -1
            reconcile_id = 0
            for pay in inv.payment_ids:
                #~ Only payments with date <= report's date
                if not reconcile_id:
                    reconcile_id = pay.reconcile_id and pay.reconcile_id.id \
                        or pay.reconcile_partial_id and \
                        pay.reconcile_partial_id.id
                if pay.date <= item.date:
                    other = True
                    amount = (pay.debit - pay.credit) * sign
                    for key in detail:
                        if pay.journal_id.id in detail[key]['journals']:
                            other = False
                            detail[key]['amount'] += amount
                    if other:
                        detail['amount_other']['amount'] += amount
                    tot_detail += amount
            residual = round(amount_total + tot_detail, 2)
            invoices_amount += residual
            data = {
                'invoice_id': inv.id,
                'reconcile_id': reconcile_id,
                'amount_total': amount_total,
                'payments': detail['payments']['amount'],
                'advances': detail['advances']['amount'],
                'wh_iva': detail['wh_iva']['amount'],
                'wh_islr': detail['wh_islr']['amount'],
                'amount_other': detail['amount_other']['amount'],
                'residual': residual,
                }
            if (item.invoice_state == 'open,paid') or \
                    (residual and item.invoice_state == 'open') or \
                    (not residual and item.invoice_state == 'paid'):
                invoice_ids.append((0, 0, data))
        return invoice_ids, invoices_amount

    def _load_advances(self, cr, uid, item, context=None):
        advance_ids = []
        advances_amount = 0
        if item.invoice_type == 'in_invoice,in_refund':  # Supplier
            acc_id = item.partner_id.property_account_prepaid.id
            field_amout, field_used = 'debit', 'credit'
        else:
            acc_id = item.partner_id.property_account_advance.id
            field_amout, field_used = 'credit', 'debit'
        obj_aml = self.pool.get('account.move.line')
        aml_ids = obj_aml.search(
            cr, uid, [('account_id', '=', acc_id),
                      ('date', '<=', item.date),
                      ('state', '=', 'valid'),  # Valid moves
                      ('partner_id', '=', item.partner_id.id),
                      (field_amout, '>', 0)
                      ])
        for aml in obj_aml.browse(cr, uid, aml_ids, context=context):
            data = {'acc_move_id': aml.id,
                    'amount_total': aml[field_amout],
                    'amount_used': 0,
                    'amount_other': 0,
                    }
            if aml.reconcile_id and aml.reconcile_id.line_id:
                for m in aml.reconcile_id.line_id:
                    if m[field_used] and m.date <= item.date:
                        data['amount_used'] -= m[field_used]
                    elif m[field_amout] and m.date <= item.date and \
                            m.id != aml.id:
                        data['amount_other'] += m[field_amout]
            elif aml.reconcile_partial_id and \
                    aml.reconcile_partial_id.line_partial_ids:
                for m in aml.reconcile_partial_id.line_partial_ids:
                    if m[field_used] and m.date <= item.date:
                        data['amount_used'] -= m[field_used]
                    elif m[field_amout] and m.date <= item.date and \
                            m.id != aml.id:
                        data['amount_other'] += m[field_amout]
            data['residual'] = round(
                data['amount_total'] + data['amount_used'] +
                data['amount_other'], 2)
            if data['residual']:
                advances_amount += data['residual']
                advance_ids.append((0, 0, data))
        return advance_ids, advances_amount

    ##--------------------------------------------------------- function fields

    _columns = {
        'partner_id': fields.many2one(
            'res.partner', 'Partner', readonly=False, required=True,
            ondelete='restrict'),
        'account_id': fields.many2one(
            'account.account', 'Account', required=False, ondelete='restrict',
            readonly=True),
        'date': fields.date(
            'Date', required=True),
        'invoice_type': fields.selection(
            [('in_invoice,in_refund', 'Supplier'),
             ('out_invoice,out_refund', 'Customer')],
            string='Invoice type', required=True, readonly=False),
        'invoice_state': fields.selection(
            [('open', 'Open'),
             ('paid', 'Paid'),
             ('open,paid', 'All'),
             ],
            string='Invoice state', required=True, readonly=False),
        'loaded': fields.boolean(
            'Loaded'),
        'invoice_ids': fields.one2many(
            'tcv.partner.balance.invoices', 'line_id', 'Invoices',
            readonly=True),
        'advance_ids': fields.one2many(
            'tcv.partner.balance.advances', 'line_id', 'Advances',
            readonly=True),
        'company_id': fields.many2one(
            'res.company', 'Company', required=True, readonly=True,
            ondelete='restrict'),
        'invoices_amount': fields.float(
            'Invoices amount', digits_compute=dp.get_precision('Account')),
        'advances_amount': fields.float(
            'Advances amount', digits_compute=dp.get_precision('Account')),
        'account_balance': fields.float(
            'Account Balance', digits_compute=dp.get_precision('Account'),
            help="Accounting balance"),
        'account_diff': fields.float(
            'Difference', digits_compute=dp.get_precision('Account'),
            help="Difference between accounting and partner balance "),
        'partner_amount': fields.float(
            'Partner amount', digits_compute=dp.get_precision('Account')),
        }

    _defaults = {
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company').
        _company_default_get(cr, uid, self._name, context=c),
        'invoice_state': lambda *a: 'open',
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    def clear_wizard_lines(self, cr, uid, item, context):
        #~ Invoices
        unlink_ids = []
        for l in item.invoice_ids:
            unlink_ids.append(l.id)
        if unlink_ids:
            obj_lin = self.pool.get('tcv.partner.balance.invoices')
            obj_lin.unlink(cr, uid, unlink_ids, context=context)
        #~ Advances
        unlink_ids = []
        for l in item.advance_ids:
            unlink_ids.append(l.id)
        if unlink_ids:
            obj_lin = self.pool.get('tcv.partner.balance.advances')
            obj_lin.unlink(cr, uid, unlink_ids, context=context)
        return unlink_ids

    def load_wizard_lines(self, cr, uid, ids, context):
        context = context or {}
        ids = isinstance(ids, (int, long)) and [ids] or ids
        for item in self.browse(cr, uid, ids, context={}):
            self.clear_wizard_lines(cr, uid, item, context)
            invoice_ids, invoices_amount = self._load_invoices(
                cr, uid, item, context)
            advance_ids, advances_amount = self._load_advances(
                cr, uid, item, context)
            account_balance, account_id = self._get_account_balance(
                cr, uid, item, context)
            self.write(
                cr, uid, [item.id], {
                    'account_id': account_id,
                    'invoice_ids': invoice_ids,
                    'advance_ids': advance_ids,
                    'invoices_amount': invoices_amount,
                    'advances_amount': advances_amount,
                    'partner_amount': invoices_amount - advances_amount,
                    'account_balance': account_balance,
                    'account_diff': invoices_amount - account_balance,
                    'loaded': True},
                context=context)
        return True

    ##-------------------------------------------------------- buttons (object)

    def button_liquidity(self, cr, uid, ids, context=None):
        item = self.browse(cr, uid, ids[0], context={})
        if not item.account_id:
            return {}
        fch_date = time.strptime(item.date, '%Y-%m-%d')
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
                    'default_date_from': '%s-01-01' % fch_date.tm_year,
                    'default_date_to': item.date,
                    'do_autoload': True,
                    }}

    ##------------------------------------------------------------ on_change...

    def on_change_partner_id(self, cr, uid, ids, partner_id):
        res = {}
        res.update({'loaded': False})
        return {'value': res}

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_partner_balance()


##------------------------------------------------ tcv_partner_balance_invoices


class tcv_partner_balance_invoices(osv.osv_memory):

    _name = 'tcv.partner.balance.invoices'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    def _compute_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for item in self.browse(cr, uid, ids, context=context):
            i_date = item.invoice_id.date_due or item.invoice_id.date_document
            d_date = item.line_id.date
            if i_date and d_date:
                a = datetime.strptime(i_date, '%Y-%m-%d')
                b = datetime.strptime(d_date, '%Y-%m-%d')
                delta = b - a
            else:
                delta = False
            res[item.id] = {
                'days_due': delta and delta.days or 0,
                'doc_type': _('Inv') if 'invoice' in item.type
                else _('N/C'),
                'number': item.invoice_id.supplier_invoice_number or
                item.invoice_id.number,
                }
        return res

    ##-------------------------------------------------------------------------

    _columns = {
        'line_id': fields.many2one(
            'tcv.partner.balance', 'String', required=True,
            ondelete='cascade'),
        'days_due': fields.function(
            _compute_all, method=True, type='int',
            string='Days due', multi='all'),
        'invoice_id': fields.many2one(
            'account.invoice', 'Invoice Reference', ondelete='restrict',
            select=True),
        'type': fields.related(
            'invoice_id', 'type', type='char', size=16, store=False),
        'reconcile_id': fields.many2one(
            'account.move.reconcile', 'Reconcile', readonly=True,
            ondelete='set null', select=2),
        'doc_type': fields.function(
            _compute_all, method=True, type='char', size=16,
            string='Doc. type', multi='all'),
        'number': fields.function(
            _compute_all, method=True, type='char', size=24,
            string='Number', multi='all'),
        'date_invoice': fields.related(
            'invoice_id', 'date_invoice', type='date', store=False,
            string="Date"),
        'name': fields.related(
            'invoice_id', 'name', type='char', size=64, store=False,
            string='Description'),
        'amount_total': fields.float(
            'Amount', digits_compute=dp.get_precision('Account')),
        'payments': fields.float(
            'Payments', digits_compute=dp.get_precision('Account')),
        'advances': fields.float(
            'Advances', digits_compute=dp.get_precision('Account')),
        'wh_iva': fields.float(
            'IVA', digits_compute=dp.get_precision('Account')),
        'wh_islr': fields.float(
            'ISLR', digits_compute=dp.get_precision('Account')),
        'amount_other': fields.float(
            'Other', digits_compute=dp.get_precision('Account')),
        'residual': fields.float(
            'Residual', digits_compute=dp.get_precision('Account')),
        'payment_ids': fields.related(
            'invoice_id', 'payment_ids', type='many2many',
            relation='account.move.line', string='Payments',
            store=False, readonly=True),

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

tcv_partner_balance_invoices()


##------------------------------------------------ tcv_partner_balance_advances


class tcv_partner_balance_advances(osv.osv_memory):

    _name = 'tcv.partner.balance.advances'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    ##-------------------------------------------------------------------------

    _columns = {
        'line_id': fields.many2one(
            'tcv.partner.balance', 'String',
            required=True, ondelete='cascade'),
        'acc_move_id': fields.many2one(
            'account.move.line', 'Move line', ondelete='restrict',
            help="The move line of this entry line.", select=True,
            readonly=True),
        'date': fields.related(
            'acc_move_id', 'date', type='date', store=False,
            string="Date"),
        'name': fields.related(
            'acc_move_id', 'name', type='char', size=64,
            store=False, string='Descriptrion'),
        'ref': fields.related(
            'acc_move_id', 'ref', type='char', size=64,
            store=False, string='Descriptrion'),
        'amount_total': fields.float(
            'Amount', digits_compute=dp.get_precision('Account')),
        'amount_used': fields.float(
            'Used', digits_compute=dp.get_precision('Account')),
        'amount_other': fields.float(
            'Other', digits_compute=dp.get_precision('Account')),
        'residual': fields.float(
            'Residual', digits_compute=dp.get_precision('Account')),
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

tcv_partner_balance_advances()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
