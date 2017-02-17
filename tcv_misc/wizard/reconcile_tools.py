# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description:
#
#
##############################################################################
from datetime import datetime
from osv import fields,osv
from tools.translate import _
import pooler
import decimal_precision as dp
import time

class reconcile_tools(osv.osv_memory):

    _name = 'reconcile.tools'

    _description = ''

    _columns = {'name': fields.char('name', size=64, required=False, readonly=False),
        }

    _defaults = {
        }

    '''
    def reconcile_invoice_vs_payment(self,cr, uid, ids, data, context=None):
        #~ data = {partner_id, invoice_number, voucher_amount, voucher_journal_id, voucher_ref, voucher_name}
        if context==None:
            context = {}
        payment = data[0]
        #~ print payment
        obj_inv = self.pool.get('account.invoice')
        obj_vou = self.pool.get('account.voucher')
        inv_id = obj_inv.search(cr, uid, [('number', '=', payment['invoice_number'])])
        inv = vou = None
        if inv_id and len(inv_id) == 1:
            inv = obj_inv.browse(cr,uid,inv_id[0],context=context)
        vou_id = obj_vou.search(cr, uid, [('name','=',payment['voucher_name']),('amount','=',payment['voucher_amount']),('state','=','draft')])
        if vou_id and len(vou_id) == 1:
            vou = obj_vou.browse(cr,uid,vou_id[0],context=context)
        if inv and vou:
            print
            #~ validar voucher
            obj_vou.proforma_voucher(cr, uid, vou_id, context=None)
            vou = obj_vou.browse(cr,uid,vou_id[0],context=context)
            acc_id = inv.partner_id.property_account_receivable.id
            print inv.partner_id.property_account_receivable.name
            move_line_ids = []
            writeoff = 0
            for a in inv.move_id.line_id:
                if a.account_id.id == acc_id:
                    print 'a',a.name, a.ref, a.account_id.name, a.debit, a.credit
                    move_line_ids.append(a.id)
                    writeoff += a.debit-a.credit
            for v in vou.move_ids:
                if v.account_id.id == acc_id:
                    print 'v',v.name, v.ref, v.account_id.name, v.debit, v.credit
                    move_line_ids.append(v.id)
                    writeoff += v.debit-v.credit
            if move_line_ids and len(move_line_ids) > 1:
                #~ reconciliar
                print 'move_line_ids',move_line_ids, writeoff
                obj_rcn = self.pool.get('account.move.line')
                if writeoff == 0:
                    obj_rcn.reconcile(cr, uid, move_line_ids, context=context)
                else:
                    obj_rcn.reconcile_partial(cr, uid, move_line_ids, context=context)


        return True
    '''

    def reconcile_invoices_vs_payments(self,cr, uid, ids, data, context=None):
        #~ data = {partner_id, invoice_list, voucher_list}
        if context==None:
            context = {}
        #~ print payment
        obj_inv = self.pool.get('account.invoice')
        obj_vou = self.pool.get('account.voucher')
        data = data[0]
        inv_ids = obj_inv.search(cr, uid, [('number', 'in',data['invoice_list'])])
        vou_ids = obj_vou.search(cr, uid, [('name','in',data['voucher_list']),('state','=','posted')])
        #~ print data['voucher_list']
        #~ print 'vou_ids',vou_ids
        move_line_ids = []
        writeoff = 0
        acc_id = 0
        for id in inv_ids:
            inv = obj_inv.browse(cr,uid,id,context=context)
            if not acc_id:
                acc_id = inv.partner_id.property_account_receivable.id
                #~ print 'acc_id',acc_id
            for a in inv.move_id.line_id:
                #~ print 'inv',a.id,a.account_id.id
                if acc_id and a.account_id.id == acc_id:
                    move_line_ids.append(a.id)
                    writeoff += a.debit-a.credit
        for id in vou_ids:
            #~ obj_vou.proforma_voucher(cr, uid, id, context=None) # Marcar como valido
            vou = obj_vou.browse(cr,uid,id,context=context)
            for v in vou.move_ids:
                #~ print 'vou',v.id,v.account_id.id
                if acc_id and v.account_id.id == acc_id:
                    move_line_ids.append(v.id)
                    writeoff += v.debit-v.credit
        if move_line_ids and len(move_line_ids) > 1:
            #~ print move_line_ids
            obj_rcn = self.pool.get('account.move.line')
            if writeoff == 0:
                obj_rcn.reconcile(cr, uid, move_line_ids, context=context)
            else:
                obj_rcn.reconcile_partial(cr, uid, move_line_ids, context=context)
        return True

reconcile_tools()
