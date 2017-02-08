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
from tools.translate import _
#~ import pooler
#~ import decimal_precision as dp
#~ import time
#~ import netsvc


class account_invoice(osv.osv):

    _inherit = 'account.invoice'

    def get_invoice_currency_rate(self, cr, uid, brw_invoice, context=None):
        if brw_invoice.company_id.currency_id == brw_invoice.currency_id:
            return 1
        context = context or {}
        obj_cur = self.pool.get('res.currency')
        if brw_invoice.date_invoice != 'False':
            context = {'date': brw_invoice.date_invoice}
        from_currency = brw_invoice.currency_id
        to_currency = brw_invoice.company_id.currency_id
        rate = obj_cur._get_conversion_rate(
            cr, uid, from_currency, to_currency, context)
        return round(rate, brw_invoice.company_id.currency_id.accuracy)

    def _import_purchase_data(self, cr, uid, vals, context=None):
        obj_ord = self.pool.get('purchase.order')
        obj_pnr = self.pool.get('res.partner')
        obj_acc = self.pool.get('res.partner.account')
        if vals.get('origin'):
            por_id = obj_ord.search(cr, uid, [('name', '=', vals['origin'])])
            if por_id and len(por_id) == 1:
                por = obj_ord.browse(cr, uid, por_id[0], context=context)
                # update partner account -----
                partner = por.partner_id
                upd_partner = {}
                if not partner.supplier:
                    upd_partner.update({'supplier': True})
                if not partner.account_kind_pay:
                    acc_id = obj_acc.search(
                        cr, uid, [('name', '=', 'CXP NACIONALES')])[0]
                    upd_partner.update({'account_kind_pay': acc_id})
                if upd_partner:
                    obj_pnr.write(
                        cr, uid, [partner.id], upd_partner, context=context)
                    new_partner = obj_pnr.browse(
                        cr, uid, partner.id, context=context)
                    if vals.get('account_id'):
                        vals.update({'account_id':
                                     new_partner.property_account_payable.id})
                # --------------------------
                vals.update({'supplier_invoice_number': por.partner_ref,
                             'name': por.description,
                             'group_wh_iva_doc': partner.group_wh_iva_doc,
                             'import_id': por.import_id.id,
                             })
        return True

    def finalize_invoice_move_lines(self, cr, uid, invoice_browse, move_lines):
        """finalize_invoice_move_lines(cr, uid, invoice, move_lines) ->
        move_lines Hook method to be overridden in additional modules to
        verify and possibly alter the move lines to be created by an invoice,
        for special cases.
        :param invoice_browse: browsable record of the invoice that is
                               generating the move lines
        :param move_lines: list of dictionaries with the account.move.lines
                           (as for create())
        :return: the (possibly updated) final move_lines to create for this
                 invoice
        """
        move_lines = super(account_invoice, self).finalize_invoice_move_lines(
            cr, uid, invoice_browse, move_lines)
        if invoice_browse.type == u'in_invoice':
            if move_lines and \
                    invoice_browse.currency_id.id != \
                    invoice_browse.company_id.currency_id.id:
                obj_cur = self.pool.get('res.currency')
                cur_brw = obj_cur.browse(
                    cr, uid, invoice_browse.currency_id.id, context={})
                if not cur_brw.account_id:
                    raise osv.except_osv(
                        _('Error!'),
                        _('Must specify an account for currency rounding ' +
                          'diff (%s)') % cur_brw.name)
                amount_diff = 0
                for x, y, ln in move_lines:
                    ln.update({'debit': round(ln['debit'], 2),
                               'credit': round(ln['credit'], 2)})
                    amount_diff += ln['debit'] - ln['credit']
                if amount_diff != 0:
                    line = {
                        'account_id': cur_brw.account_id.id,
                        'date': invoice_browse.date_invoice,
                        'partner_id': invoice_browse.partner_id.id,
                        'name': _('Currency rounding diff'),
                        'debit': abs(amount_diff) if amount_diff < 0
                        else 0,
                        'credit': abs(amount_diff) if amount_diff > 0
                        else 0,
                        }
                    move_lines.append((0, 0, line))
        return move_lines

    def test_open(self, cr, uid, ids, *args):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        for item in self.browse(cr, uid, ids, context={}):
            if item.date_invoice < item.date_document:
                raise osv.except_osv(
                    _('Error!'),
                    _('The accounting date must be >= document date'))
            if not item.tax_line:
                raise osv.except_osv(
                    _('Error!'),
                    _('Must indicate at least one tax line'))
        return super(account_invoice, self).test_open(cr, uid, ids, args)

    def create(self, cr, uid, vals, context=None):
        if vals.get('type') in ('in_invoice', 'in_refund'):
            self._import_purchase_data(cr, uid, vals, context)
        if vals.get('supplier_invoice_number'):
            vals.update({'reference': vals['supplier_invoice_number'],
                         'reference_type': 'none'})
        res = super(account_invoice, self).create(cr, uid, vals, context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        if vals.get('supplier_invoice_number'):
            vals.update({'reference': vals['supplier_invoice_number'],
                         'reference_type': 'none'})
        res = super(account_invoice, self).write(cr, uid, ids, vals, context)
        return res


account_invoice()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
