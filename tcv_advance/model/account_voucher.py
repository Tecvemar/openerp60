# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date: 16/07/2012
#    Version: 0.0.0.0
#
#    Description: Incorpora el campo voucher_type para indicar si es un
#           asiento normal o de anticipo
#
##############################################################################
from datetime import datetime
from osv import fields,osv
from tools.translate import _
import pooler
import decimal_precision as dp
import time


class account_voucher(osv.osv):

    _inherit = 'account.voucher'


    _columns =  {
                'voucher_type':fields.selection([('normal', 'Normal'),('advance', 'Advance')], string='Voucher type', required=True, readonly=True, states={'draft':[('readonly',False)]}),
                }


    _defaults = {
                'voucher_type':lambda *a: 'normal'
                }


    def action_move_line_create_advance(self, cr, uid, ids, context=None):
        ## Replace original code to call advance's account
        ## Reemplaza el codigo original para llamar a las cuentas de anticipo
        ##    account_id = inv.partner_id.property_account_advance.id
        ##    account_id = inv.partner_id.property_account_prepaid.id
        def _get_payment_term_lines(term_id, amount):
            term_pool = self.pool.get('account.payment.term')
            if term_id and amount:
                terms = term_pool.compute(cr, uid, term_id, amount)
                return terms
            return False
        if context is None:
            context = {}
        move_pool = self.pool.get('account.move')
        move_line_pool = self.pool.get('account.move.line')
        currency_pool = self.pool.get('res.currency')
        tax_obj = self.pool.get('account.tax')
        seq_obj = self.pool.get('ir.sequence')
        for inv in self.browse(cr, uid, ids, context=context):
            if inv.move_id:
                continue
            context_multi_currency = context.copy()
            context_multi_currency.update({'date': inv.date})

            if inv.journal_id.sequence_id:
                name = seq_obj.get_id(cr, uid, inv.journal_id.sequence_id.id)
            if not name:
                raise osv.except_osv(_('Error !'), _('Please define a sequence on the journal and make sure it is activated !'))
            if not inv.reference:
                ref = name.replace('/','')
            else:
                ref = inv.reference

            move = {
                'name': name,
                'journal_id': inv.journal_id.id,
                'narration': inv.narration,
                'date': inv.date,
                'ref': ref,
                'period_id': inv.period_id and inv.period_id.id or False
            }
            move_id = move_pool.create(cr, uid, move)

            #create the first line manually
            company_currency = inv.journal_id.company_id.currency_id.id
            current_currency = inv.currency_id.id
            debit = 0.0
            credit = 0.0
            # TODO: is there any other alternative then the voucher type ??
            # -for sale, purchase we have but for the payment and receipt we do not have as based on the bank/cash journal we can not know its payment or receipt
            if inv.type in ('purchase', 'payment'):
                credit = currency_pool.compute(cr, uid, current_currency, company_currency, inv.amount, context=context_multi_currency)
            elif inv.type in ('sale', 'receipt'):
                debit = currency_pool.compute(cr, uid, current_currency, company_currency, inv.amount, context=context_multi_currency)
            if debit < 0:
                credit = -debit
                debit = 0.0
            if credit < 0:
                debit = -credit
                credit = 0.0
            sign = debit - credit < 0 and -1 or 1
            #create the first line of the voucher
            move_line = {
                'name': inv.name or '/',
                'debit': debit,
                'credit': credit,
                'account_id': inv.account_id.id,
                'move_id': move_id,
                'journal_id': inv.journal_id.id,
                'period_id': inv.period_id.id,
                'partner_id': inv.partner_id.id,
                'currency_id': company_currency <> current_currency and  current_currency or False,
                'amount_currency': company_currency <> current_currency and sign * inv.amount or 0.0,
                'date': inv.date,
                'date_maturity': inv.date_due
            }
            move_line_pool.create(cr, uid, move_line)
            rec_list_ids = []
            line_total = debit - credit
            if inv.type == 'sale':
                line_total = line_total - currency_pool.compute(cr, uid, inv.currency_id.id, company_currency, inv.tax_amount, context=context_multi_currency)
            elif inv.type == 'purchase':
                line_total = line_total + currency_pool.compute(cr, uid, inv.currency_id.id, company_currency, inv.tax_amount, context=context_multi_currency)

            for line in inv.line_ids:
                #create one move line per voucher line where amount is not 0.0
                if not line.amount:
                    continue
                #we check if the voucher line is fully paid or not and create a move line to balance the payment and initial invoice if needed
                if line.amount == line.amount_unreconciled:
                    amount = line.move_line_id.amount_residual #residual amount in company currency
                else:
                    amount = currency_pool.compute(cr, uid, current_currency, company_currency, line.untax_amount or line.amount, context=context_multi_currency)
                move_line = {
                    'journal_id': inv.journal_id.id,
                    'period_id': inv.period_id.id,
                    'name': line.name and line.name or '/',
                    'account_id': line.account_id.id,
                    'move_id': move_id,
                    'partner_id': inv.partner_id.id,
                    'currency_id': company_currency <> current_currency and current_currency or False,
                    'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
                    'quantity': 1,
                    'credit': 0.0,
                    'debit': 0.0,
                    'date': inv.date
                }
                if not amount:
                    raise osv.except_osv(_('Warning'),
                        _("Error while processing 'account.voucher %s' (id:%s) for partner '%s', amount: %s !") % (inv.name, inv.id, inv.partner_id.name, inv.amount))
                if amount < 0:
                    amount = -amount
                    if line.type == 'dr':
                        line.type = 'cr'
                    else:
                        line.type = 'dr'

                if (line.type=='dr'):
                    line_total += amount
                    move_line['debit'] = amount
                else:
                    line_total -= amount
                    move_line['credit'] = amount

                if inv.tax_id and inv.type in ('sale', 'purchase'):
                    move_line.update({
                        'account_tax_id': inv.tax_id.id,
                    })
                if move_line.get('account_tax_id', False):
                    tax_data = tax_obj.browse(cr, uid, [move_line['account_tax_id']], context=context)[0]
                    if not (tax_data.base_code_id and tax_data.tax_code_id):
                        raise osv.except_osv(_('No Account Base Code and Account Tax Code!'),_("You have to configure account base code and account tax code on the '%s' tax!") % (tax_data.name))
                sign = (move_line['debit'] - move_line['credit']) < 0 and -1 or 1
                move_line['amount_currency'] = company_currency <> current_currency and sign * line.amount or 0.0
                voucher_line = move_line_pool.create(cr, uid, move_line)
                if line.move_line_id.id:
                    rec_ids = [voucher_line, line.move_line_id.id]
                    rec_list_ids.append(rec_ids)

            inv_currency_id = inv.currency_id or inv.journal_id.currency or inv.journal_id.company_id.currency_id
            if not currency_pool.is_zero(cr, uid, inv_currency_id, line_total):
                diff = line_total
                account_id = False
                if inv.payment_option == 'with_writeoff':
                    account_id = inv.writeoff_acc_id.id
                elif inv.type in ('sale', 'receipt'):
                    account_id = inv.partner_id.property_account_advance.id
                else:
                    account_id = inv.partner_id.property_account_prepaid.id
                if not account_id:
                    raise osv.except_osv(_('Warning'),
                        _("Error while processing 'account.voucher %s' (id:%s) for partner '%s', amount: %s !\nShould indicate an advance account for the partner") % (inv.name, inv.id, inv.partner_id.name, inv.amount))
                move_line = {
                    'name': name,
                    'account_id': account_id,
                    'move_id': move_id,
                    'partner_id': inv.partner_id.id,
                    'date': inv.date,
                    'credit': diff > 0 and diff or 0.0,
                    'debit': diff < 0 and -diff or 0.0,
                    #'amount_currency': company_currency <> current_currency and currency_pool.compute(cr, uid, company_currency, current_currency, diff * -1, context=context_multi_currency) or 0.0,
                    #'currency_id': company_currency <> current_currency and current_currency or False,
                }
                move_line_pool.create(cr, uid, move_line)
            self.write(cr, uid, [inv.id], {
                'move_id': move_id,
                'state': 'posted',
                'number': name,
            })
            move_pool.post(cr, uid, [move_id], context={})
            for rec_ids in rec_list_ids:
                if len(rec_ids) >= 2:
                    move_line_pool.reconcile_partial(cr, uid, rec_ids)
        return True

    def action_move_line_create(self, cr, uid, ids, context=None):
        for vou in self.browse(cr, uid, ids, context=context):
            if vou.voucher_type == 'advance':
                if vou.line_ids or vou.line_dr_ids or vou.line_cr_ids:
                    raise osv.except_osv(_('Warning'),
                        _("Advance voucher's can't have any lines"))

                self.action_move_line_create_advance(cr, uid, [vou.id], context)
            else:
                super(account_voucher, self).action_move_line_create(cr, uid, [vou.id], context)
        return True

    def onchange_voucher_type(self, cr, uid, ids, voucher_type, line_dr_ids, line_cr_ids, context=None):
        if voucher_type != 'normal':
            ## no referenced lines for advance
            return {'value':{'line_ids':[], 'line_dr_ids':[], 'line_cr_ids':[]}}
        else:
            return {}


    def cancel_voucher(self, cr, uid, ids, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        obj_adv = self.pool.get('tcv.voucher.advance')
        for vou in self.browse(cr,uid,ids):
            if vou.voucher_type == 'advance':
                for line in vou.move_ids:
                    adv_ids = obj_adv.search(cr, uid, [('move_line', '=', line.id)])
                    if adv_ids:
                        adv = obj_adv.browse(cr,uid,adv_ids,context=context)[0]
                        raise osv.except_osv(_('Error!'),_('Can\'t unreconcile voucher ' \
                              'while is used in advance:\nReference: %s\nDescription: %s\nAdvance move: %s\nDate: %s' % \
                              (adv.ref,
                               adv.name,
                               adv.move_line.name,
                               adv.date)))
        return super(account_voucher, self).cancel_voucher(cr, uid, ids, context)

account_voucher()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
