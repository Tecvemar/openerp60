# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2017-09-26
#    Version: 0.0.0.1
#
#    Description:
#
#
##############################################################################

#~ from datetime import datetime
from osv import fields, osv
#~ from tools.translate import _
#~ import pooler
#~ import decimal_precision as dp
#~ import time
#~ import netsvc

##--------------------------------------------------------- tcv_special_tax_sel


class tcv_special_tax_sel(osv.osv_memory):

    _name = 'tcv.special.tax.sel'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'name': fields.char(
            'Name', size=64, required=False, readonly=False),
        'type': fields.selection([
            ('out_invoice', 'Customer Invoice'),
            ('in_invoice', 'Supplier Invoice'),
            ('out_refund', 'Customer Refund'),
            ('in_refund', 'Supplier Refund'),
            ], 'Type', readonly=True, select=True, change_default=True),
        'type_tax_use': fields.selection([
            ('sale', 'Sale'),
            ('purchase', 'Purchase'),
            ], 'Tax use', readonly=True, select=True, change_default=True),
        'invoice_id': fields.many2one(
            'account.invoice', 'Invoice Reference', ondelete='restrict',
            select=True),
        'invoice_line_tax_id': fields.many2one(
            'account.tax', 'Tax', required=False, ondelete='restrict'),
        'apply_new_tax': fields.boolean(
            'Apply new tax'),
        }

    _defaults = {
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    def button_done(self, cr, uid, ids, context=None):
        obj_inv = self.pool.get('account.invoice')
        obj_ail = self.pool.get('account.invoice.line')
        for item in self.browse(cr, uid, ids, context={}):
            if item.invoice_line_tax_id and item.apply_new_tax:
                for line in item.invoice_id.invoice_line:
                    for tax in line.invoice_line_tax_id:
                        obj_ail.write(
                            cr, uid, [line.id],
                            {'invoice_line_tax_id': [(3, tax.id)]},
                            context=context)
                        tax_id = item.invoice_line_tax_id.id
                        obj_ail.write(
                            cr, uid, [line.id],
                            {'invoice_line_tax_id': [(4, tax_id)]},
                            context=context)
            res = obj_inv.button_reset_taxes(
                cr, uid, [item.invoice_id.id], context)
            return {'type': 'ir.actions.act_window_close'}

    ##------------------------------------------------------------ on_change...

    def on_change_invoice_line_tax_id(self, cr, uid, ids, invoice_line_tax_id):
        res = {}
        res.update({'apply_new_tax': bool(invoice_line_tax_id)})
        return {'value': res}

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow


tcv_special_tax_sel()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
