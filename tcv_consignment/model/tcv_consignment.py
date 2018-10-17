# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2018-10-16
#    Version: 0.0.0.1
#
#    Description:
#
#
##############################################################################

# ~ from datetime import datetime
from osv import fields, osv
from tools.translate import _
# ~ import pooler
import decimal_precision as dp
import time
# ~ import netsvc

##------------------------------------------------------------- tcv_consignment


class tcv_consignment(osv.osv):

    _name = 'tcv.consignment'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def _get_type(self, cr, uid, context=None):
        context = context or {}
        return context.get('consignment_type', 'out_consignment')

    ##--------------------------------------------------------- function fields

    _columns = {
        'name': fields.char(
            'Reference', size=64, required=False, readonly=True),
        'date': fields.date(
            'Date', required=True, readonly=True,
            states={'draft': [('readonly', False)]}, select=True),
        'partner_id': fields.many2one(
            'res.partner', 'Partner', change_default=True,
            readonly=True, required=True,
            states={'draft': [('readonly', False)]}, ondelete='restrict'),
        'user_id': fields.many2one(
            'res.users', 'User', readonly=True, select=True,
            ondelete='restrict'),
        'narration': fields.text(
            'Notes', readonly=False),
        'line_ids': fields.one2many(
            'tcv.consignment.lines', 'line_id', 'Detail',
            readonly=True, states={'draft': [('readonly', False)]}),
        'type': fields.selection(
            [('in_consignment', 'In consignment'),
             ('out_consignment', 'Out consignment')],
            string='Type', required=True, readonly=True),
        'state': fields.selection(
            [('draft', 'Draft'), ('done', 'Done'), ('cancel', 'Cancelled')],
            string='State', required=True, readonly=True),
        'move_id': fields.many2one(
            'account.move', 'Accounting entries', ondelete='restrict',
            help="The move of this entry line.", select=True, readonly=True),
        'picking_id': fields.many2one(
            'stock.picking', 'Picking', readonly=True, ondelete='restrict',
            help="The picking for this entry line"),
        }

    _defaults = {
        'name': lambda *a: '/',
        'type': _get_type,
        'user_id': lambda s, c, u, ctx: u,
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        'state': lambda *a: 'draft',
        }

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', 'The name must be unique!'),
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    def create_account_move(self, cr, uid, ids, context=None):
        return 0

    def create_stock_picking(self, cr, uid, ids, vals, context=None):
        return 0

    ##-------------------------------------------------------- buttons (object)

    def button_lot_list(self, cr, uid, ids, context=None):
        return True
        # ~ ids = isinstance(ids, (int, long)) and [ids] or ids
        # ~ so_brw = self.browse(cr, uid, ids, context={})[0]
        # ~ context.update({'sale_order_id': so_brw.id,
                        # ~ 'default_sale_id': so_brw.id,
                        # ~ 'default_partner_id': so_brw.partner_id.id,
                        # ~ })
        # ~ return {'name': _('Load lot list'),
                # ~ 'type': 'ir.actions.act_window',
                # ~ 'res_model': 'tcv.sale.lot.list',
                # ~ 'view_type': 'form',
                # ~ 'view_id': False,
                # ~ 'view_mode': 'form',
                # ~ 'nodestroy': True,
                # ~ 'target': 'new',
                # ~ 'domain': "",
                # ~ 'context': context}

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    def create(self, cr, uid, vals, context=None):
        context = context or {}
        if not vals.get('name') or vals.get('name') == '/':
            if context.get('consignment_type') == 'out_consignment':
                seq_name = 'tcv.consignment.sale'

            elif context.get('consignment_type') == 'in_consignment':
                seq_name = 'tcv.consignment.purchase'
            else:
                raise osv.except_osv(
                    _('Error!'),
                    _('Must indicate consignment_type in context'))
            vals.update({
                'name': self.pool.get('ir.sequence').get(cr, uid, seq_name),
                })
        res = super(tcv_consignment, self).create(
            cr, uid, vals, context)
        return res

    ##---------------------------------------------------------------- Workflow

    def button_draft(self, cr, uid, ids, context=None):
        vals = {'state': 'draft'}
        return self.write(cr, uid, ids, vals, context)

    def button_done(self, cr, uid, ids, context=None):
        pickind_id = self.create_stock_picking(cr, uid, ids, context)
        move_id = self.create_account_move(cr, uid, ids, context)
        vals = {
            'state': 'done',
            'pickind_id': pickind_id,
            'move_id': move_id,
            }
        return self.write(cr, uid, ids, vals, context)

    def button_cancel(self, cr, uid, ids, context=None):
        vals = {'state': 'cancel'}
        return self.write(cr, uid, ids, vals, context)

    def test_draft(self, cr, uid, ids, *args):
        return True

    def test_done(self, cr, uid, ids, *args):
        return True

    def test_cancel(self, cr, uid, ids, *args):
        return True


tcv_consignment()


##------------------------------------------------------- tcv_consignment_lines


class tcv_consignment_lines(osv.osv):

    _name = 'tcv.consignment.lines'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'line_id': fields.many2one(
            'tcv.consignment', 'Line', required=True, ondelete='cascade'),
        'name': fields.char(
            'Name', size=64, required=False, readonly=False),
        'prod_lot_id': fields.many2one(
            'stock.production.lot', 'Production lot', required=True),
        'product_id': fields.related(
            'prod_lot_id', 'product_id', type='many2one',
            relation='product.product', string='Product', store=False,
            readonly=True),
        'quantity': fields.float(
            'quantity', digits_compute=dp.get_precision('Product UoM')),
        'pieces': fields.integer(
            'Pieces'),
        }

    _defaults = {
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    def on_change_prod_lot_id(self, cr, uid, ids, prod_lot_id):
        res = {}
        if not prod_lot_id:
            return {'value': res}
        obj_lot = self.pool.get('stock.production.lot')
        lot = obj_lot.browse(cr, uid, prod_lot_id, context=None)
        res.update({
            'product_id': lot.product_id.id,
            'quantity': lot.stock_available,
            'pieces': round(lot.stock_available / lot.lot_factor, 0),
            })
        return {'value': res}

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow


tcv_consignment_lines()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
