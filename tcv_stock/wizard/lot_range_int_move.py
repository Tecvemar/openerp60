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

##---------------------------------------------------------- lot_range_int_move


class lot_range_int_move(osv.osv_memory):

    _name = 'lot.range.int.move'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'type': fields.selection(
            [('range', 'Range'), ('location', 'Location'),
             ('bundle', 'Bundle')],
            string='Type', required=True),
        'location_id': fields.many2one(
            'stock.location', 'Location', ondelete='restrict'),
        'prod_lot_id': fields.many2one(
            'stock.production.lot', 'First lot', required=False),
        'bundle_id': fields.many2one(
            'tcv.bundle', 'Bundle', required=False,
            domain=[('reserved', '=', False)]),
        'product_id': fields.related(
            'prod_lot_id', 'product_id', type='many2one',
            relation='product.product', string='Product',
            store=False, readonly=True),
        'item_qty': fields.integer(
            'Lot\'s qty', required=True),
        'date': fields.date(
            'Date'),
        'location_dest_id': fields.many2one(
            'stock.location', 'Destination Location', readonly=False,
            ondelete='restrict', required=True,
            help="Location where the system will stock the finished " +
            "products."),
        }

    _defaults = {
        'item_qty': 10,
        'type': lambda *a: 'location',
        }

    _sql_constraints = [
        ('item_qty_range', 'CHECK(item_qty between 1 and 99)',
         'The Lot\'s qty must be in 1-99 range!'),
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    def create_lines_by_range(self, cr, uid, ids, lot_rng, context=None):
        lines = []
        obj_lot = self.pool.get('stock.production.lot')
        obj_wiz = self.pool.get('tcv.internal.move.wiz.lines')
        lot_int = int(lot_rng.prod_lot_id.name)
        lot_names = map(lambda x: str(x),
                        range(lot_int, lot_int + lot_rng.item_qty))
        for lot_name in lot_names:
            lot_ids = obj_lot.search(
                cr, uid, [('name', 'ilike', lot_name)])
            for lot in obj_lot.browse(cr, uid, lot_ids, context={}):
                data = obj_wiz.get_lot_data(
                    cr, uid, ids, lot.id, context=None)
                data.update(
                    {'location_dest_id': lot_rng.location_dest_id.id,
                     })
                lines.append((0, 0, data))
        return lines

    def create_lines_by_location(self, cr, uid, ids, lot_rng, context=None):
        lines = []
        obj_loc = self.pool.get('tcv.stock.by.location.report')
        obj_wiz = self.pool.get('tcv.internal.move.wiz.lines')
        loc_data_id = obj_loc.create(
            cr, uid,
            {'location_id': lot_rng.location_id.id,
             'date': lot_rng.date,
             }, context)
        obj_loc.button_load_inventory(cr, uid, loc_data_id, context=context)
        loc_brw = obj_loc.browse(cr, uid, loc_data_id, context=context)
        for line in loc_brw.line_ids:
            data = obj_wiz.get_lot_data(
                cr, uid, ids, line.prod_lot_id.id, context=None)
            data.update(
                {'location_dest_id': lot_rng.location_dest_id.id,
                 })
            lines.append((0, 0, data))
        return lines

    def create_lines_by_bundle(self, cr, uid, ids, lot_rng, context=None):
        lines = []
        obj_wiz = self.pool.get('tcv.internal.move.wiz.lines')
        for line in lot_rng.bundle_id.line_ids:
            data = obj_wiz.get_lot_data(
                cr, uid, ids, line.prod_lot_id.id, context=None)
            data.update(
                {'location_dest_id': lot_rng.location_dest_id.id,
                 })
            lines.append((0, 0, data))
        return lines

    def create_wizard_lines(self, cr, uid, ids, lot_rng, context=None):
        lines = []
        if lot_rng.type == 'range' and lot_rng.prod_lot_id.name.isdigit() \
                and lot_rng.item_qty:
            lines = self.create_lines_by_range(
                cr, uid, ids, lot_rng, context=context)
        elif lot_rng.type == 'location':
            lines = self.create_lines_by_location(
                cr, uid, ids, lot_rng, context=context)
        elif lot_rng.type == 'bundle':
            lines = self.create_lines_by_bundle(
                cr, uid, ids, lot_rng, context=context)
        return lines

    ##-------------------------------------------------------- buttons (object)

    def button_done(self, cr, uid, ids, context=None):
        context = context or {}
        ids = isinstance(ids, (int, long)) and [ids] or ids
        if context.get('active_model') == 'tcv.internal.move.wiz' and \
                context.get('active_ids'):
            lot_rng = self.browse(cr, uid, ids, context={})[0]
            obj_wiz = self.pool.get('tcv.internal.move.wiz')
            #~ obj_brw = obj_wiz.browse(cr, uid, ids[0], context=context)
            lines = self.create_wizard_lines(
                cr, uid, ids, lot_rng, context=context)
            if lines:
                obj_wiz.write(cr, uid, context.get('active_ids'),
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

    def on_change_bundle_id(self, cr, uid, ids, bundle_id):
        res = {}
        if bundle_id:
            obj_bun = self.pool.get('tcv.bundle')
            bun = obj_bun.browse(cr, uid, bundle_id, context=None)
            if bun.location_id:
                res.update({'location_dest_id': bun.location_id.id})
        return {'value': res}

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

lot_range_int_move()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
