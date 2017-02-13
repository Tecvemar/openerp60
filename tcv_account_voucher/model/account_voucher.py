# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2014-02-04
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
#~ import decimal_precision as dp
#~ import time
#~ import netsvc

##------------------------------------------------------------- account_voucher


class account_voucher(osv.osv):

    _inherit = 'account.voucher'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def _check_is_not_duplicated(self, cr, uid, ids, context=None):
        '''
        Check if the account voucher is duplicates
        fields to be compared:
            type
            partner_id
            amount
            journal_id
            reference
            payment_doc
            id (to avoid "self.id" error)
        returns True if not duplicated
        '''
        res = True
        for item in self.browse(cr, uid, ids, context=context):
            if item.payment_doc != 'cash':
                # Don't check payment_doc if dosen't exists
                chk_doc = '' if item.payment_doc else '--'
                sql = '''
                         select id from account_voucher
                         where type = '%s' and partner_id = %s and
                               amount = %s and journal_id = %s and
                               reference = '%s' and
                               %s payment_doc = '%s' and
                               id != %s
                      ''' % (item.type, item.partner_id.id,
                             item.amount, item.journal_id.id,
                             item.reference,
                             chk_doc, item.payment_doc,
                             item.id)
                cr.execute(sql)
                data = cr.fetchall()
                res = len(data) == 0  # 0 = no others vouchers
        return res

    ##--------------------------------------------------------- function fields

    _columns = {
        'voucher_type': fields.selection([('normal', 'Normal'),
                                          ('advance', 'Advance'),
                                          ('other', 'Other')],
                                         string='Voucher type',
                                         required=True, readonly=True,
                                         states={'draft':
                                                 [('readonly', False)]}),
        'voucher_account_id': fields.many2one(
            'account.account', 'Account', required=False,
            readonly=True, states={'draft': [('readonly', False)]},
            ondelete='restrict'),
        }

    _defaults = {
        }

    _sql_constraints = [
        ]

    _constraints = [
        (_check_is_not_duplicated,
         'Error ! This voucher is already registered.',
         ['partner_id', 'amount', 'journal_id', 'reference', 'payment_doc'])
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    def action_move_line_create_other(self, cr, uid, ids, context=None):
        ## Replace original code to call advance's account
        ## Reemplaza el codigo original para llamar a las cuentas de anticipo
        ##    account_id = inv.partner_id.property_account_advance.id
        ##    account_id = inv.partner_id.property_account_prepaid.id
        context = context or {}
        ids = isinstance(ids, (int, long)) and [ids] or ids
        obj_move = self.pool.get('account.move')
        currency_pool = self.pool.get('res.currency')
        seq_obj = self.pool.get('ir.sequence')
        for item in self.browse(cr, uid, ids, context=context):
            if item.move_id:
                continue
            context_multi_currency = context.copy()
            context_multi_currency.update({'date': item.date})

            if item.journal_id.sequence_id:
                name = seq_obj.get_id(cr, uid, item.journal_id.sequence_id.id)
            if not name:
                raise osv.except_osv(
                    _('Error !'),
                    _('Please define a sequence on the journal and make ' +
                        'sure it is activated !'))
            if not item.reference:
                ref = name.replace('/', '')
            else:
                ref = item.reference

            move = {
                'name': name,
                'journal_id': item.journal_id.id,
                'narration': item.narration,
                'date': item.date,
                'ref': ref,
                'period_id': item.period_id and item.period_id.id or False
            }
            company_currency = item.journal_id.company_id.currency_id.id
            current_currency = item.currency_id.id
            debit = credit = 0.0
            if item.type in ('purchase', 'payment'):
                credit = currency_pool.compute(cr, uid, current_currency,
                                               company_currency, item.amount,
                                               context=context_multi_currency)
            elif item.type in ('sale', 'receipt'):
                debit = currency_pool.compute(cr, uid, current_currency,
                                              company_currency, item.amount,
                                              context=context_multi_currency)
            if debit < 0:
                credit = -debit
            if credit < 0:
                debit = -credit
            sign = debit - credit < 0 and -1 or 1
            #create the first line of the voucher

            line1 = {
                'name': item.name or '/',
                'debit': debit,
                'credit': credit,
                'account_id': item.account_id.id,
                'journal_id': item.journal_id.id,
                'period_id': item.period_id.id,
                'partner_id': item.partner_id.id,
                'currency_id': company_currency != current_currency and
                current_currency or False,
                'amount_currency': company_currency != current_currency and
                sign * item.amount or 0.0,
                'date': item.date,
                'date_maturity': item.date_due
            }
            line2 = {}
            line2.update(line1)
            line2.update({'account_id': item.voucher_account_id.id,
                          'debit': credit,
                          'credit': debit,
                          })
            if debit > 0:
                move_lines = [(0, 0, line2),
                              (0, 0, line1)]
            else:
                move_lines = [(0, 0, line1),
                              (0, 0, line2)]
            move.update({'line_id': move_lines})
            move_id = obj_move.create(cr, uid, move, context)
            if move_id:
                obj_move.post(cr, uid, [move_id], context=context)
                self.write(cr, uid, [item.id],
                           {'move_id': move_id,
                            'state': 'posted',
                            'number': name,
                            })
        return True

    def action_move_line_create(self, cr, uid, ids, context=None):
        for vou in self.browse(cr, uid, ids, context=context):
            if vou.voucher_type == 'other':
                if vou.line_ids or vou.line_dr_ids or vou.line_cr_ids:
                    raise osv.except_osv(_('Warning'),
                        _("Other voucher's can't have any lines"))

                self.action_move_line_create_other(cr, uid, [vou.id], context)
            else:
                super(account_voucher, self).action_move_line_create(cr, uid, [vou.id], context)
        return True

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

account_voucher()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
