# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
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
#~ import time
#~ from datetime import datetime
#~ from dateutil.relativedelta import relativedelta
#~ from datetime import datetime, timedelta
from osv import osv, fields
#~ import netsvc
#~ import pooler
#~ from tools.translate import _
import decimal_precision as dp
#~ from osv.orm import browse_record, browse_null
import logging
logger = logging.getLogger('server')


class stock_move(osv.osv):
    _inherit = 'stock.move'

    def _compute_pieces(self, cr, uid, ids, name, arg, context=None):
        move = self.browse(cr, uid, ids)
        res = {}
        for m in move:
            if m.product_id.stock_driver in ('tile','slab','block'):
                uom = self.pool.get('product.uom')
                pieces = uom._compute_pieces(cr, uid, m.product_id.stock_driver,
                        m.product_qty, m.prodlot_id.lot_factor, context)
                res[m.id] = pieces
            else:
                res[m.id] = 0
        return res

    _columns = {
        'pieces_qty': fields.integer('Pieces', states={'done': [('readonly', True)]}),
        'length': fields.float('Length (m)', digits_compute=dp.get_precision('Product UoM')),
        'width': fields.float('Width (m)', digits_compute=dp.get_precision('Product UoM')),
        'heigth': fields.float('Heigth (m)', digits_compute=dp.get_precision('Product UoM')),
    }

    _defaults = {
        'pieces_qty': lambda *a: 0,
    }

    def onchange_lot_id(self, cr, uid, ids, prodlot_id=False, product_qty=False,
                        loc_id=False, product_id=False, uom_id=False, context=None):
        res = super(stock_move, self).onchange_lot_id(cr, uid, ids, prodlot_id, product_qty,
                loc_id, product_id, uom_id, context)
        if prodlot_id and product_qty == 1:
            obj_lot = self.pool.get('stock.production.lot')
            lot = obj_lot.browse(cr, uid, prodlot_id, context=context)
            res.update({'value': {'product_id': lot.product_id.id,
                        'product_qty': lot.lot_factor,
                        'product_uos_qty': lot.lot_factor, 'pieces_qty': 1,
                        'length': lot.length, 'width': lot.width,
                        'heigth': lot.heigth}})
        return res

    def on_change_pieces_qty(self, cr, uid, ids, prodlot_id, pieces_qty):
        res = {}
        context = {}
        if prodlot_id and pieces_qty:
            obj_prd = self.pool.get('product.product')
            obj_lot = self.pool.get('stock.production.lot')
            obj_uom = self.pool.get('product.uom')
            lot = obj_lot.browse(cr, uid, prodlot_id, context=context)
            product = obj_prd.browse(cr, uid, lot.product_id.id, context=context)
            if product.stock_driver != 'normal':
                product_qty = obj_uom._compute_area(cr, uid, product.stock_driver,
                        pieces_qty, lot.length, lot.heigth, lot.width, context)
                res = {'value': {'product_qty': product_qty}}
        return res

    def create(self, cr, uid, vals, context=None):
        obj_sol = self.pool.get('sale.order.line')
        obj_pol = self.pool.get('purchase.order.line')
        obj_lot = self.pool.get('stock.production.lot')
        obj_uom = self.pool.get('product.uom')
        obj_prd = self.pool.get('product.product')
        if vals.get('product_id'):
            product = obj_prd.browse(cr, uid, vals['product_id'], context=context)
            #~ if product.track_outgoing and not vals.get('prodlot_id'):
                #~ raise osv.except_osv(_('Error!'), _('You must indicate a lot for product: %s')%product.name)
            if vals.get('sale_line_id'):
                sol = obj_sol.browse(cr, uid, vals['sale_line_id'],
                                     context=context)
                if sol.prod_lot_id:
                    vals.update({'prodlot_id': sol.prod_lot_id and sol.prod_lot_id.id,
                                 'pieces_qty': sol.pieces})
                    location_id = obj_lot.\
                                get_actual_lot_location(cr, uid,
                                                        sol.prod_lot_id.id)
                    if location_id and len(location_id) == 1:
                        vals.update({'location_id': location_id[0]})
            elif vals.get('purchase_line_id'):
                pol = obj_pol.browse(cr, uid, vals['purchase_line_id'],
                                     context=context)
                vals.update({'prodlot_id': pol.prod_lot_id and pol.prod_lot_id.id,
                             'pieces_qty': pol.pieces})
            if product.stock_driver != 'normal' and vals.get('prodlot_id'):
                lot = obj_lot.browse(cr, uid, vals['prodlot_id'], context=context)
                if not vals.get('pieces_qty'):
                    pieces_qty = obj_uom._compute_pieces(cr, uid, product.stock_driver,
                            vals.get('product_qty'), lot.lot_factor, context)
                    logger.warn('[stock.move] pieces_qty updated (%s)'%(vals))
                    vals.update({'pieces_qty': pieces_qty})
                product_qty = obj_uom._compute_area(cr, uid, product.stock_driver,
                        vals.get('pieces_qty'), lot.length, lot.heigth, lot.width, context)
                if abs(vals.get('product_qty')-product_qty) >= 0.0001:
                    logger.warn('[stock.move] the move area dosen\'t correspond with pcs*factor (%s)'%(vals))
        res = super(stock_move, self).create(cr, uid, vals, context)
        return res

    def write(self, cr, uid, ids, vals, context=None):

        if vals.get('product_qty') or vals.get('pieces_qty'):
            ids = isinstance(ids, (int, long)) and [ids] or ids
            for id in ids:
                so_brw = self.browse(cr, uid, id, context)
                obj_prd = self.pool.get('product.product')
                product_id = vals.get('product_id', so_brw.product_id.id)
                product = obj_prd.browse(cr, uid, product_id, context=context)
                if product.stock_driver != 'normal':
                    obj_lot = self.pool.get('stock.production.lot')
                    prodlot_id = vals.get('prodlot_id', so_brw.prodlot_id.id)
                    lot = obj_lot.browse(cr, uid, prodlot_id, context=context)
                    obj_uom = self.pool.get('product.uom')
                    if vals.get('product_qty') and not vals.get('pieces_qty'):
                        pieces_qty = obj_uom._compute_pieces(cr, uid, product.stock_driver,
                                vals.get('product_qty'), lot.lot_factor, context)
                        vals.update({'pieces_qty': pieces_qty})
                    elif vals.get('product_qty') and vals.get('pieces_qty'):
                        product_qty = obj_uom._compute_area(cr, uid, product.stock_driver,
                                vals.get('pieces_qty'), lot.length, lot.heigth,
                                lot.width, context)
                        if abs(vals.get('product_qty')-product_qty) >= 0.0001:
                            logger.warn('[stock.move] the move area dosen\'t ' +\
                                    'correspond with pcs*factor (%s)' % (vals))

        res = super(stock_move, self).write(cr, uid, ids, vals, context)
        return res

