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

##---------------------------------------------------------- tcv_lot_range_sale


class tcv_lot_range_sale(osv.osv_memory):

    _name = 'tcv.lot.range.sale'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'prod_lot_id': fields.many2one('stock.production.lot',
                                       'First lot', required=True),
        'product_id': fields.related('prod_lot_id', 'product_id',
                                     type='many2one',
                                     relation='product.product',
                                     string='Product',
                                     store=False, readonly=True),
        'item_qty': fields.integer('Lot\'s qty'),
        }

    _defaults = {
        'item_qty': 1,
        }

    _sql_constraints = [
        ('item_qty_range', 'CHECK(item_qty between 1 and 99)',
         'The Lot\'s qty must be in 1-99 range!'),
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    def create_wizard_lines(self, cr, uid, ids, lot_rng, context=None):
        lines = []
        obj_prd = self.pool.get('product.product')
        if lot_rng.prod_lot_id.name.isdigit() and lot_rng.item_qty:
            obj_lot = self.pool.get('stock.production.lot')
            obj_uom = self.pool.get('product.uom')
            lot_int = int(lot_rng.prod_lot_id.name)
            lot_names = map(lambda x: str(x),
                            range(lot_int, lot_int + lot_rng.item_qty))
            for lot_name in lot_names:
                lot_ids = obj_lot.search(
                    cr, uid, [('name', 'ilike', lot_name)])
                for lot in obj_lot.browse(cr, uid, lot_ids, context={}):
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
            lot_rng = self.browse(cr, uid, ids, context={})[0]
            obj_so = self.pool.get('tcv.sale.lot.list')
            lines = self.create_wizard_lines(
                cr, uid, ids, lot_rng, context=context)
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

tcv_lot_range_sale()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
