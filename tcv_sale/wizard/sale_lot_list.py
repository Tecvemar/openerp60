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
import decimal_precision as dp
import time
#~ import netsvc


##----------------------------------------------------------- tcv_sale_lot_list

class tcv_sale_lot_list(osv.osv_memory):

    _name = 'tcv.sale.lot.list'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'name': fields.char(
            'Name', size=64, required=False, readonly=False),
        'line_ids': fields.one2many(
            'tcv.sale.lot.list.lines', 'line_id', 'Lines'),
        'sale_id': fields.many2one(
            'sale.order', 'Sales Order', ondelete='restrict', select=True,
            readonly=True),
        'partner_id': fields.many2one(
            'res.partner', 'Partner', readonly=True, ondelete='restrict'),
        }

    _defaults = {
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    def button_refresh(self, cr, uid, ids, context=None):
        obj_lin = self.pool.get('tcv.sale.lot.list.lines')
        ids = isinstance(ids, (int, long)) and [ids] or ids
        for item in self.browse(cr, uid, ids, context={}):
            for line in item.line_ids:
                res = obj_lin.on_change_prod_lot_id(
                    cr, uid, line.id, line.prod_lot_id.id, 0, 0)
                data = res.get('value', {})
                if line.pieces:
                    data.update({'pieces': line.pieces})
                obj_lin.write(cr, uid, [line.id], data, context=context)
        return True

    def button_done(self, cr, uid, ids, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        obj_ord = self.pool.get('sale.order')
        obj_col = self.pool.get('tcv.sale.data.collector')
        brw = self.browse(cr, uid, ids, context={})[0]
        duplicated = []
        #~ Add Actual order lots to duplicated
        for item in brw.sale_id.order_line:
            if item.prod_lot_id and item.prod_lot_id.id:
                duplicated.append(item.prod_lot_id.id)
        if brw.sale_id:
            if brw.sale_id.state != 'draft':
                raise osv.except_osv(
                    _('Error!'),
                    _('Can\'t add lines when state <> "draft"'))
            if brw.sale_id.date_due < time.strftime('%Y-%m-%d'):
                raise osv.except_osv(
                    _('Error!'),
                    _('Can\'t update an order while date due is < today'))
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
                    obj_ord.write(cr, uid, brw.sale_id.id,
                                  {'order_line': lines}, context)
        return {'type': 'ir.actions.act_window_close'}

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow


tcv_sale_lot_list()


##----------------------------------------------------- tcv_sale_lot_list_lines


class tcv_sale_lot_list_lines(osv.osv_memory):

    _name = 'tcv.sale.lot.list.lines'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def _compute_sub_total(self, product_qty, price_unit, roundto=2):
        return round(product_qty * price_unit, roundto)

    def _compute_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for item in self.browse(cr, uid, ids, context=context):
            res[item.id] = {'sub_total': self._compute_sub_total(
                            item.product_qty, item.price_unit)}
        return res

    ##--------------------------------------------------------- function fields

    _columns = {
        'line_id': fields.many2one('tcv.sale.lot.list', 'line', required=True,
                                   ondelete='cascade'),
        'prod_lot_id': fields.many2one('stock.production.lot',
                                       'Production lot', required=True),
        'product_id': fields.related('prod_lot_id', 'product_id',
                                     type='many2one',
                                     relation='product.product',
                                     string='Product',
                                     store=False, readonly=True),
        'max_pieces': fields.integer('available pcs', readonly=True),
        'pieces': fields.integer('Pieces'),
        'product_qty': fields.float(
            'Quantity', digits_compute=dp.get_precision('Product UoM'),
            readonly=True),
        'price_unit': fields.float(
            'Unit price', digits_compute=dp.get_precision('Account'),
            readonly=True),
        'sub_total': fields.function(
            _compute_all, method=True, type='float', string='Total amount',
            digits_compute=dp.get_precision('Account'), multi='all'),
        }

    _defaults = {
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    def on_change_prod_lot_id(self, cr, uid, ids, prod_lot_id, pieces,
                              max_pieces):
        res = {}
        if not prod_lot_id:
            return res
        obj_lot = self.pool.get('stock.production.lot')
        obj_uom = self.pool.get('product.uom')
        obj_ord = self.pool.get('sale.order.line')
        obj_prd = self.pool.get('product.product')
        lot = obj_lot.browse(cr, uid, prod_lot_id, context=None)
        if not pieces:
            product_qty = lot.stock_available
            pieces = obj_uom._compute_pieces(
                cr, uid, lot.product_id.stock_driver,
                product_qty, lot.lot_factor, context=None)
            max_pieces = pieces
        else:
            if pieces <= 0:
                pieces = 1
            elif pieces > max_pieces:
                pieces = max_pieces
            product_qty = obj_uom._calc_area(pieces, lot.lot_factor)
        #~ price_unit = lot.product_id.property_list_price
        price_unit = obj_prd.get_property_list_price(
            cr, uid, lot.product_id, lot, None)
        res.update({'product_id': lot.product_id.id,
                    'max_pieces': max_pieces,
                    'pieces': pieces,
                    'product_qty': product_qty,
                    'price_unit': price_unit,
                    'sub_total': self._compute_sub_total(product_qty,
                                                         price_unit)})
        res = {'value': res}
        res.update(obj_ord.warning_on_prod_lot_id_used(cr, uid, [],
                                                       prod_lot_id))
        return res

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow


tcv_sale_lot_list_lines()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
