# -*- encoding: utf-8 -*-
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

#import datetime
from osv import fields, osv
#~ import pooler
import decimal_precision as dp
from tools.translate import _

class stock_production_lot(osv.osv):

    _inherit = 'stock.production.lot'


    def _calc_lot_area(self, l, h, w):
        return self.pool.get('product.uom')._calc_area(l, h, w)

    def _call_full_name(self, name, l, h, w, drv='normal'):
        if drv in ('tile', 'slab'):
            extra_name = ' (%sx%s)' % (l, h)
        elif drv == 'block':
            extra_name = ' (%sx%sx%s)' % (l, h, w)
        else:
            extra_name = ''
        return '%s%s' % (name, extra_name.replace('.',','))

    def _calc_function_fields(self, cr, uid, ids, field_name, arg,
                              context=None):
        res = {}
        for item in self.browse(cr, uid, ids, context=context):
            entra = sale = 0.0
            for move in item.move_ids:
                if move.state != 'cancel':
                    if move.location_id.usage == 'internal':
                        if move.location_dest_id.usage != 'internal':
                            sale = sale + move.product_qty
                    if move.location_id.usage != 'internal':
                        if move.location_dest_id.usage in ('internal',
                                                           'transit'):
                            entra = entra + move.product_qty
            virtual = entra - sale
            lot_factor = self._calc_lot_area(item.length,
                                             item.heigth,
                                             item.width)
            full_name = self._call_full_name(item.name,
                                             item.length,
                                             item.heigth,
                                             item.width,
                                             item.stock_driver)
            res[item.id] = {'virtual': virtual,
                            'lot_factor': lot_factor,
                            'full_name': full_name}
        return res

    def on_change_size(self, cr, uid, ids, length, heigth, width):
        obj_uom = self.pool.get('product.uom')
        length, heigth, width = obj_uom.adjust_sizes(length, heigth, width)
        lot_factor = self._calc_lot_area(length, heigth, width)
        res = {'value': {'length': length,
                         'heigth': heigth,
                         'width': width,
                         'lot_factor': lot_factor}}
        return res

    def name_get(self, cr, uid, ids, context):
        res = []
        ids = isinstance(ids, (int, long)) and [ids] or ids
        for item in self.browse(cr, uid, ids, context={}):
            name = self._call_full_name(item.name,
                                        item.length,
                                        item.heigth,
                                        item.width,
                                        item.stock_driver)
            res.append((item.id, name))
        return res

    _columns = {
        'length': fields.float('Length (m)', digits_compute=dp.get_precision('Extra UOM data')),
        'width': fields.float('Width (m)', digits_compute=dp.get_precision('Extra UOM data')),
        'heigth': fields.float('Heigth (m)', digits_compute=dp.get_precision('Extra UOM data')),
        'lot_factor': fields.function(_calc_function_fields, method=True, type="float", string='Lot Factor', digits_compute=dp.get_precision('Product UoM'), multi='all'),
        'virtual': fields.function(_calc_function_fields, method=True, type="float", string='Virtual', digits_compute=dp.get_precision('Product UoM'), multi='all'),
        'full_name': fields.function(_calc_function_fields, method=True, type="char", string='Name', multi='all'),
        'stock_driver': fields.related('product_id', 'stock_driver',
                                       type='char', size=12,
                                       relation='product.product'),
        'layout_id':fields.related('product_id','layout_id', type='many2one', relation='product.product.features', string='Layout', store=True, readonly=True, domain=[('type','=','layout')]),
    }

    _defaults = {
        'length': 0.0,
        'width': 0.0,
        'heigth': 0.0,
        'stock_driver': lambda *a: 'normal',
    }

    _sql_constraints = [
        ('length_gt_zero', 'CHECK (length>=0)', 'The length must be >= 0!'),
        ('heigth_gt_zero', 'CHECK (heigth>=0)', 'The heigth must be >= 0!'),
        ('width_gt_zero', 'CHECK (width>=0)', 'The width must be >= 0!'),
        ('length_gt_heigth', 'CHECK (length>=heigth)', 'The length must be >= heigth!'),
        ('name_ref_uniq', 'unique (name, ref, product_id)', 'The combination of product, serial number and internal reference must be unique !'),
        ('lot_uniq', 'unique (name, product_id)', 'The combination of product, serial number and internal reference must be unique !'),
    ]

    def on_change_product_id(self, cr, uid, ids, prd_id):
        res = {}
        if prd_id:
            prod = self.pool.get('product.product').browse(cr, uid, prd_id, {})
            data = {'stock_driver': prod.stock_driver}
            if prod.stock_driver in ('tile','slab'):
                data.update({'width': 0})
            if prod.stock_driver == 'tile':
                data.update({'length': prod.tile_format_id.length,
                             'heigth': prod.tile_format_id.heigth,
                             'lot_factor': prod.tile_format_id.factile})
            res = {'value': data}
        return res

    def validate_format(self, cr, uid, vals, context=None):
        if vals.get('product_id'):
            prod = self.pool.get('product.product').\
                browse(cr, uid, vals['product_id'])
            if prod.stock_driver in ('tile','slab'):
                vals.update({'width': 0})
                if prod.stock_driver == 'tile':
                    vals.update({'length': prod.tile_format_id.length,
                                 'heigth': prod.tile_format_id.heigth,
                                 'lot_factor': prod.tile_format_id.factile})
                elif prod.stock_driver == 'slab':
                    if vals.get('length') >= 4 or vals.get('heigth') >= 4:
                        raise osv.except_osv(_('Error!'), _('Length or heigth > 4 (%sx%s)') %
                                             (vals.get('length'), vals.get('heigth')))
        return vals

    def create(self, cr, uid, vals, context=None):
        self.validate_format(cr, uid, vals, context=context)
        return super(stock_production_lot, self).create(cr, uid, vals, context)

    def write(self, cr, uid, ids, vals, context=None):
        self.validate_format(cr, uid, vals, context=context)
        res = super(stock_production_lot, self).write(cr, uid, ids, vals, context)
        return res

stock_production_lot()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
