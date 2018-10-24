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

    def _get_consignment_config(self, cr, uid, ids, context):
        obj_cfg = self.pool.get('tcv.consignment.config')
        ids = isinstance(ids, (int, long)) and [ids] or ids
        for consig in self.browse(cr, uid, ids, context=context):
            cfg_id = obj_cfg.search(
                cr, uid, [('partner_id', '=', consig.partner_id.id)])
            if cfg_id:
                self.write(
                    cr, uid, [consig.id], {'config_id': cfg_id[0]},
                    context=context)
            else:
                raise osv.except_osv(
                    _('Error!'),
                    _('Please set a valid consignement configuration for '
                      'partner: %s\n'
                      'Sales->Configuration->Sales->Consignment Settings') %
                    (consig.partner_id.name))

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
            help="The move of this entry line.", select=True, readonly=False),
        'picking_id': fields.many2one(
            'stock.picking', 'Picking', readonly=False, ondelete='set null',
            help="The picking for this entry line"),
        'config_id': fields.many2one(
            'tcv.consignment.config', 'Configuration', readonly=True,
            ondelete='restrict', help="Config settings for this document"),
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

    def create_stock_move_lines(self, cr, uid, item, lines, context=None):
        res = []
        obj_lot = self.pool.get('stock.production.lot')
        for line in item.line_ids:
            date = time.strftime('%Y-%m-%d %H:%M:%S')
            location_id = obj_lot.get_actual_lot_location(
                cr, uid, line.prod_lot_id.id, context=None)
            data = {
                'name': item.name,
                'product_id': line.product_id.id,
                'product_qty': line.product_qty,
                'product_uom': line.product_id.uom_id.id,
                'product_uos_qty': line.product_qty,
                'product_uos': line.product_id.uom_id.id,
                'pieces_qty': line.pieces,
                'date': date,
                'date_expected': date,
                'prodlot_id': line.prod_lot_id.id,
                'location_id': location_id and location_id[0] or 0,
                'location_dest_id': item.config_id.stock_location_id.id,
                }
            res.append(data)
        return res

    def create_stock_picking(self, cr, uid, ids, vals, context=None):
        context = context or {}
        ids = isinstance(ids, (int, long)) and [ids] or ids
        obj_pck = self.pool.get('stock.picking')
        company_id = self.pool.get('res.company')._company_default_get(
            cr, uid, self._name, context=context)
        date = time.strftime('%Y-%m-%d %H:%M:%S')
        for item in self.browse(cr, uid, ids, context=context):
            address = [addr for addr in item.partner_id.address
                       if addr.type == 'invoice']
            lines = self.create_stock_move_lines(
                cr, uid, item, None, context)
            picking = {
                'name': '/',
                'type': 'internal',
                'origin': ' '.join((item.name, item.config_id.name)),
                'date': date,
                'invoice_state': 'none',
                'stock_journal_id': item.config_id.stock_journal_id.id,
                'company_id': company_id,
                'auto_picking': False,
                'move_type': 'one',
                'partner_id': item.partner_id.id,
                'address_id': address[0].id,
                'state_rw': 0,
                'note': item.narration,
                'move_lines': lines and [(0, 0, l) for l in lines],
                }

            pick_id = obj_pck.create(cr, uid, picking, context)
        return pick_id

    def create_account_move(self, cr, uid, ids, context=None):
        return False

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
        vals = {'state': 'draft', 'config_id': 0}
        return self.write(cr, uid, ids, vals, context)

    def button_done(self, cr, uid, ids, context=None):
        context = context or {}
        self._get_consignment_config(cr, uid, ids, context)
        picking_id = self.create_stock_picking(cr, uid, ids, context)
        move_id = self.create_account_move(cr, uid, ids, context)
        vals = {
            'state': 'done',
            'picking_id': picking_id,
            'move_id': move_id,
            }
        return self.write(cr, uid, ids, vals, context)

    def button_cancel(self, cr, uid, ids, context=None):
        vals = {'state': 'cancel'}
        return self.write(cr, uid, ids, vals, context)

    def test_draft(self, cr, uid, ids, *args):
        return True

    def test_done(self, cr, uid, ids, *args):
        for item in self.browse(cr, uid, ids, context={}):
            for line in item.line_ids:
                if not line.product_qty:
                    raise osv.except_osv(
                        _('Error!'),
                        _('No quantity for lot: %s') % line.prod_lot_id.name)
        return True

    def test_cancel(self, cr, uid, ids, *args):
        for item in self.browse(cr, uid, ids, context={}):
            if item.picking_id.state not in ('draft', 'cancel'):
                raise osv.except_osv(
                    _('Error!'),
                    _('Can\'t cancel while picking\'s state ' +
                      '<> "Draft" or "Cancel"'))
            # ~ else:
                # ~ if item.picking_id.state == 'draft':
                    # ~ cancel pcking
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
        'product_qty': fields.float(
            'Quantity', digits_compute=dp.get_precision('Product UoM')),
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
            'product_qty': lot.stock_available,
            'pieces': round(lot.stock_available / lot.lot_factor, 0),
            })
        return {'value': res}

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow


tcv_consignment_lines()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
