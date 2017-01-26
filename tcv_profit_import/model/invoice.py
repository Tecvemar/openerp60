# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

#~ from datetime import datetime
from osv import osv
#~ from tools.translate import _
#~ import pooler
#~ import decimal_precision as dp
#~ import time
#~ import netsvc


class account_invoice(osv.osv):

    _inherit = 'account.invoice'

    def _import_in_invoice_from_profit(self, cr, uid, vals, context=None):
        obj_ord = self.pool.get('purchase.order')
        obj_imp = self.pool.get('tcv.purchase.order.import')
        obj_cur = self.pool.get('res.currency')
        obj_jnl = self.pool.get('account.journal')
        obj_pnr = self.pool.get('res.partner')
        obj_acc = self.pool.get('res.partner.account')
        por_id = obj_ord.search(cr, uid, [('name', '=', vals['origin'])])
        if por_id and len(por_id) == 1:
            por = obj_ord.browse(cr,uid,por_id[0],context=context)
            # update partner account -----
            partner = por.partner_id
            upd_partner = {}
            if not partner.supplier:
                upd_partner.update({'supplier':True})
            if not partner.account_kind_pay:
                acc_id = obj_acc.search(cr, uid, [('name', '=', 'CXP NACIONALES')])[0]
                upd_partner.update({'account_kind_pay':acc_id})
            if upd_partner:
                obj_pnr.write(cr,uid,[partner.id],upd_partner,context=context)
                new_partner = obj_pnr.browse(cr,uid,partner.id,context=context)
                if vals.get('account_id'):
                    vals.update({'account_id':new_partner.property_account_payable.id})
            # --------------------------
            if por.profit_doc and por.profit_db:
                context.update({'profit_config':por.profit_db})
                imp_id = obj_imp.create(cr,uid,{'name':por.profit_doc,'profit_id':por.profit_db.id},context)
                data = obj_imp._get_profit_document(cr,uid,[imp_id],context=context)
                date_document = obj_imp.encode_date(data['fec_reg']) if data['fec_reg'].year != 1900 else obj_imp.encode_date(data['fec_emis'])
                currency_id = obj_cur.search(cr, uid, [('name', '=', obj_imp.profit_2_openerp_currency(por.profit_db.company_ref,data['moneda']))])[0]
                if currency_id == 3: #### VEB
                    jnl_id = obj_jnl.search(cr, uid, [('code', '=', 'DCN')])[0]
                    vals.update({'journal_id':jnl_id})
                vals.update({'internal_number':data['nro_doc'],
                             'supplier_invoice_number':data['nro_fact'],
                             'nro_ctrl':data['n_control'] or data['nro_fact'],
                             'check_total':float(data['monto_net']),
                             'date_invoice':obj_imp.encode_date(data['fec_emis']),
                             'date_due':obj_imp.encode_date(data['fec_venc']),
                             'date_document':date_document,
                             'currency_id':currency_id,
                             'comment':por.notes,
                             'group_wh_iva_doc':partner.group_wh_iva_doc,
                             })
                if data.get('observa'):
                    vals.update({'name':data['observa']})
        return True


    def _import_out_invoice_from_profit(self, cr, uid, vals, context=None):
        obj_ord = self.pool.get('sale.order')
        obj_inv = self.pool.get('tcv.profit.invoice.import')
        obj_cur = self.pool.get('res.currency')
        obj_jnl = self.pool.get('account.journal')
        obj_pnr = self.pool.get('res.partner')
        obj_acc = self.pool.get('res.partner.account')
        por_id = obj_ord.search(cr, uid, [('name', '=', vals['origin'])])
        if por_id and len(por_id) == 1:
            por = obj_ord.browse(cr,uid,por_id[0],context=context)
            # update partner account -----
            partner = por.partner_id
            upd_partner = {}
            if not partner.customer:
                upd_partner.update({'customer':True})
            if not partner.account_kind_rec:
                acc_id = obj_acc.search(cr, uid, [('name', '=', 'CXC NACIONALES')])[0]
                upd_partner.update({'account_kind_rec':acc_id})
            if upd_partner:
                obj_pnr.write(cr,uid,[partner.id],upd_partner,context=context)
                new_partner = obj_pnr.browse(cr,uid,partner.id,context=context)
                if vals.get('account_id'):
                    vals.update({'account_id':new_partner.property_account_receivable.id})
            # --------------------------
            if por.profit_doc and por.profit_db:
                context.update({'profit_config':por.profit_db})
                #~ imp_id = obj_ped.create(cr,uid,{'name':por.profit_doc,'profit_id':por.profit_db.id},context)
                inv_id = obj_inv.create(cr,uid,{'name':por.profit_inv,'profit_id':por.profit_db.id},context)
                data_inv = obj_inv._get_profit_document(cr,uid,[inv_id],context=context)
                currency_id = obj_cur.search(cr, uid, [('name', '=', obj_inv.profit_2_openerp_currency(por.profit_db.company_ref,data_inv['moneda']))])[0]
                if currency_id == 3: #### VEB
                    jnl_id = obj_jnl.search(cr, uid, [('code', '=', 'DVN')])[0]
                    vals.update({'journal_id':jnl_id})
                vals.update({'internal_number':data_inv['fact_num'],
                             'nro_ctrl':data_inv['numcon'],
                             'payment_term':4,
                             'date_invoice':obj_inv.encode_date(data_inv['fec_emis']),
                             'date_due':obj_inv.encode_date(data_inv['fec_venc']),
                             'currency_id':currency_id,
                             'comment':por.note,
                             })
                if data_inv.get('observa'):
                    vals.update({'name':data_inv['observa']})
        return True


    def create(self, cr, uid, vals, context=None):
        belongs = self.pool.get('res.users').\
            user_belongs_groups(cr, uid, ('tcv_profit_import / Manager',
                                          'tcv_profit_import / sale',
                                          'tcv_profit_import / purchase'), context)
        if belongs and vals.get('origin'):
            if vals.get('type') in ('in_invoice','in_refund'):
                self._import_in_invoice_from_profit(cr, uid, vals, context)
            else:
                self._import_out_invoice_from_profit(cr, uid, vals, context)
        res = super(account_invoice, self).create(cr, uid, vals, context)
        return res


account_invoice()



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
