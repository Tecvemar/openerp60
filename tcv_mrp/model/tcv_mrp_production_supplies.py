# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2017-03-20
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

##------------------------------------------------- tcv_mrp_production_supplies


class tcv_mrp_production_supplies(osv.osv):

    _name = 'tcv.mrp.production.supplies'

    _description = ''

    _order = 'ref desc'

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'ref': fields.char(
            'Ref', size=16, required=True, readonly=True),
        'name': fields.char(
            'Concept', size=64, required=False, readonly=True,
            states={'draft': [('readonly', False)]}),
        'date': fields.date(
            'Date', required=True, readonly=True,
            states={'draft': [('readonly', False)]}, select=True),
        'narration': fields.text(
            'Notes', readonly=False),
        'picking_id': fields.many2one(
            'stock.picking', 'Picking', readonly=True, ondelete='restrict',
            help="The out stock picking for this entry line"),
        'journal_id': fields.many2one(
            'account.journal', 'Journal', required=True,
            domain="[('type','=','general')]", ondelete='restrict'),
        'move_id': fields.many2one(
            'account.move', 'Accounting entries', ondelete='restrict',
            help="The move of this entry line.", select=True, readonly=True),
        'user_id': fields.many2one(
            'res.users', 'User', readonly=True, select=True,
            ondelete='restrict'),
        'approved_user_id': fields.many2one(
            'res.users', 'Approved by', readonly=True, select=True,
            ondelete='restrict'),
        'company_id': fields.many2one(
            'res.company', 'Company', required=True, readonly=True,
            ondelete='restrict'),
        'line_ids': fields.one2many(
            'tcv.mrp.production.supplies.lines', 'line_id', 'Lines',
            readonly=True, states={'draft': [('readonly', False)]}),
        'state': fields.selection(
            [('draft', 'Draft'), ('done', 'Done'), ('cancel', 'Cancelled')],
            string='State', required=True, readonly=True),
        }

    _defaults = {
        'ref': lambda *a: '/',
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        'state': lambda *a: 'draft',
        'user_id': lambda s, c, u, ctx: u,
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company').
        _company_default_get(cr, uid, self._name, context=c),
        }

    _sql_constraints = [
        ('ref_uniq', 'UNIQUE(ref)', 'The ref must be unique!'),
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    def create_stock_move_lines(self, cr, uid, item, context=None):
        lines = []
        for line in item.line_ids:
            sml = {
                'product_id': line.product_id.id,
                'prodlot_id': line.prod_lot_id.id,
                'name': item.name or '',
                'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'product_uom': line.uom_id.id,
                'state': 'draft',
                'location_id': line.location_id.id,
                'location_dest_id': context.get('location_dest_id'),
                'product_qty': line.product_qty,
                'product_uos_qty': line.product_qty,
                }
            lines.append((0, 0, sml.copy()))
        return lines

    def create_stock_picking(self, cr, uid, ids, context=None):
        context = context or {}
        res = {'picking_id': 0}
        ids = isinstance(ids, (int, long)) and [ids] or ids
        obj_pck = self.pool.get('stock.picking')
        obj_cfg = self.pool.get('tcv.mrp.config')
        company_id = self.pool.get('res.users').browse(
            cr, uid, uid, context=context).company_id.id
        cfg_id = obj_cfg.search(cr, uid, [('company_id', '=', company_id)])
        if cfg_id:
            mrp_cfg = obj_cfg.browse(cr, uid, cfg_id[0], context=context)
            context.update({'location_dest_id': mrp_cfg.location_id.id})
        else:
            raise osv.except_osv(
                _('Error!'),
                _('Please set a valid configuration '))
        for item in self.browse(cr, uid, ids, context={}):
            picking = {
                'name': '/',
                'origin': '[%s] %s' % (item.ref, item.name or ''),
                'date': item.date,
                'invoice_state': 'none',
                'stock_journal_id': mrp_cfg.stock_journal_id.id,
                'company_id': item.company_id.id,
                'auto_picking': False,  #
                'move_type': 'one',
                'partner_id': item.company_id.partner_id.id,
                'state_rw': 0,
                'note': item.narration,
                'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'type': 'out',
                }
            lines = self.create_stock_move_lines(
                cr, uid, item, context)
            if lines:
                picking.update({
                    'move_lines': lines})
                res['picking_id'] = obj_pck.create(
                    cr, uid, picking, context)
        return res

    def create_account_move_lines(self, cr, uid, item, context=None):
        res = []
        obj_cst = self.pool.get('tcv.cost.management')
        for line in item.line_ids:
            categ = line.product_id.categ_id
            name = '(%s) %s' % (line.prod_lot_id.name,
                                line.product_id.name)
            pre_line = {
                'auto': True,
                'company_id': item.company_id.id,
                'name': name,
                'debit': 0,
                'credit': 0,
                'reconcile': False,
                }
            if not categ.property_account_expense_categ or \
                    not categ.property_stock_account_output_categ:
                raise osv.except_osv(
                    _('Error!'),
                    _('Can\'t find accounting info for categ: %s\n' +
                      '(stock output & account expense)') % categ.name)
            accs = [categ.property_account_expense_categ.id,
                    categ.property_stock_account_output_categ.id]
            amt_fld = ['debit', 'credit']
            cost = obj_cst.get_tcv_cost(
                cr, uid, line.prod_lot_id, line.product_id, context)
            amount = line.product_qty * cost
            for x in range(2):
                move_line = pre_line.copy()
                move_line.update({'account_id': accs[x],
                                  amt_fld[x]: round(amount, 2)})
                res.append((0, 0, move_line))
        res.reverse()
        return res

    def create_account_move(self, cr, uid, ids, context=None):
        context = context or {}
        res = {'move_id': 0}
        obj_move = self.pool.get('account.move')
        obj_per = self.pool.get('account.period')
        for item in self.browse(cr, uid, ids, context={}):
            period_id = obj_per.find(cr, uid, item.date)[0]
            move = {
                'ref': '%s %s' % (item.ref, item.name or ''),
                'journal_id': item.journal_id.id,
                'date': item.date,
                'min_date': item.date,
                'company_id': item.company_id.id,
                'state': 'draft',
                'to_check': False,
                'period_id': period_id,
                'narration': item.narration,
                }
            move.update({
                'line_id': self.create_account_move_lines(
                    cr, uid, item, context)
                })
            move_id = obj_move.create(cr, uid, move, context)
            if move_id:
                obj_move.post(cr, uid, [move_id], context=context)
                res['move_id'] = move_id
        return res

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    def create(self, cr, uid, vals, context=None):
        if not vals.get('ref') or vals.get('ref') == '/':
            vals.update({'ref': self.pool.get('ir.sequence').get(
                cr, uid, 'tcv.mrp.production.supplies')})
        res = super(tcv_mrp_production_supplies, self).create(
            cr, uid, vals, context)
        return res

    ##---------------------------------------------------------------- Workflow

    def button_draft(self, cr, uid, ids, context=None):
        vals = {'state': 'draft'}
        return self.write(cr, uid, ids, vals, context)

    def button_done(self, cr, uid, ids, context=None):
        vals = {'state': 'done', 'approved_user_id': uid}
        vals.update(self.create_stock_picking(cr, uid, ids, context))
        vals.update(self.create_account_move(cr, uid, ids, context))
        return self.write(cr, uid, ids, vals, context)

    def button_cancel(self, cr, uid, ids, context=None):
        obj_move = self.pool.get('account.move')
        move_ids = []
        for item in self.browse(cr, uid, ids, context={}):
            if item.move_id:
                move_ids.append(item.move_id.id)
        vals = {'state': 'cancel', 'move_id': 0,
                'done_user_id': 0, 'picking_id': 0}
        res = self.write(cr, uid, ids, vals, context)
        obj_move.unlink(cr, uid, move_ids, context)
        return res

    def test_draft(self, cr, uid, ids, *args):
        return True

    def test_done(self, cr, uid, ids, *args):
        for item in self.browse(cr, uid, ids, context={}):
            if not item.line_ids:
                raise osv.except_osv(
                    _('Error!'),
                    _('Please add some lines first'))
            for line in item.line_ids:
                if not line.product_qty:
                    raise osv.except_osv(
                        _('Error!'),
                        _('The product qty must be > 0 (%s, %s)') %
                        (line.product_id.default_code, line.prod_lot_id.name))
        return True

    def test_cancel(self, cr, uid, ids, *args):
        for item in self.browse(cr, uid, ids, context={}):
            if item.move_id and item.move_id.state != 'draft':
                raise osv.except_osv(
                    _('Error!'),
                    _('You can not cancel a document while the account ' +
                      'move is posted.'))
        return True

tcv_mrp_production_supplies()


##------------------------------------------- tcv_mrp_production_supplies_lines


class tcv_mrp_production_supplies_lines(osv.osv):

    _name = 'tcv.mrp.production.supplies.lines'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'line_id': fields.many2one(
            'tcv.mrp.production.supplies', 'Parent', required=True,
            ondelete='cascade'),
        'product_id': fields.many2one(
            'product.product', 'Product', ondelete='restrict', required=True),
        'prod_lot_id': fields.many2one(
            'stock.production.lot', 'Production lot', required=False),
        'product_qty': fields.float(
            'Quantity', digits_compute=dp.get_precision('Product UoM'),
            readonly=False, required=True),
        'uom_id': fields.many2one(
            'product.uom', 'Unit of Measure', ondelete='restrict',
            required=True),
        'location_id': fields.many2one(
            'stock.location', 'Location', readonly=False, ondelete='restrict',
            required=True,
            help="Phisical location for goods (origin location)"),
        }

    _defaults = {
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    def on_change_product(self, cr, uid, ids,
                          product_id, prod_lot_id, product_qty, location_id):
        res = {}
        obj_lot = self.pool.get('stock.production.lot')
        if not product_id and prod_lot_id:
            lot_brw = obj_lot.browse(cr, uid, prod_lot_id, context=None)
            res.update({'product_id': lot_brw.product_id.id,
                        'uom_id': lot_brw.product_id.uom_id.id})
            if not location_id:
                act_loc_id = obj_lot.get_actual_lot_location(
                    cr, uid, prod_lot_id, context=None)[0]
                res.update({'location_id': act_loc_id})
        return {'value': res}

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_mrp_production_supplies_lines()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
