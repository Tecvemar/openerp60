# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2014-05-26
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

##---------------------------------------------------------- tcv_bundle_sale


class tcv_bundle_sale(osv.osv_memory):

    _name = 'tcv.bundle.sale'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'bundle_ids': fields.many2many(
            'tcv.bundle', 'bundle_rel', 'sale_order_id',
            'bundle_id', 'Bundles',
            domain=[('reserved', '=', False)])
        }

    _defaults = {
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    def create_wizard_lines(self, cr, uid, ids, bundle_lines, context=None):
        lines = []
        obj_uom = self.pool.get('product.uom')
        obj_prd = self.pool.get('product.product')
        for bundle in bundle_lines.bundle_ids:
            for item in bundle.line_ids:
                lot = item.prod_lot_id
                product_qty = lot.stock_available
                pieces = obj_uom._compute_pieces(
                    cr, uid, lot.product_id.stock_driver,
                    product_qty, lot.lot_factor, context=context)
                list_price = obj_prd.get_property_list_price(
                        cr, uid, lot.product_id, lot, None)
                data = {'product_id': lot.product_id.id,
                        'prod_lot_id': lot.id,
                        'max_pieces': pieces,
                        'pieces': pieces,
                        'product_qty': product_qty,
                        'price_unit': list_price,
                        }
                lines.append((0, 0, data))
        return lines

    ##-------------------------------------------------------- buttons (object)

    def button_done(self, cr, uid, ids, context=None):
        context = context or {}
        ids = isinstance(ids, (int, long)) and [ids] or ids
        if context.get('active_model') == 'tcv.sale.lot.list' and \
                context.get('active_ids'):
            bundles = self.browse(cr, uid, ids, context={})[0]
            obj_so = self.pool.get('tcv.sale.lot.list')
            lines = self.create_wizard_lines(
                cr, uid, ids, bundles, context=context)
            if lines:
                obj_so.write(cr, uid, context.get('active_ids'),
                             {'line_ids': lines}, context)
        return {'type': 'ir.actions.act_window_close'}

    ##------------------------------------------------------------ on_change...

    def on_change_prod_lot_id(self, cr, uid, ids, prod_lot_id):
        res = {}
        if not prod_lot_id:
            return res
        obj_lot = self.pool.get('stock.production.lot')
        lot = obj_lot.browse(cr, uid, prod_lot_id, context=None)
        res.update({'product_id': lot.product_id.id})
        res = {'value': res}
        return res

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_bundle_sale()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
