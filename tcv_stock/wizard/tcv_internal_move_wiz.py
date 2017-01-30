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
from tools.translate import _
#~ import pooler
import decimal_precision as dp
import time
#~ import netsvc

##------------------------------------------------------- tcv_internal_move_wiz


class tcv_internal_move_wiz(osv.osv_memory):

    _name = 'tcv.internal.move.wiz'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def default_get(self, cr, uid, fields, context=None):
        data = super(tcv_internal_move_wiz, self).\
            default_get(cr, uid, fields, context)
        if context.get('active_model') == u'stock.picking' and \
                context.get('active_id'):
            data.update({'picking_id': context.get('active_id')})
        return data

    ##--------------------------------------------------------- function fields

    _columns = {
        'date': fields.date(
            'Date', required=True, readonly=True,
            states={'draft': [('readonly', False)]}, select=True),
        'name': fields.char(
            'Name', size=64, required=False, readonly=False),
        'line_ids': fields.one2many(
            'tcv.internal.move.wiz.lines', 'line_id', 'Lines'),
        'picking_id': fields.many2one(
            'stock.picking', 'Picking', ondelete='restrict', readonly=True),
        }

    _defaults = {
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        'ignore_error': lambda *a: False,
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    def button_done(self, cr, uid, ids, context=None):
        obj_mov = self.pool.get('stock.move')
        obj_pic = self.pool.get('stock.picking')
        for item in self.browse(cr, uid, ids, context={}):
            for line in item.line_ids:
                if line.status != 'ok':
                    raise osv.except_osv(
                        _('Error!'),
                        _('Can\'t process lines when status <> Ok'))
                pieces = 0 if line.product_id.stock_driver == 'normal' else \
                    int((line.product_qty /
                         line.prod_lot_id.lot_factor) + 0.000000001)
                data = {
                    'name': item.picking_id.name,
                    'date': item.date,
                    'date_expected': item.date,
                    'product_id': line.product_id.id,
                    'product_uom': line.product_id.uom_id.id,
                    'product_qty': line.product_qty,
                    'location_id': line.location_id.id,
                    'location_dest_id': line.location_dest_id.id,
                    'prodlot_id': line.prod_lot_id.id,
                    'picking_id': item.picking_id.id,
                    'state': 'draft',
                    'pieces': pieces,
                    }
                #~ tipo picking
                if line.prod_lot_id and line.location_dest_id and \
                        line.location_id.id != line.location_dest_id.id:
                    obj_mov.create(cr, uid, data, context)
            obj_pic.write(cr, uid, [item.picking_id.id],
                          {'date': item.date,
                           'date_done': item.date,
                           'min_date': item.date,
                           'origin': item.name,
                           'stock_journal_id': 4,
                           },
                          context=context)
        return {'type': 'ir.actions.act_window_close'}

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_internal_move_wiz()


##------------------------------------------------- tcv_internal_move_wiz_lines


class tcv_internal_move_wiz_lines(osv.osv_memory):

    _name = 'tcv.internal.move.wiz.lines'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'line_id': fields.many2one(
            'tcv.internal.move.wiz', 'Wizard', required=True,
            ondelete='cascade'),
        'prod_lot_id': fields.many2one(
            'stock.production.lot', 'Production lot', required=False),
        'product_id': fields.related(
            'prod_lot_id', 'product_id', type='many2one',
            relation='product.product', string='Product',
            store=False, readonly=True),
        'product_qty': fields.float(
            'Quantity', digits_compute=dp.get_precision('Product UoM'),
            readonly=True),
        'location_id': fields.many2one(
            'stock.location', 'Source Location', readonly=True,
            ondelete='restrict',
            help="Sets a location if you produce at a fixed location. " +
            "This can be a partner location if you subcontract the " +
            "manufacturing operations."),
        'location_dest_id': fields.many2one(
            'stock.location', 'Destination Location', readonly=False,
            ondelete='restrict',
            help="Location where the system will stock the finished " +
            "products."),
        'status': fields.selection(
            [('ok', 'Ok'), ('error1', 'Move error '),
             ('error2', 'Location error')],
            string='Status', required=True, readonly=True),
        'manual': fields.boolean('manual'),
        'move_ids': fields.related(
            'prod_lot_id', 'move_ids', type='one2many', relation='stock.move',
            string='Moves for this lot', store=False, readonly=True),
        }

    _defaults = {
        'status': lambda *a: 'ok',
        'manual': lambda *a: False,
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    def get_lot_data(self, cr, uid, ids, prod_lot_id, context=None):
        context = context or {}
        obj_lot = self.pool.get('stock.production.lot')
        lot_brw = obj_lot.browse(cr, uid, prod_lot_id, context={})
        location_id = obj_lot.get_actual_lot_location(
            cr, uid, prod_lot_id, context=None)
        status = 'ok'
        for move in lot_brw.move_ids:
            if move.state not in ('done', 'cancel'):
                status = 'error1'
        if len(location_id) != 1:
            status = 'error2'
        if context.get('data_vals') and context['data_vals'].get('manual') \
                and context['data_vals'].get('status'):
            status = context['data_vals'].get('status')
        return {'prod_lot_id': lot_brw.id,
                'product_id': lot_brw.product_id.id,
                'product_qty': lot_brw.stock_available,
                'location_id': location_id and location_id[0] or 0,
                'status': status,
                }

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    def on_change_prod_lot_id(self, cr, uid, ids, prod_lot_id):
        res = {}
        if not prod_lot_id:
            return res
        res = self.get_lot_data(cr, uid, ids, prod_lot_id, context=None)
        res = {'value': res}
        return res

    def on_change_status(self, cr, uid, ids, location_id, status):
        res = {}
        if not status:
            return res
        res.update({'manual': True, 'status': 'ok'})
        res = {'value': res}
        return res

    ##----------------------------------------------------- create write unlink

    def create(self, cr, uid, vals, context=None):
        context = context or {}
        context.update({'data_vals': vals})
        if vals.get('prod_lot_id'):
            vals.update(self.get_lot_data(cr, uid, [], vals['prod_lot_id'],
                                          context=context))
        res = super(tcv_internal_move_wiz_lines, self).\
            create(cr, uid, vals, context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        context = context or {}
        context.update({'data_vals': vals})
        if vals.get('prod_lot_id'):
            vals.update(self.get_lot_data(cr, uid, ids, vals['prod_lot_id'],
                                          context=context))
        res = super(tcv_internal_move_wiz_lines, self).\
            write(cr, uid, ids, vals, context)
        return res

    ##---------------------------------------------------------------- Workflow

tcv_internal_move_wiz_lines()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
