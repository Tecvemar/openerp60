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
#~ ###########################################################################

from osv import fields, osv
import decimal_precision as dp
import time
from tools.translate import _


class stock_move(osv.osv):

    _inherit = 'stock.move'

    def _check_uom(self, cursor, user, ids, context=None):
        for move in self.browse(cursor, user, ids, context=context):
            product = self.pool.get('product.product').\
                browse(cursor, user, move.product_id.id, context=context)
            if product.uom_id.category_id.id != \
                    move.product_uom.category_id.id:
                return False
        return True

    _constraints = [
        (_check_uom,
         'Error: The move UOM and the product UOM must be in the same category.',
         ['product_uom']),
        ]
    _sql_constraints = [
        ('same_location', 'CHECK (location_id != location_dest_id)',
         'The origin and destination location can\'t be the same'),
        ]


stock_move()


class stock_inventory_line(osv.osv):

    _inherit = 'stock.inventory.line'

    def _check_uom(self, cursor, user, ids, context=None):
        for line in self.browse(cursor, user, ids, context=context):
            product = self.pool.get('product.product').\
                browse(cursor, user, line.product_id.id, context=context)
            if product.uom_id.category_id.id != \
                    line.product_uom.category_id.id:
                return False
        return True

    _constraints = [
        (_check_uom,
         'Error: The line UOM and the product UOM must be in the same category.',
         ['product_uom']),
    ]


stock_inventory_line()

##-------------------------------------------------------- stock_production_lot


class stock_production_lot(osv.osv):

    _inherit = 'stock.production.lot'

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'property_cost_price': fields.property(
            'product.template',
            type='float',
            string="Cost Price (multicompany)",
            method=True,
            view_load=True,
            digits_compute=dp.get_precision('Purchase Price'),
            help="Lot's cost for accounting stock valuation in multicompany environments."),
        'sale_lines_ids': fields.one2many(
            'sale.order.line', 'prod_lot_id',
            help="Sale orders lines for this production lot", readonly=True),
        'invoice_lines_ids': fields.one2many(
            'account.invoice.line', 'prod_lot_id',
            help="Invoice lines for this production lot", readonly=True),
        }

    ##-----------------------------------------------------

    ##----------------------------------------------------- public methods

    def get_actual_lot_location(self, cr, uid, prod_lot_id, context=None):
        """ Gets stock actual location
        @return: location_id
        """
        ids = []
        if context is None:
            context = {}
        #~ cr.execute('''
            #~ select location_id, sum(qty)
            #~ from stock_report_prodlots
            #~ where prodlot_id = %s
            #~ group by location_id
            #~ having  sum(qty) > 0
            #~ ''' % prod_lot_id)
        cr.execute('''
            select s.location_id, sum(s.qty)
            from stock_report_prodlots s
            left join stock_location l on s.location_id = l.id
            where prodlot_id = %s and l.scrap_location = False
            group by s.location_id
            having  sum(s.qty) > 0
            ''' % prod_lot_id)
        res = cr.fetchall()
        if res:
            ids = map(lambda x: x[0], res)
        return ids

    def copy(self, cr, uid, id, default=None, context=None):
        default = default or {}
        lot = self.browse(cr, uid, id, context=context)
        if lot.name.isdigit():
            name = '%s' % (int(lot.name) + 1)
            while len(lot.name) > len(name):
                name = '0%s' % name
        else:
            name = self.pool.get('ir.sequence').get(
                cr, uid, 'stock.lot.serial'),
        default.update({
            'name': name,
            'property_cost_price': lot.property_cost_price,
            'move_ids': [],
            'sale_lines_ids': [],
            'invoice_lines_ids': [],
            })
        res = super(stock_production_lot, self).copy(
            cr, uid, id, default, context)
        return res

    ##----------------------------------------------------- buttons (object)

    ##----------------------------------------------------- on_change...

    ##----------------------------------------------------- create write unlink

    ##----------------------------------------------------- Workflow


stock_production_lot()


##--------------------------------------------------------------- stock_picking


class stock_picking(osv.osv):

    _inherit = 'stock.picking'

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'driver_id': fields.many2one('tcv.driver.vehicle', 'Driver',
                                     ondelete='restrict',
                                     domain="[('type','=','driver')]"),
        'vehicle_id': fields.many2one('tcv.driver.vehicle', 'Vehicle',
                                      ondelete='restrict',
                                      domain="[('type','=','vehicle')]"),
        'container': fields.char(
            'Container', size=16, required=False, readonly=False),
        }

    _defaults = {
        }

    _sql_constraints = [
        ]

    ##-----------------------------------------------------

    ##----------------------------------------------------- public methods

    def copy(self, cr, uid, id, default=None, context=None):

        def set_additonal_move_line_data(pick_brw, new_pick_id):
            field = ''
            if pick_brw.type == 'out':
                field = 'sale_line_id'
            elif pick_brw.type == 'in':
                field = 'purchase_line_id'
            if not field:
                return False
            obj_mov = self.pool.get('stock.move')
            for org_move in pick_brw.move_lines:
                if org_move[field]:
                    move_id = obj_mov.search(
                        cr, uid, [('picking_id', '=', new_pick_id),
                                  (field, '=', org_move[field].id)])
                    if move_id and len(move_id) == 1:
                        values = {
                            'origin': org_move.origin,
                            'prodlot_id': org_move.prodlot_id and
                            org_move.prodlot_id.id or 0,
                            }
                        obj_mov.write(
                            cr, uid, move_id, values, context=context)
            return True

        default = default or {}
        new_pick_id = super(stock_picking, self).copy(
            cr, uid, id, default, context)
        pick_brw = self.browse(cr, uid, id, context=context)
        if new_pick_id and pick_brw.state == 'cancel':
            #~ Copy additional data when original picking is cancelled
            data = {
                'origin': '%s-%s' % (pick_brw.origin, pick_brw.name),
                'backorder_id': pick_brw.id,
                'note': '%s%s' % (
                    pick_brw.note and pick_brw.note + '\n' or '',
                    _('Copy of: %s') % pick_brw.name)
                }
            self.write(cr, uid, [new_pick_id], data, context=context)
            set_additonal_move_line_data(pick_brw, new_pick_id)
        return new_pick_id

    ##----------------------------------------------------- buttons (object)

    ##----------------------------------------------------- on_change...

    ##----------------------------------------------------- create write unlink

    ##----------------------------------------------------- Workflow


stock_picking()


##-------------------------------------------------------------- stock_tracking


class stock_tracking(osv.osv):

    _inherit = 'stock.tracking'

    _columns = {
        'weight_net': fields.float(
            'Weight net', digits_compute=dp.get_precision('Account')),
        'image': fields.binary("Image", help="Select image here"),
        }

    _defaults = {
        'active': 1,
        'name': lambda obj, cr, uid, context: obj.pool.get('ir.sequence').
        get(cr, uid, 'stock.lot.tracking'),
        'date': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
    }

    ##------------------------------------------------------- _internal methods


stock_tracking()
