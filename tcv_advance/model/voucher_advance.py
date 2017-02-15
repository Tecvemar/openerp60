# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date: 16/07/2012
#    Version: 0.0.0.0
#
#    Description: This module handle customers & suppliers advances
#
##############################################################################
from datetime import datetime
from osv import fields,osv
from tools.translate import _
import pooler
import decimal_precision as dp
import time

class tcv_voucher_advance(osv.osv):

    _name = 'tcv.voucher.advance'

    _description = 'Used to reconcile advances with payments (by partner)'

    def default_get(self, cr, uid, fields, context=None):
        data = super(tcv_voucher_advance, self).default_get(
            cr, uid, fields, context)
        return data


    def _get_partner_accounts(self, cr, uid, partner, a_type, context=None):
        res = 0
        if type(partner) == list and len(partner) == 1:
            partner = partner[0]
        if type(partner) == int:
            ## convertir id en objeto
            partner = self.pool.get('res.partner').browse(cr,uid,partner)
        if a_type == 'advance':
            acc_advance = partner.property_account_advance.id
            acc_partner = partner.property_account_receivable.id
        else:
            acc_advance = partner.property_account_prepaid.id
            acc_partner = partner.property_account_payable.id
        return {'advance_account':acc_advance,
                'partner_account':acc_partner}


    def _get_partner_account_all(self, cr, uid, ids, field_name, args, context=None):
        if not ids:
            return {}
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            if line.partner_id:
                res[line.id] = self._get_partner_accounts(cr,uid,line.partner_id,line.type)[field_name]
            else:
                res[line.id] = 0
        return res


    def _amount_move_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for adv in self.browse(cr, uid, ids, context=context):
            if adv.state != 'draft':
                values = {
                    'amount': adv.amount,
                    'amount_residual': adv.amount_residual,
                    'amount_applied':adv.amount_applied,
                    'amount_dif':adv.amount_dif,
                    }
                res[adv.id] = values[field_name]
            else:
                if adv.type=='advance':
                    amount = adv.move_line.credit
                else:
                    amount = adv.move_line.debit
                values = {
                    'amount': amount,
                    'amount_residual': abs(adv.move_line.amount_residual),
                    'amount_applied':0.0,
                    'amount_dif':0.0,
                    }
                for line in adv.line_ids:
                    values['amount_applied'] += line.amount_to_apply
                values.update({'amount_dif':values['amount_residual']-values['amount_applied']})
                if abs(values['amount_dif']) < 0.0001:
                        values['amount_dif'] = 0.0
                if field_name:
                    res[adv.id] = values[field_name]
        return res

    _order = 'ref desc'

    _columns = {
        'ref': fields.char('Reference', size=16, required=False, readonly=True, states={'draft':[('readonly',False)]}), # Secuence
        'date': fields.date('Date', required=True, readonly=True, states={'draft':[('readonly',False)]}, select=True),
        'partner_id': fields.many2one('res.partner', 'Partner', readonly=True, required=True, states={'draft':[('readonly',False)]}, ondelete='restrict'),
        'advance_account':fields.function(_get_partner_account_all, method=True, type='many2one', string='Advance account', relation='account.account'),
        'partner_account':fields.function(_get_partner_account_all, method=True, type='many2one', string='Partner account', relation='account.account'),
        'move_line':fields.many2one('account.move.line', 'Advance move', required=True, readonly=True, states={'draft':[('readonly',False)]}, ondelete='restrict'),
        'amount':fields.function(_amount_move_all, method=True, type='float', string='Amount', digits_compute=dp.get_precision('Account'), store=True),
        'amount_residual':fields.function(_amount_move_all, method=True, type='float', string='Residual', digits_compute=dp.get_precision('Account'), store=True),
        'amount_applied':fields.function(_amount_move_all, method=True, type='float', string='Applied', digits_compute=dp.get_precision('Account'), store=True),
        'amount_dif':fields.function(_amount_move_all, method=True, type='float', string='To be applied', digits_compute=dp.get_precision('Account'), store=True),
        'name': fields.char('Description', size=64, required=False, readonly=False),
        'company_id': fields.many2one('res.company','Company', required=True, readonly=True, states={'draft':[('readonly',False)]}, ondelete='restrict'),
        'currency_id': fields.many2one('res.currency', 'Currency', required=True, readonly=True, states={'draft':[('readonly',False)]}, ondelete='restrict'),
        'type':fields.selection([('advance','Customer Advance'),('prepaid','Supplier prepaid')],'Type', required=True),
        'line_ids':fields.one2many('tcv.voucher.advance.line','line_id','Invoices',ondelete='cascade'),
        'move_id': fields.many2one('account.move', 'Account move', help="The move of this entry line.", select=2, readonly=True, ondelete='restrict'),
        'state': fields.selection([('draft', 'Draft'),('posted', 'Posted'),('cancel', 'Cancelled')], string='State', required=True, readonly=True),
        'journal_id':fields.many2one('account.journal', 'Journal', required=True, select=True, readonly=True, states={'draft':[('readonly',False)]}, ondelete='restrict'),
        }


    _defaults = {
        'ref': lambda *a: '/',
        'name': lambda *a: '',
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        'company_id':lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr,uid,'tcv.voucher.advance',context=c),
        'currency_id': lambda self,cr,uid,c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.currency_id.id,
        'type': lambda self,cr,uid,c: c.get('advance_type'),
        'state': 'draft',
        }


    def onchange_partner_id(self,cr,uid,ids,partner_id,type,lines):
        res = {}
        if partner_id:
            line_obj = self.pool.get('tcv.voucher.advance.line')
            ## clear actual lines
            unlink_ids = []
            for l in lines:
                unlink_ids.append(l[1]) # l is a tuple (1,ID,{DATA DICT})
            if unlink_ids:
                line_obj.unlink(cr,uid,unlink_ids,context=None)
            ##Update lines data
            partner_acc = self._get_partner_accounts(cr,uid,partner_id,type)
            partner_acc.update({'move_line':[],'amount':0,'amount_residual':0})
            inv = line_obj._load_partner_invoice_moves(cr,uid,ids,partner_id,partner_acc['partner_account'],type)
            partner_acc.update(inv)
            res.update({'value':partner_acc})
        return res


    def onchange_move_line(self,cr,uid,ids,move_line,type):
        res = {}
        if move_line:
            move = self.pool.get('account.move.line').browse(cr,uid,move_line,context=None)
            if type=='advance':
                amount = move.credit
            else:
                amount = move.debit
            res.update({'value':{'amount':amount,'amount_residual':abs(move.amount_residual)}})
        return res

    def unlink(self, cr, uid, ids, context=None):
        so_brw = self.browse(cr,uid,ids,context={})
        unlink_ids = []
        for adv in so_brw:
            if adv.state in ('draft','cancel'):
                unlink_ids.append(adv.id)
            else:
                raise osv.except_osv(_('Invalid action !'), _('Cannot delete advances that are already posted!'))
        return super(tcv_voucher_advance, self).unlink(cr, uid, unlink_ids, context)


    def button_calculate_click(self,cr,uid,ids,context=None):
        res = self._amount_move_all(cr, uid, ids, None, None, context)
        return True


    def _gen_account_move_line(self, company_id, partner_id, account_id, name, debit, credit):
        return (0,0,{
                'auto' : True,
                'company_id': company_id,
                'partner_id': partner_id,
                'account_id': account_id,
                'name': name,
                'debit': debit,
                'credit': credit,
                'reconcile':False,
                })


    def do_reconcile(self, cr, uid, advance, move_id, context):
        context = context or {}
        obj_move = self.pool.get('account.move')
        move = obj_move.browse(cr, uid, move_id, context)
        # Post (Approve) account.move
        if move.state == 'draft':
            obj_move.post(cr, uid, [move_id], context=context)
        obj_move_line = self.pool.get('account.move.line')
        rec_ids = []
        adv_lines = [{'ids':[advance.move_line.id],
                      'name':advance.move_line.name,
                      'amount':advance.move_line.debit+advance.move_line.credit,
                      'advance_id':-1,
                      'reconcile_id':advance.move_line.reconcile_id.id or advance.move_line.reconcile_partial_id.id,
                      'acc_id':advance.move_line.account_id.id}]
        for line in advance.line_ids:
            if line.amount_to_apply:
                adv_lines.append({'ids':[line.invoice_move_line2.id],
                                  'name':line.invoice_move_line2.name,
                                  'amount':line.invoice_move_line2.debit+line.invoice_move_line2.credit,
                                  'advance_id':line.id,
                                  'reconcile_id':line.invoice_move_line2.reconcile_id.id or line.invoice_move_line2.reconcile_partial_id.id,
                                  'acc_id':line.invoice_move_line2.account_id.id})
        for line in move.line_id:
            for item in adv_lines:
                if item['acc_id'] == line.account_id.id:
                    item['ids'].append(line.id)
                    item['amount'] -= line.debit+line.credit
        for item in adv_lines:
            if abs(item['amount']) < 0.0001:
                obj_move_line.reconcile(
                    cr, uid, item['ids'], context=context)
            else:
                obj_move_line.reconcile_partial(
                    cr, uid, item['ids'], context=context)
        return True


    def _gen_account_move(self, cr, uid, ids, context=None):
        context = context or {}
        so_brw = self.browse(cr,uid,ids,context={})
        obj_move = self.pool.get('account.move')
        obj_lines = self.pool.get('account.move.line')
        obj_per = self.pool.get('account.period')
        move_id=None
        for adv in so_brw:
            ref = context.get('advance_reference','Ant')
            period_id = obj_per.find(cr, uid, adv.date)[0]
            move={
                'ref':'%s [%s]'%(_('Adv'),ref),
                'journal_id':adv.journal_id.id,
                'date':adv.date,
                'company_id':adv.company_id.id,
                'state':'draft',
                'to_check':False,
                'narration':adv.name,
                'period_id':period_id
                }
            lines = []
            unlink_ids = []
            amount_residual = 0.0
            for line in adv.line_ids: # move line for advosit lines
                if line.amount_to_apply == 0:
                    unlink_ids.append(line.id)
                else:
                    # last chance amount_residual validation
                    valid = obj_lines.browse(cr,uid,line.invoice_move_line2.id,context=context)
                    if abs(valid.amount_residual) < line.amount_to_apply and abs(abs(valid.amount_residual) - line.amount_to_apply) > 0.0001:
                        raise osv.except_osv(_('Error!'),_('You can not apply an amount > move residual, invoice: %s.\nYou need to refresh data.')%(line.invoice_move_line2.name))
                    debit, credit = 0, 0
                    amount_residual = abs(line.invoice_move_line2.amount_residual) if adv.type == 'advance' else -abs(line.invoice_move_line2.amount_residual)
                    if amount_residual < 0:
                        debit = line.amount_to_apply
                    else:
                        credit = line.amount_to_apply

                    lines.append(self._gen_account_move_line(adv.company_id.id,
                                                             adv.partner_id.id,
                                                             line.invoice_move_line2.account_id.id,
                                                             '%s - %s'%(ref,line.invoice_move_line2.name),
                                                             debit,
                                                             credit))
            if unlink_ids:
                self.pool.get('tcv.voucher.advance.line').unlink(cr,uid,unlink_ids,context)
            # move line for advance
            debit = credit = 0.0
            if amount_residual > 0:
                debit = adv.amount_applied
            else:
                credit = adv.amount_applied
            valid = obj_lines.browse(cr,uid,adv.move_line.id,context=context)
            if abs(valid.amount_residual) < adv.amount_applied and abs(abs(valid.amount_residual) - adv.amount_applied) > 0.0001:
                raise osv.except_osv(_('Error!'),_('You can not apply an amount > move residual, advance: %s.\nYou need to refresh data.')%(adv.move_line.name))
            lines.append(self._gen_account_move_line(adv.company_id.id,
                                                     adv.partner_id.id,
                                                     adv.move_line.account_id.id,
                                                     '%s - %s'%(ref,adv.move_line.name),
                                                     debit,
                                                     credit))
            move.update({'line_id':lines})
            move_id = obj_move.create(cr, uid, move, context)
            self.do_reconcile(cr, uid, adv, move_id, context)
        return move_id


    ## Workflow -----------------------------------------------------------------------------------------------------------


    def test_post(self, cr, uid, ids, *args):
        so_brw = self.browse(cr,uid,ids,context={})
        for adv in so_brw:
            if not adv.amount_applied:
                raise osv.except_osv(_('No valid amount!'), _('The applied amount must be > 0'))
            if adv.amount_applied > adv.amount_residual:
                raise osv.except_osv(_('No valid amount!'), _('The amount to be aplied must be <= residual amount'))
        return True


    def button_post(self, cr, uid, ids, context=None):
        context = context or {}
        if len(ids) != 1:
            raise osv.except_osv(_('Error!'), _('Multiplies validations not allowed.'))
        for adv in self.browse(cr, uid, ids, context=context):
            if adv.ref != '/':
                ref = adv.ref
            else:
                ref = self.pool.get('ir.sequence').get(
                    cr, uid, 'voucher.advance')
            context.update({'advance_reference': ref, 'advance_type': adv.type})
            vals = {'state': 'posted',
                    'ref': ref,
                    'move_id': self._gen_account_move(cr, uid, ids, context)}
            return self.write(cr, uid, ids, vals, context)



    def test_cancel(self, cr, uid, ids, *args):
        so_brw = self.browse(cr,uid,ids,context={})
        for adv in so_brw:
            if adv.move_id.id:
                move=self.pool.get('account.move').browse(cr, uid, adv.move_id.id, context=None)
                if move.state=='posted':
                    raise osv.except_osv(_('Error!'),_('You can not cancel a advance while the account move is posted.'))
        return True


    def button_cancel(self, cr, uid, ids, context=None):
        if context == None:
            context = {}
        so_brw = self.browse(cr,uid,ids,context={})
        obj_lines = self.pool.get('account.move.line')
        obj_adv = self.pool.get('tcv.voucher.advance')
        res = {}
        for adv in so_brw:
            if adv.state == 'posted':
                if adv.move_id.id:
                    obj_move = self.pool.get('account.move')
                    move = obj_move.browse(cr, uid, adv.move_id.id, context=None)
                    if move.state=='draft':
                        recon_ids = []
                        for line in move.line_id:
                            if line.reconcile_id.id:
                                recon_ids.append(line.id)
                            elif line.reconcile_partial_id.id:
                                recon_ids.append(line.id)
                        if recon_ids:
                            # unreconcile advance, need account_smart_unreconcile to work
                            obj_lines._remove_move_reconcile(cr, uid, recon_ids, context=None)
                        vals={'state':'cancel','move_id':0}
                        res = obj_adv.write(cr,uid,ids,vals,context)
                        obj_move.unlink(cr, uid, [move.id])
            elif adv.state == 'draft':
                obj=self.pool.get('tcv.voucher.advance')
                vals={'state':'cancel','move_id':0}
                res = obj.write(cr,uid,ids,vals,context)
        return res


    def button_draft(self, cr, uid, ids, context=None):
        res = {}
        so_brw = self.browse(cr,uid,ids,context={})
        for adv in so_brw:
            if adv.state == 'cancel' and adv.partner_id and adv.move_line:
                lines = []
                for l in adv.line_ids:
                    lines.append((1,l.id,{}))
                res = self.onchange_partner_id(cr,uid,ids,adv.partner_id.id,adv.type,lines)['value']
                re2 = self.onchange_move_line(cr,uid,ids,adv.move_line.id,adv.type)['value']
                res.update(re2)
                res.update({'move_line':adv.move_line.id})
                line_ids = []
                for l in res['line_ids']:
                    line_ids.append((0,0,l))
                res.update({'line_ids':line_ids})
        obj=self.pool.get('tcv.voucher.advance')
        vals={'state':'draft'}
        vals.update(res)
        obj.write(cr,uid,ids,vals,context)
        return True

