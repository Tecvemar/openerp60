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


##------------------------------------------------------- tcv_purchase_lot_list

class tcv_purchase_lot_list(osv.osv_memory):

    _name = 'tcv.purchase.lot.list'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'name': fields.char('Name', size=64, required=False, readonly=False),
        'pricelist_id': fields.many2one('product.pricelist', 'Pricelist'),
        'line_ids': fields.one2many('tcv.purchase.lot.list.lines', 'line_id',
                                    'Lines'),
        }

    _defaults = {
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    #~ def create_order_lines(self, cr, uid, ids, lot_list, context=None):

    ##-------------------------------------------------------- buttons (object)

    def button_done(self, cr, uid, ids, context=None):
        if context.get('purchase_order_id'):
            ids = isinstance(ids, (int, long)) and [ids] or ids
            obj_ord = self.pool.get('purchase.order')
            obj_lot = self.pool.get('stock.production.lot')
            so_brw = self.browse(cr, uid, ids, context={})[0]
            lots = []
            lines = []
            for item in so_brw.line_ids:
                if item.product_id and item.lot_name and item.product_qty and \
                   item.price_unit:
                    lot = {'product_id': item.product_id.id,
                           'name': item.lot_name,
                           'length': item.length,
                           'heigth': item.heigth,
                           'width': item.width,
                           'pieces': item.pieces}
                    lot_id = obj_lot.create(cr, uid, lot, context)
                    lot.update({'lot_id': lot_id})
                    lots.append(lot)
                    taxes = []
                    for tax in item.product_id.supplier_taxes_id:
                        taxes.append((4, tax.id))
                    data = {'product_id': item.product_id.id,
                            'concept_id': item.product_id.concept_id.id,
                            'prod_lot_id': lot_id,
                            'pieces': item.pieces,
                            'product_qty': item.product_qty,
                            'product_uom': item.product_id.uom_id.id,
                            'name': '[%s] %s' % (item.product_id.default_code,
                                                 item.product_id.name),
                            'price_unit': item.price_unit,
                            'date_planned': time.strftime('%Y-%m-%d'),
                            'taxes_id': taxes,
                            }
                    lines.append((0, 0, data))
            if lines:
                obj_ord.write(cr, uid,
                              context.get('purchase_order_id'),
                              {'order_line': lines}, context)
        return {'type': 'ir.actions.act_window_close'}

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_purchase_lot_list()

##------------------------------------------------- tcv_purchase_lot_list_lines


class tcv_purchase_lot_list_lines(osv.osv_memory):

    _name = 'tcv.purchase.lot.list.lines'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def _compute_values(self, cr, uid, data, roundto=2):
        '''
        data = {'stock_driver': ,
                'pieces': ,
                'length': ,
                'heigth': ,
                'width': ,
                'price_unit':}
        return data.update({'product_qty': ,
                            'sub_total': })
        '''
        obj_uom = self.pool.get('product.uom')
        qty = obj_uom._compute_area(cr, uid,
                                    data.get('stock_driver', 'normal'),
                                    data.get('pieces', 0),
                                    data.get('length', 0),
                                    data.get('heigth', 0),
                                    data.get('width', 0))
        data.update({'product_qty': qty,
                     'sub_total': round(qty * data.get('price_unit', 0),
                                        roundto)})
        return data

    def _compute_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for item in self.browse(cr, uid, ids, context=context):
            data = {'stock_driver': item.stock_driver,
                    'pieces': item.pieces,
                    'length': item.length,
                    'heigth': item.heigth,
                    'width': item.width,
                    'price_unit': item.price_unit}
            res[item.id] = self._compute_values(cr, uid, data)
        return res

    def default_get(self, cr, uid, fields, context=None):
        last_line = False
        if context.get('lot_lines'):
            last_line = context['lot_lines'][-1][2]
        data = super(tcv_purchase_lot_list_lines, self).\
            default_get(cr, uid, fields, context)
        if last_line:
            next_lot = last_line['lot_name']
            try:
                if 'BL-' in next_lot:
                    next_lot = 'BL-%s' % (int(next_lot.split('-')[1]) + 1)
                else:
                    next_lot = '%s' % (int(next_lot) + 1)
                last_line.update({'lot_name': next_lot})
            except:
                pass
            data.update(last_line)
        return data

    ##--------------------------------------------------------- function fields

    _columns = {
        'line_id': fields.many2one('tcv.purchase.lot.list', 'line',
                                   required=True, ondelete='cascade'),
        'product_id': fields.many2one('product.product', 'Product',
                                      ondelete='restrict', required=True),
        'stock_driver': fields.related('product_id', 'stock_driver',
                                       type='char', size=12,
                                       relation='product.product'),
        'lot_name': fields.char('Production lot', size=64, required=True,
                                readonly=False),
        'length': fields.float('Length (m)', digits_compute=dp.get_precision('Extra UOM data')),
        'width': fields.float('Width (m)', digits_compute=dp.get_precision('Extra UOM data')),
        'heigth': fields.float('Heigth (m)', digits_compute=dp.get_precision('Extra UOM data')),
        'pieces': fields.integer('Pieces'),
        'product_qty': fields.function(_compute_all, method=True, type='float',
                                       string='Quantity',
                                       digits_compute=dp.get_precision('Product UoM'),
                                       multi='all'),
        'price_unit': fields.float('Unit price',
                                   digits_compute=dp.get_precision('Account'),
                                   readonly=False),
        'sub_total': fields.function(_compute_all, method=True, type='float',
                                     string='Total amount',
                                     digits_compute=dp.get_precision('Account'),
                                     multi='all'),

        }

    _defaults = {
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    def on_change_product_id(self, cr, uid, ids, product_id):
        res = {}
        if not product_id:
            return res
        obj_prd = self.pool.get('product.product')
        product = obj_prd.browse(cr, uid, product_id, context={})
        res.update({'stock_driver': product.stock_driver})
        if product.stock_driver == 'tile':
            res.update({'length': product.tile_format_id.length,
                        'heigth': product.tile_format_id.heigth,
                        'width': 0,
                        'pieces': 1})
            self._compute_values(cr, uid, res)
        elif product.stock_driver in ('slab', 'block'):
            res.update({'pieces': 1})

        return {'value': res}

    def on_change_lot_name(self, cr, uid, ids, prd_id, stock_driver, lot_name):
        res = {}
        if prd_id and lot_name:
            lot_name = lot_name.upper()
            if stock_driver == 'block' and not 'BL-' in lot_name:
                lot_name = 'BL-%s' % lot_name
            res.update({'lot_name': lot_name.upper()})
            obj_lot = self.pool.get('stock.production.lot')
            lot_ids = obj_lot.search(cr, uid, [('name', '=', lot_name),
                                               ('product_id', '=', prd_id)])
            if lot_ids:
                return {'warning': {'title': 'Warning',
                                    'message': _('The lot: "%s" already exits')
                                    % lot_name},
                        'value': {'lot_name': ''}}
        return {'value': res}

    def on_change_size(self, cr, uid, ids, stock_driver, length, heigth, width,
                       pieces, price_unit):
        res = {}
        obj_uom = self.pool.get('product.uom')
        length, heigth, width = obj_uom.adjust_sizes(length, heigth, width)
        res.update({'stock_driver': stock_driver,
                    'length': length,
                    'heigth': heigth,
                    'width': width,
                    'pieces': pieces,
                    'price_unit': price_unit})
        self._compute_values(cr, uid, res)
        return {'value': res}

    ##----------------------------------------------------- create write unlink

    def create(self, cr, uid, vals, context=None):
        if vals.get('stock_driver') and vals.get('product_id'):
            obj_prd = self.pool.get('product.product')
            product = obj_prd.browse(cr, uid, vals['product_id'], context={})
            if vals['stock_driver'] == 'tile':
                vals.update({'length': product.tile_format_id.length,
                             'heigth': product.tile_format_id.heigth})
            elif vals['stock_driver'] in ('slab', 'block'):
                vals.update({'pieces': 1})
        res = super(tcv_purchase_lot_list_lines, self).\
            create(cr, uid, vals, context)
        return res

    ##---------------------------------------------------------------- Workflow

tcv_purchase_lot_list_lines()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
