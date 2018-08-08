# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2015-08-12
#    Version: 0.0.0.1
#
#    Description:
#
#
##############################################################################

#~ from datetime import datetime
from osv import osv
from tools.translate import _
#~ import pooler
#~ import decimal_precision as dp
#~ import time
#~ import netsvc

##-------------------------------------------------------- stock_production_lot


class stock_production_lot(osv.osv):

    _inherit = 'stock.production.lot'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        }

    _defaults = {
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    def check_lot_for_sale_invoice(
            self, cr, uid, lot_brw, quantity, invoice, context={}):
        """
        Check if this lot is used or compromised in any other document
        return msg_not_for_sale
        """
        res = []
        if not lot_brw or invoice.type != 'out_invoice':
            return ''
        obj_so = self.pool.get('sale.order')
        # available qty
        if lot_brw.stock_available < quantity:
            res.append(_('No stock available for lot: %s') % lot_brw.name)
        # check sale_invoices
        if lot_brw.invoice_lines_ids:
            for inv_line in lot_brw.invoice_lines_ids:
                inv = inv_line.invoice_id
                if inv.id != invoice.id:
                    so_ids = obj_so.search(
                        cr, uid, [('invoice_ids', 'in', [inv.id])])
                    for so in obj_so.browse(cr, uid, so_ids, context=None):
                        if so.state != 'cancel':
                            if not so.picking_ids:
                                res.append(
                                    _('Lot with unavailable pickings for '
                                      'sale order: %s, lot: %s') %
                                    (so.name, lot_brw.name))
                            else:
                                for pk in so.picking_ids:
                                    if pk.state not in ('cancel', 'done'):
                                        res.append(
                                            _('Lot with unprocesed pickings '
                                              'for sale order: %s, lot: %s, '
                                              'picking: %s') %
                                            (so.name, lot_brw.name, pk.name))
        return '\n'.join(res)

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow


stock_production_lot()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