stock_move()


class stock_inventory(osv.osv):

    _inherit = 'stock.inventory'

    def _inventory_line_hook(self, cr, uid, inventory_line, move_vals):
        """
        Added to transfer pieces_qty to stock_move
        """
        if inventory_line.pieces_qty:
            move_vals.update({'pieces_qty': inventory_line.pieces_qty})
        return super(stock_inventory, self)._inventory_line_hook(cr, uid,
                inventory_line, move_vals)

stock_inventory()


class stock_inventory_line(osv.osv):
    """
    stock_inventory_line
    """
    _inherit = 'stock.inventory.line'

    def _compute_pieces(self, cr, uid, ids, name, arg, context=None):
        line = self.browse(cr, uid, ids)
        res = {}
        for l in line:
            if l.product_id.stock_driver in ('tile', 'slab', 'block'):
                uom = self.pool.get('product.uom')
                pieces = uom._compute_pieces(cr, uid, l.product_id.stock_driver,
                        l.product_qty, l.prod_lot_id.lot_factor, context)
                res[l.id] = pieces
            else:
                res[l.id] = 0
        return res

    _columns = {
        'pieces_qty': fields.function(_compute_pieces, method=True, type="integer", string='Pieces'),
        }

    def on_change_prod_lot(self, cr, uid, ids, prod_lot_id, product_qty):
        res = {}
        if prod_lot_id:
            lot = self.pool.get('stock.production.lot').browse(cr, uid, prod_lot_id, {})
            if lot.stock_driver in ('slab', 'block'):
                res =  {'value':{'product_qty': lot.lot_factor, 'pieces_qty': 1}}
            if lot.stock_driver in ('tile'):
                pc_qty = product_qty // lot.lot_factor
                res =  {'value':{'pieces_qty': pc_qty, 'product_qty': pc_qty * lot.lot_factor}}
        return res


    def on_change_product_qty(self, cr, uid, ids, product_id, product_qty):
        res = {}
        values = {}
        if product_id:
            prd = self.pool.get('product.product').browse(cr, uid, product_id, context=None)
            if prd.stock_driver in ('slab','block'):
                values.update({'pieces_qty':1})
            elif prd.stock_driver in ('tile'):
                pc_qty = product_qty // prd.tile_format_id.factile
                values.update({'pieces_qty': pc_qty,
                               'product_qty': pc_qty * prd.tile_format_id.factile})
            if values:
                res = {'value': values}
        return res

stock_inventory_line()


class stock_picking(osv.osv):

    def _invoice_line_hook(self, cr, uid, move_line, invoice_line_id):
        ail_obj = self.pool.get('account.invoice.line')
        ail_obj.write(cr, uid, invoice_line_id, {'prod_lot_id': move_line.prodlot_id and \
                move_line.prodlot_id.id, 'pieces': move_line.pieces_qty}, context=None)
        return super(stock_picking, self)._invoice_line_hook(cr, uid, move_line,
                invoice_line_id)

    _inherit = 'stock.picking'
    _columns = {
        'pieces_qty': fields.integer('Pieces'),

    }

stock_picking()
