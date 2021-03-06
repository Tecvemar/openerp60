# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2013-09-11
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
# ~ import decimal_precision as dp
# ~ import time
#~ import netsvc


##----------------------------------------------------------- tcv_sale_lot_list

class tcv_sale_lot_list(osv.osv_memory):

    _inherit = 'tcv.sale.lot.list'

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'consignement_id': fields.many2one(
            'tcv.consignment', 'Consignement order', ondelete='restrict',
            select=True, readonly=True),
        }

    _defaults = {
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    def button_done_consig(self, cr, uid, ids, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        obj_cns = self.pool.get('tcv.consignment')
        obj_col = self.pool.get('tcv.sale.data.collector')
        brw = self.browse(cr, uid, ids, context={})[0]
        duplicated = []
        # Add Actual order lots to duplicated
        for item in brw.consignement_id.line_ids:
            if item.prod_lot_id and item.prod_lot_id.id:
                duplicated.append(item.prod_lot_id.id)
        if brw.consignement_id:
            if brw.consignement_id.state != 'draft':
                raise osv.except_osv(
                    _('Error!'),
                    _('Can\'t add lines when state <> "draft"'))
            lots = []
            for item in brw.line_ids:
                if item.prod_lot_id and item.prod_lot_id.id in duplicated:
                    raise osv.except_osv(
                        _('Error!'),
                        _('The lot must be unique!\nLot: %s\nProduct: %s') % (
                            item.prod_lot_id.name,
                            item.prod_lot_id.product_id.name))
                else:
                    duplicated.append(item.prod_lot_id.id)
                if item.prod_lot_id and \
                        item.product_id.stock_driver != 'normal' and \
                        not item.pieces:
                    raise osv.except_osv(
                        _('Error!'),
                        _('Can\'t process a lot with 0 pieces (%s)') %
                        (item.prod_lot_id.name))
                if item.prod_lot_id:
                    lots.append({'prod_lot_id': item.prod_lot_id.id,
                                 'pieces': item.pieces,
                                 'price_unit': item.price_unit,
                                 'product_qty': item.product_qty})
            if lots:
                lines = obj_col.create_order_lines(cr, uid, ids, lots, context)
                if lines:
                    lines.reverse()  # To set same order for TXT file
                    obj_cns.write(cr, uid, brw.consignement_id.id,
                                 {'line_ids': lines}, context)

        return {'type': 'ir.actions.act_window_close'}

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow


tcv_sale_lot_list()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
