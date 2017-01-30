# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

from osv import osv, fields
from tools.translate import _
import decimal_precision as dp

##-------------------------------------------------------------- purchase_order


class purchase_order(osv.osv):

    _inherit = 'purchase.order'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'name': fields.char(
            'Order Reference', size=64, required=True,
            select=True, readonly=True,
            help="Unique number of the purchase order, " +
                 "computed automatically when the purchase " +
                 "order is created"),
        'description': fields.char(
            'Description', size=64, select=True, readonly=True,
            states={'draft': [('readonly', False)]}),
        }

    _defaults = {
        'name': lambda *a: '/',
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    def inv_line_create(self, cr, uid, a, ol):
        '''
        '''
        data = super(purchase_order, self).inv_line_create(cr, uid, a, ol)
        data[2]['prod_lot_id'] = ol.prod_lot_id and ol.prod_lot_id.id
        data[2]['pieces'] = ol.pieces
        data[2]['track_incoming'] = ol.track_incoming
        return data

    def action_picking_create(self, cr, uid, ids, *args):
        '''
        Added to transfer order_line.prod_lot_id.id to stock_move.prodlot_id
        '''
        picking_id = super(purchase_order, self).\
            action_picking_create(cr, uid, ids, args)
        obj_mov = self.pool.get('stock.move')
        for order in self.browse(cr, uid, ids):
            for order_line in order.order_line:
                if order_line.prod_lot_id:
                    move_id = obj_mov.search(
                        cr, uid, [('purchase_line_id', '=', order_line.id)])
                    if move_id:
                        updated_data = {
                            'prodlot_id': order_line.prod_lot_id.id,
                            'pieces_qty': order_line.pieces}
                        obj_mov.write(cr, uid, move_id, updated_data)

        return picking_id

    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        default.update({
            'validator': False,
            'date_approve': False,
            'partner_ref': '',
            'origin': '',
            'notes': '',
        })
        return super(purchase_order, self).copy(cr, uid, id, default, context)

    ##-------------------------------------------------------- buttons (object)

    def button_lot_list(self, cr, uid, ids, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        so_brw = self.browse(cr, uid, ids, context={})[0]
        context.update({'default_pricelist_id': so_brw.pricelist_id.id,
                        'purchase_order_id': so_brw.id})
        return {'name': _('Load lot list'),
                'type': 'ir.actions.act_window',
                'res_model': 'tcv.purchase.lot.list',
                'view_type': 'form',
                'view_id': False,
                'view_mode': 'form',
                'nodestroy': True,
                'target': 'new',
                'domain': "",
                'context': context}

    def action_invoice_create(self, cr, uid, ids, *args):
        inv_id = super(purchase_order, self).\
            action_invoice_create(cr, uid, ids, args)
        if inv_id:
            obj_val = self.pool.get('ir.values')
            res_journal_default = obj_val.get(
                cr, uid, 'default', 'type=in_invoice', ['account.invoice'])
            journal_id = 0
            for j in res_journal_default:
                if j[1] == 'journal_id':
                    journal_id = j[2]
            if journal_id:
                obj_inv = self.pool.get('account.invoice')
                obj_inv.write(cr, uid, inv_id, {'journal_id': journal_id},
                              context={})
        return inv_id

    ##------------------------------------------------------------ on_change...

    def onchange_partner_id(self, cr, uid, ids, part):
        # Added to set the default purchase location (purchase dest) from
        # partner fields
        res = super(purchase_order, self).\
            onchange_partner_id(cr, uid, ids, part)
        if part:
            obj_pnr = self.pool.get('res.partner')
            partner = obj_pnr.browse(cr, uid, part, context=None)
            if partner.property_stock_purchase:
                location_id = partner.property_stock_purchase.id
                res['value'].update({'location_id': location_id})
        return res

    ##----------------------------------------------------- create write unlink

    def create(self, cr, uid, vals, context=None):
        if not vals.get('name') or vals.get('name') == '/':
            vals.update({'name': self.pool.get('ir.sequence').
                        get(cr, uid, 'purchase.order')})
        res = super(purchase_order, self).create(cr, uid, vals, context)
        return res

    ##---------------------------------------------------------------- Workflow

purchase_order()

##--------------------------------------------------------- purchase_order_line


class purchase_order_line(osv.osv):

    _inherit = 'purchase.order.line'

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'prod_lot_id': fields.many2one(
            'stock.production.lot', 'Production lot', ondelete='restrict'),
        'pieces': fields.integer(
            'Pieces', require=True),
        'product_qty': fields.float(
            'Quantity', digits_compute=dp.get_precision('Product UoM')),
        'track_incoming': fields.related(
            'product_id', 'track_incoming', type='bool',
            relation='product.product'),
        'stock_driver': fields.related(
            'product_id', 'stock_driver', type='char', size=12,
            relation='product.product'),
        }

    ##-----------------------------------------------------

    ##----------------------------------------------------- public methods

    def copy_data(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        default.update({'state': 'draft',
                        'move_ids': [],
                        'invoiced': 0,
                        'invoice_lines': [],
                        'sale_order_line_ids': [],
                        'prod_lot_id': []})
        return super(purchase_order_line, self).\
            copy_data(cr, uid, id, default, context)

    def inv_line_create(self, cr, uid, a, ol):
        data = super(purchase_order, self).inv_line_create(cr, uid, a, ol)
        data[2]['prod_lot_id'] = ol.prod_lot_id and ol.prod_lot_id.id
        data[2]['pieces'] = ol.pieces
        data[2]['track_incoming'] = ol.track_incoming
        return data

    def action_picking_create(self, cr, uid, ids, *args):
        '''
        Added to transfer order_line.prod_lot_id.id to stock_move.prodlot_id
        '''
        picking_id = super(purchase_order, self).\
            action_picking_create(cr, uid, ids, args)
        obj_mov = self.pool.get('stock.move')
        for order in self.browse(cr, uid, ids):
            for order_line in order.order_line:
                if order_line.prod_lot_id:
                    move_id = obj_mov.search(cr, uid, [('purchase_line_id',
                                                        '=', order_line.id)])
                    if move_id:
                        upd_data = {'prodlot_id': order_line.prod_lot_id.id,
                                    'pieces_qty': order_line.pieces}
                        obj_mov.write(cr, uid, move_id, upd_data)

        return picking_id

    ##----------------------------------------------------- buttons (object)

    ##----------------------------------------------------- on_change...

    def product_id_change(self, cr, uid, ids, pricelist, product, qty, uom,
                          partner_id, date_order=False, fiscal_position=False,
                          date_planned=False, name=False, price_unit=False,
                          notes=False):
        '''
        This method loads the withholding concept to a product automatically
        '''
        res = super(purchase_order_line, self).\
            product_id_change(cr, uid, ids, pricelist, product, qty, uom,
                              partner_id, date_order, fiscal_position,
                              date_planned, name, price_unit, notes)
        if product:
            product_obj = self.pool.get('product.product')
            produc_brw = product_obj.browse(cr, uid, product)
            res['value']['track_incoming'] = produc_brw.track_incoming
            res['value']['stock_driver'] = produc_brw.stock_driver
        else:
            res['value']['track_incoming'] = False

        return res

    def on_change_qty(self, cr, uid, ids, product_id, pieces, context=None):
        """
        Only products type tile compute pieces
        @param product_id Id of product to purchase
        @param pieces Number of pieces to compute the area
        """

        if not context:
            context = {}
        res = {'value': {}}

        if pieces and product_id:
            product_obj = self.pool.get('product.product')
            product_brw = product_obj.browse(cr, uid, product_id)
            if product_brw.stock_driver == 'tile':
                if product_brw.tile_format_id.factile:
                    res['value'].update({'product_qty':
                                         round(pieces *
                                               product_brw.tile_format_id.
                                               factile, 4)})
                else:
                    raise osv.except_osv(_('Error'),
                                         _("You must set a tile format in " +
                                           "product's especial special " +
                                           "features"))
        return res

    def on_change_prod_lot_id(self, cr, uid, ids, product_id, prod_lot_id):
        res = {}
        if prod_lot_id:
            obj_lot = self.pool.get('stock.production.lot')
            lot = obj_lot.browse(cr, uid, prod_lot_id, context={})
            if not product_id:
                res.update({'product_id': lot.product_id.id})
            if lot.product_id.stock_driver in ('slab', 'block'):
                res.update({'pieces': 1,
                            'product_qty': lot.lot_factor})

        return {'value': res}

    ##----------------------------------------------------- create write unlink

    ##----------------------------------------------------- Workflow

purchase_order_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