tcv_voucher_advance()


## tcv_voucher_advance_line ---------------------------------------------------------------------------


class tcv_voucher_advance_line(osv.osv):

    _name = 'tcv.voucher.advance.line'

    _description = ''

    _columns = {
        'line_id':fields.many2one('tcv.voucher.advance', 'invoices', required=True, ondelete='cascade'),
        'selected':fields.boolean('Select',required=True),
        'invoice_move_line':fields.many2one('account.move.line', 'Invoice move', store=False ),
        'invoice_move_line2':fields.many2one('account.move.line', 'Invoice move', ondelete='restrict'),
        'invoice':fields.many2one('account.invoice', 'Invoice', ondelete='restrict'),
        'inv_date':fields.date('Date'),
        'inv_amount':fields.float('Amount', digits_compute=dp.get_precision('Account') ),
        'inv_residual':fields.float('Residual', digits_compute=dp.get_precision('Account') ),
        'amount_to_apply':fields.float('Amount to aply', digits_compute=dp.get_precision('Account'),required=True ),
        }

    _defaults = {
        'selected': lambda *a: False,
        'amount_to_apply': lambda *a: 0.0,
        }

    _sql_constraints = [
        ('check_amount_to_apply', 'CHECK(amount_to_apply >= 0)', 'The amount to apply must be >= 0'),
        ]


    def _load_partner_invoice_moves(self,cr,uid,ids,partner_id,account_id, a_type,context=None):
        res = {'line_ids':[]}
        obj_adv = self.pool.get('tcv.voucher.advance')
        adv = obj_adv.browse(cr,uid,ids,context=context)
        obj_move = move = self.pool.get('account.move.line')
        move_ids = obj_move.search(cr, uid, [('account_id', '=', account_id),('reconcile_id','=', 0)])
        moves = obj_move.browse(cr,uid,move_ids,context=context)
        for m in moves:
            if (a_type == 'advance' and m.debit) or (a_type == 'prepaid' and m.credit):
                line = {
                        'selected':False,
                        'invoice_move_line':m.id,
                        'invoice_move_line2':m.id,
                        'invoice':m.invoice.id,
                        'inv_date':m.date,
                        'inv_amount':m.debit+m.credit,
                        'inv_residual':abs(m.amount_residual),
                        'amount_to_apply':0.0,
                        }
                if abs(m.amount_residual) > 0.0001:
                    res['line_ids'].append(line)
        return res


    def onchange_amount_to_apply(self,cr,uid,ids,selected,amount_to_apply,inv_residual):
        res = {}
        if selected:
            if amount_to_apply == 0 or amount_to_apply > inv_residual:
                amount_to_apply = inv_residual
        else:
            amount_to_apply = 0
        res.update({'value':{'selected':amount_to_apply != 0,'amount_to_apply':amount_to_apply}})
        return res


    def create(self,cr,uid,vals,context=None):
        if vals.get('invoice_move_line2'):
            obj_move = move = self.pool.get('account.move.line')
            m = obj_move.browse(cr,uid,vals['invoice_move_line2'],context=context)
            data = {'invoice_move_line':m.id,
                    'invoice':m.invoice.id,
                    'inv_date':m.date,
                    'inv_amount':m.debit+m.credit,
                    'inv_residual':abs(m.amount_residual),
                    }
            vals.update(data)
        res = super(tcv_voucher_advance_line, self).create(cr, uid, vals, context)
        return res


    def write(self, cr, uid, ids, vals, context=None):
        if vals.has_key('selected') and not vals['selected']:
            vals.update({'amount_to_apply':0.0})
        res = super(tcv_voucher_advance_line, self).write(cr, uid, ids, vals, context)
        return res


tcv_voucher_advance_line()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
