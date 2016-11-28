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
#~ import decimal_precision as dp
#~ import time
#~ import netsvc

##----------------------------------------------------- tcv_split_stock_picking


class tcv_split_stock_picking(osv.osv_memory):

    _name = 'tcv.split.stock.picking'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def default_get(self, cr, uid, fields, context=None):
        data = super(tcv_split_stock_picking, self).\
            default_get(cr, uid, fields, context)
        if context.get('active_model') == u'stock.picking' and \
                context.get('active_id'):
            pic_id = context.get('active_id')
            obj_pic = self.pool.get('stock.picking')
            pic_brw = obj_pic.browse(cr, uid, pic_id, context=context)
            line_ids = []
            for move in pic_brw.move_lines:
                if move.state not in ('done', 'cancel'):
                    line_ids.append({
                        'move_id': move.id,
                        'product_id': move.product_id.id,
                        'prod_lot_id': move.prodlot_id.id,
                        'selected': False,
                        })
            if pic_brw.state not in ('done', 'cancel'):
                data.update({'picking_id': pic_id,
                             'line_ids': line_ids})
        return data

    ##--------------------------------------------------------- function fields

    _columns = {
        'picking_id': fields.many2one(
            'stock.picking', 'Picking', ondelete='restrict', readonly=True),
        'line_ids': fields.one2many(
            'tcv.split.stock.picking.lines', 'line_id', 'String'),
        }

    _defaults = {
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
            move_lines_ids = []
            lines_moved_ids = []
            for line in item.line_ids:
                if line.selected:
                    move_lines_ids.append(line.move_id.id)
                else:
                    lines_moved_ids.append(line.move_id.id)
            if not move_lines_ids or not lines_moved_ids:
                raise osv.except_osv(
                    _('Error!'),
                    _('Must select at lest one move'))
            new_pic = {
                'origin': item.picking_id.origin,
                'address_id': item.picking_id.address_id.id,
                'min_date': item.picking_id.min_date,
                'date': item.picking_id.date,
                'stock_journal_id': item.picking_id.stock_journal_id.id,
                'backorder_id': item.picking_id.id,
                'partner_id': item.picking_id.partner_id.id,
                'name': '/',
                'auto_picking': False,
                'move_type': item.picking_id.move_type,
                'company_id': item.picking_id.company_id.id,
                'invoice_state': item.picking_id.invoice_state,
                'state': 'draft',
                'type': item.picking_id.type,
                'max_date': item.picking_id.max_date,
                'sale_id': item.picking_id.sale_id.id,
                'driver_id': item.picking_id.driver_id and
                item.picking_id.driver_id.id,
                'vehicle_id': item.picking_id.vehicle_id and
                item.picking_id.vehicle_id.id,
                }
            new_pic_id = obj_pic.create(cr, uid, new_pic, context)
            obj_mov.write(cr, uid, lines_moved_ids,
                          {'picking_id': new_pic_id}, context=context)
            obj_pic.draft_force_assign(cr, uid, [new_pic_id])
        return {'type': 'ir.actions.act_window_close'}

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_split_stock_picking()


##----------------------------------------------- tcv_split_stock_picking_lines


class tcv_split_stock_picking_lines(osv.osv_memory):

    _name = 'tcv.split.stock.picking.lines'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'line_id': fields.many2one(
            'tcv.split.stock.picking', 'String', required=True,
            ondelete='cascade'),
        'move_id': fields.many2one(
            'stock.move', 'Internal Moves',
            readonly=False, required=True, ondelete='restrict'),
        'product_id': fields.related(
            'move_id', 'product_id',
            type='many2one',
            relation='product.product',
            string='Product',
            store=False, readonly=True),
        'prod_lot_id': fields.related(
            'move_id', 'prodlot_id',
            type='many2one',
            relation='stock.production.lot',
            string='Production lot',
            store=False, readonly=True),
        'selected': fields.boolean(
            'Select'),
        }

    _defaults = {
        'selected': lambda *a: True,
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_split_stock_picking_lines()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
