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
from osv import osv, fields
from tools.translate import _
#~ import pooler
#~ import decimal_precision as dp
import time
#~ import netsvc


##------------------------------------------------------------- account_invoice


class account_invoice(osv.osv):

    _inherit = 'account.invoice'

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'period_id': fields.many2one(
            'account.period', 'Force Period',
            domain=[('state','<>','done')],
            help="Keep empty to use the period of the validation(invoice)'\
            ' date.", readonly=True, states={'draft':[('readonly',False)]}),
        }

    _defaults = {
        }

    _sql_constraints = [
        ]

    ##-----------------------------------------------------

    ##----------------------------------------------------- public methods

    def action_date_assign(self, cr, uid, ids, *args):
        res = super(account_invoice, self).action_date_assign(
            cr, uid, ids, args)
        date = time.strftime('%Y-%m-%d')
        for item in self.browse(cr, uid, ids, context={}):
            values = {}
            if not item.date_invoice:
                values.update({'date_invoice': date})
            if not item.date_document:
                values.update({'date_document': date})
            if values:
                self.write(cr, uid, [item.id], values)
        return res

    def invoice_pay_customer(self, cr, uid, ids, context=None):
        for inv in self.browse(cr, uid, ids, context={}):
            if inv.type == 'in_invoice':
                obj_wh_islr = self.pool.get('islr.wh.doc.invoices')
                islr_ids = obj_wh_islr.search(
                    cr, uid, [('invoice_id', 'in', ids)])
                for islr in obj_wh_islr.browse(cr, uid, islr_ids,
                                               context=context):
                    if islr.islr_wh_doc_id.state != 'done':
                        raise osv.except_osv(
                            _('Error!'),
                            _('You must first process the ISLR withholding'))
                obj_wh_iva = self.pool.get('account.wh.iva.line')
                iva_ids = obj_wh_iva.search(
                    cr, uid, [('invoice_id', 'in', ids)])
                for iva in obj_wh_iva.browse(cr, uid, iva_ids,
                                             context=context):
                    if iva.retention_id.state != 'done':
                        raise osv.except_osv(
                            _('Error!'),
                            _('You must first process the IVA withholding'))
        return super(account_invoice, self).\
            invoice_pay_customer(cr, uid, ids, context)

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
        ok_lines = []
        if invoice_browse.type == u'out_invoice':

            obj_cst = self.pool.get('tcv.cost.management')
            account_out = []
            lines = []
            for i in invoice_browse.invoice_line:
                categ_id = i.product_id.categ_id
                if i.product_id and i.product_id.type == 'product':
                    if categ_id and categ_id.property_stock_account_output_categ:
                        account_out.append(categ_id.property_stock_account_output_categ.id)
                    if categ_id and categ_id.property_account_expense_categ:
                        account_out.append(categ_id.property_account_expense_categ.id)
                    if i.product_id.property_stock_account_output:
                        account_out.append(i.product_id.property_stock_account_output.id)
                    if i.product_id.property_account_expense:
                        account_out.append(i.product_id.property_account_expense.id)
                lines.append(i)

            if account_out:
                for item in move_lines:
                    if not item[2].get('account_id') in account_out:
                        ok_lines.append(item)

                for i in lines:
                    if i.prod_lot_id:
                        name = '(%s) %s' % (i.prod_lot_id.name,
                                            i.product_id.name)
                    else:
                        name = i.product_id.name
                    price_unit = obj_cst.get_tcv_cost(
                        cr, uid, i.prod_lot_id.id, i.product_id.id,
                        context=None)
                    price = round(price_unit * i.quantity, 2)
                    categ_id = i.product_id.categ_id
                    debit_acc = i.product_id.property_account_expense or \
                        categ_id and \
                        categ_id.property_account_expense_categ and \
                        categ_id.property_account_expense_categ.id
                    debit = {'analytic_lines': [],
                             'account_id': debit_acc,
                             'currency_id': False,
                             'date_maturity': False,
                             'date': invoice_browse.date_invoice,
                             'partner_id': invoice_browse.partner_id.id,
                             'product_id': i.product_id.id,
                             'analytic_account_id': i.account_analytic_id and i.account_analytic_id.id,
                             'tax_amount': False,
                             'name': name,
                             'product_uom_id': i.uos_id.id,
                             'tax_code_id': False,
                             'debit': price,
                             'credit': 0,
                             'amount_currency': 0,
                             'ref': '',
                             'quantity': i.quantity}
                    credit_acc = \
                        i.product_id.property_stock_account_output or \
                        categ_id and \
                        categ_id.property_stock_account_output_categ and \
                        categ_id.property_stock_account_output_categ.id
                    credit = {'analytic_lines': [],
                              'account_id': credit_acc,
                              'currency_id': False,
                              'date_maturity': False,
                              'date': invoice_browse.date_invoice,
                              'partner_id': invoice_browse.partner_id.id,
                              'product_id': i.product_id.id,
                              'analytic_account_id': i.account_analytic_id and i.account_analytic_id.id,
                              'tax_amount': False,
                              'name': name,
                              'product_uom_id': i.uos_id.id,
                              'tax_code_id': False,
                              'debit': 0,
                              'credit': price,
                              'amount_currency': 0,
                              'ref': '',
                              'quantity': i.quantity}
                    ok_lines.append((0, 0, credit))
                    ok_lines.append((0, 0, debit))
                if ok_lines and \
                        invoice_browse.currency_id.id != \
                        invoice_browse.company_id.currency_id.id:
                    obj_cur = self.pool.get('res.currency')
                    cur_brw = obj_cur.browse(
                        cr, uid, invoice_browse.currency_id.id, context={})
                    if not cur_brw.account_id:
                        raise osv.except_osv(
                            _('Error!'),
                            _('Mus specify an account for currency rounding '
                              'diff (%s)') % cur_brw.name)
                    amount_diff = 0
                    for x, y, ln in ok_lines:
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
                        ok_lines.append((0, 0, line))
                    ok_lines.reverse()

        return ok_lines or move_lines

    ##----------------------------------------------------- buttons (object)

    def button_nullify(self, cr, uid, ids, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        for item in self.browse(cr, uid, ids, context={}):
            if item.internal_number:
                number = item.internal_number if not item.number else ''
                cr.execute(
                    "update account_invoice set number = '%s' where id = %s"
                    % (number, item.id))
        return True

    # Deprecated at 2018-01-01 this feature is useless
    # ~ def button_reset_taxes2(self, cr, uid, ids, context=None):
        # ~ '''
        # ~ Replace original button to implement special TAX (es_VE) case:
            # ~ tax amount 12%, 9% or 7% based on invoice amount and
            # ~ payment method valid from 2017-09-19 to 2017-12-31
        # ~ '''
        # ~ ids = isinstance(ids, (int, long)) and [ids] or ids
        # ~ if ids and len(ids) == 1:
            # ~ invoice = self.browse(cr, uid, ids[0], context={})
            # ~ invoice_line_tax_id = 0
            # ~ for line in invoice.invoice_line:
                # ~ for tax in line.invoice_line_tax_id:
                    # ~ if tax.appl_type == 'general':
                        # ~ invoice_line_tax_id = invoice_line_tax_id or tax.id
            # ~ type_tax_use = 'sale' if 'out_' in invoice.type else 'purchase'
            # ~ return {'name': _('Special tax selection'),
                    # ~ 'type': 'ir.actions.act_window',
                    # ~ 'res_model': 'tcv.special.tax.sel',
                    # ~ 'view_type': 'form',
                    # ~ 'view_id': False,
                    # ~ 'view_mode': 'form',
                    # ~ 'nodestroy': True,
                    # ~ 'target': 'new',
                    # ~ 'domain': "",
                    # ~ 'context': {
                        # ~ 'default_type': invoice.type,
                        # ~ 'default_invoice_id': invoice.id,
                        # ~ 'default_type_tax_use': type_tax_use,
                        # ~ 'default_invoice_line_tax_id': invoice_line_tax_id,
                        # ~ }}
        # ~ return self.button_reset_taxes(cr, uid, ids, context)

    ##----------------------------------------------------- on_change...

    ##----------------------------------------------------- create write unlink

    ##----------------------------------------------------- Workflow

    def test_open(self, cr, uid, ids, *args):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        #~ obj_ail = self.pool.get('account.invoice.line')
        obj_lot = self.pool.get('stock.production.lot')
        obj_inv = self.pool.get('account.invoice')
        sql = "select distinct i.id, p.name, i.origin, o.name " + \
            "from account_invoice_line l " + \
            "left join account_invoice i on l.invoice_id = i.id " + \
            "left join res_partner p on i.partner_id = p.id " + \
            "left join stock_production_lot o on l.prod_lot_id = o.id " + \
            "where l.prod_lot_id in (%s) and i.state = 'draft' and " + \
            "i.id not in (%s)"
        for item in self.browse(cr, uid, ids, context={}):
            lot_ids = []
            if item.date_invoice < item.date_document:
                raise osv.except_osv(
                    _('Error!'),
                    _('The accounting date must be >= document\'s date'))
            for line in item.invoice_line:
                if line.prod_lot_id and \
                        line.prod_lot_id.product_id.stock_driver in ('slab',
                                                                     'block'):
                    lot_ids.append(line.prod_lot_id.id)

                msg_not_for_sale = obj_lot.check_lot_for_sale_invoice(
                    cr, uid, line.prod_lot_id, line.quantity, item)
                if msg_not_for_sale:
                    raise osv.except_osv(
                        _('Error!'),
                        _('Invoice can\'t be aproved!\n%s') %
                        msg_not_for_sale)
            if lot_ids:
                cr.execute(sql % (str(lot_ids)[1:-1].replace('L', ''),
                                  str(ids)[1:-1].replace('L', '')))
                invoices = cr.fetchall()
                if invoices:
                    str_inv = u', '.join([
                        u'%s: %s (%s)' % (x[3], x[2], x[1]) for x in invoices])
                    raise osv.except_osv(
                        _('Error!'),
                        _('This lot is duplicated in the invoice(s):\n%s') %
                        str_inv)
            #~ Acá revisamos si hay facturas de ventas,
            #~ con el mismo  numero de control
            #~ Y el ID diferente a la factura actual
            #~ Si se consigue, se genera un mensaje de error
            try:
                duplicated = obj_inv.read(cr, uid, obj_inv.search(
                    cr, uid, [
                    ('nro_ctrl', '=', item.nro_ctrl),
                    ('type', '=', 'out_invoice' ),
                    ('id', '!=', item.id),
                    ])[0])['number']
                raise osv.except_osv(
                    _('Error!'),
                    _('The invoice %s has already registered with the control number %s') %
                    (duplicated, item.nro_ctrl))
            except IndexError:
                pass
        return super(account_invoice, self).test_open(cr, uid, ids, args)

    def action_cancel_draft(self, cr, uid, ids, *args):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        for item in self.browse(cr, uid, ids, context={}):
            if item.number:
                raise osv.except_osv(
                    _('Error!'),
                    _('Can\'t reset an invoice with assigned number (%s)') %
                    item.number)
        return super(account_invoice, self).\
            action_cancel_draft(cr, uid, ids, args)

    def action_cancel(self, cr, uid, ids, *args):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        obj_so = self.pool.get('sale.order')
        obj_grp = self.pool.get('res.groups')
        group_ids = obj_grp.search(
            cr, uid, [('name', '=', 'TCV Sales / sale invoice void')])
        user_ids = []
        if group_ids:
            group = obj_grp.browse(cr, uid, group_ids[0], context=None)
            user_ids = [x.id for x in group.users]
        if uid not in user_ids:
            for item in self.browse(cr, uid, ids, context={}):
                #~ Check if invoice is associated with sale_order and have
                #~ any active picking (state!= 'cancel')
                so_ids = obj_so.search(
                    cr, uid, [('invoice_ids', 'in', [item.id])])
                for so in obj_so.browse(cr, uid, so_ids, context=None):
                    for picking in so.picking_ids:
                        if picking.state != 'cancel':
                            raise osv.except_osv(
                                _('Error!'),
                                _('Can\'t reset an invoice while sale order '
                                  'have picking in state <> Cancel (%s, %s)'
                                  'User must belong to: TCV Sales / sale '
                                  'invoice void group to cancel this '
                                  'invoice') %
                                (so.name, picking.name))
        return super(account_invoice, self).\
            action_cancel(cr, uid, ids, args)

    def write(self, cr, uid, ids, vals, context=None):
        """
        Adjust invoice date's changes in out invoice adn refund
        """
        obj_per = self.pool.get('account.period')
        obj_inv = self.pool.get('account.invoice')
        ids = isinstance(ids, (int, long)) and [ids] or ids
        for item in self.browse(cr, uid, ids, context={}):
            if 'date_invoice' in vals and 'date_document' not in vals:
                itype = vals.get('type', item.type)
                if itype in ('out_invoice', 'out_refund'):
                    period_id = obj_per.find(cr, uid, vals['date_invoice'])[0]
                    vals.update({
                        'date_document': vals['date_invoice'],
                        'period_id': period_id,
                        })
        res = super(account_invoice, self).write(
            cr, uid, ids, vals, context)
        return res

    def unlink(self, cr, uid, ids, context=None):
        obj_so = self.pool.get('sale.order')
        for item in self.browse(cr, uid, ids, context={}):
            if item.type in ['out_invoice', 'out_refund'] and \
                    item.nro_ctrl:
                raise osv.except_osv(
                    _('Error!'),
                    _('Can\'t delete an invoice with Control Number (%s)') %
                    item.nro_ctrl)
            #~ Check if invoice is associated with sale_order and have
            #~ any active picking (state!= 'cancel')
            so_ids = obj_so.search(cr, uid, [('invoice_ids', 'in', [item.id])])
            for so in obj_so.browse(cr, uid, so_ids, context=None):
                for picking in so.picking_ids:
                    if picking.state != 'cancel':
                        raise osv.except_osv(
                            _('Error!'),
                            _('Can\'t delete an invoice while sale order '
                              'have picking in state <> Cancel (%s, %s)') %
                            (so.name, picking.name))
        res = super(account_invoice, self).unlink(cr, uid, ids, context)
        return res


account_invoice()


##-------------------------------------------------------- account_invoice_line


class account_invoice_line(osv.osv):

    _inherit = 'account.invoice.line'

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        }

    _defaults = {
        }

    _sql_constraints = [
        ]

    ##-----------------------------------------------------

    ##----------------------------------------------------- public methods

    ##----------------------------------------------------- buttons (object)

    ##----------------------------------------------------- on_change...

    ##----------------------------------------------------- create write unlink

    def create(self, cr, uid, vals, context=None):
        # auto add a tax 0% if no tax selected
        if len(vals.get('invoice_line_tax_id')[0][2]) > 1:
            raise osv.except_osv(
                _('Error!'),
                _('Can\'t select multiple taxes for single line'))
        elif len(vals.get('invoice_line_tax_id')[0][2]) == 0:  # No tax >set 0%
            inv = self.pool.get('account.invoice').\
                browse(cr, uid, vals.get('invoice_id'), context=context)
            if inv.type in ('in_invoice', 'in_refund'):
                tax_id = self.pool.get('account.tax').\
                    search(cr, uid, [('name', '=', 'IVA 0% Compras')])
            else:
                tax_id = self.pool.get('account.tax').\
                    search(cr, uid, [('name', '=', 'IVA 0% Ventas')])
            if tax_id:
                vals.update({'invoice_line_tax_id': [(6, 0, tax_id)]})
        res = super(account_invoice_line, self).create(cr, uid, vals, context)
        return res

    ##----------------------------------------------------- Workflow


account_invoice_line()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
