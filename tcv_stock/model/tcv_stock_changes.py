# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2014-07-17
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

##----------------------------------------------------------- tcv_stock_changes


_TCV_STOCK_CHANGES_STATES = [
    ('draft', 'Draft'),
    ('confirm', 'Confirmed'),
    ('done', 'Done'),
    ('cancel', 'Cancelled')
    ]


class tcv_stock_changes(osv.osv):

    _name = 'tcv.stock.changes'

    _description = ''

    _order = 'ref desc'

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def _check_stock_production_lot(self, cr, lot_ids, sql):
        cr.execute(sql % str(lot_ids)[1:-1].replace('L', ''))
        res = cr.fetchall()
        return res and str([str(x[0]) for x in res])[1:-1]

    ##--------------------------------------------------------- function fields

    _columns = {
        'ref': fields.char(
            'ref', size=64, required=False, readonly=True),
        'name': fields.char(
            'Name', size=64, required=True, readonly=True,
            states={'draft': [('readonly', False)]}, select=True),
        'date': fields.date(
            'Date', required=True, readonly=True,
            states={'draft': [('readonly', False)]}, select=True),
        'method_id': fields.many2one(
            'tcv.stock.changes.method', 'Adj. method', readonly=True,
            states={'draft': [('readonly', False)]}, select=True,
            required=True, ondelete='restrict'),
        'picking_in_id': fields.many2one(
            'stock.picking', 'Picking IN', readonly=True,
            ondelete='restrict'),
        'picking_out_id': fields.many2one(
            'stock.picking', 'Picking OUT', readonly=True,
            ondelete='restrict'),
        'move_id': fields.many2one(
            'account.move', 'Accounting entries', ondelete='restrict',
            help="The move of this entry line.", select=True, readonly=True),
        'state': fields.selection(
            _TCV_STOCK_CHANGES_STATES, 'State', required=True, readonly=True),
        'narration': fields.text(
            'Notes', readonly=False),
        'confirm_user_id': fields.many2one(
            'res.users', 'Confirmed by', readonly=True, select=True,
            ondelete='restrict'),
        'done_user_id': fields.many2one(
            'res.users', 'Doned by', readonly=True, select=True,
            ondelete='restrict'),
        'company_id': fields.many2one(
            'res.company', 'Company', required=True, readonly=True,
            ondelete='restrict'),
        'account_id': fields.many2one(
            'account.account', 'Account', ondelete='restrict', required=False,
            readonly=True, states={'draft': [('readonly', False)]},
            help="The account for inventory variation, use only when " +
            "need to replace default account"),
        'line_ids': fields.one2many(
            'tcv.stock.changes.lines', 'line_id', 'Production lots',
            readonly=True, states={'draft': [('readonly', False)]}),
        }

    _defaults = {
        'ref': lambda *a: '/',
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        'state': lambda *a: 'draft',
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company').
        _company_default_get(cr, uid, self._name, context=c),
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    def create_stock_move_lines(self, cr, uid, item, context=None):
        lines_in = []
        lines_out = []
        obj_lot = self.pool.get('stock.production.lot')
        obj_uom = self.pool.get('product.uom')
        for line in item.line_ids:
            if not line.location_id:
                act_loc_id = obj_lot.get_actual_lot_location(
                    cr, uid, line.prod_lot_id.id, context)[0]
            else:
                act_loc_id = line.location_id.id
            locations = {'internal': act_loc_id,
                         'scrap': item.method_id.location_id.id}
            sml = {
                'product_id': line.product_id.id,
                'prodlot_id': line.prod_lot_id.id,
                'name': item.name or '',
                'date': item.date,
                'product_uom': line.product_id.uom_id.id,
                'state': 'draft'}
            lot = {}
            if line.stock_driver in ('slab', 'block'):
                lot.update({'length': line.new_length,
                            'heigth': line.new_heigth,
                            'width': line.new_width})
            lot_area = obj_uom._compute_area(
                cr, uid, line.stock_driver, line.pieces,
                line.length, line.heigth, line.width,
                context=context) if line.pieces else 0
            new_area = obj_uom._compute_area(
                cr, uid, line.stock_driver, line.new_pieces,
                line.new_length, line.new_heigth, line.new_width,
                context=context) if line.new_pieces else 0
            if item.method_id.type == 'stock':

                lot_value = lot_area * line.cost_price
                new_cost = (lot_value / new_area) if new_area else 0
                if new_cost:
                    lot.update({'property_cost_price': new_cost})
            if lot:
                obj_lot.write(
                    cr, uid, [line.prod_lot_id.id], lot, context=context)
            # Send out all stock (=0) then create new stock
            if lot_area > 0:
                sml.update({
                    'location_id': locations['internal'],
                    'location_dest_id': locations['scrap'],
                    'pieces_qty': line.pieces,
                    'product_qty': lot_area,
                    'product_uos_qty': lot_area,
                    })
                lines_out.append((0, 0, sml.copy()))
            if new_area > 0:
                sml.update({
                    'location_id': locations['scrap'],
                    'location_dest_id': locations['internal'],
                    'pieces_qty': line.new_pieces,
                    'product_qty': new_area,
                    'product_uos_qty': new_area,
                    })
                lines_in.append((0, 0, sml.copy()))
        return lines_in, lines_out

    def create_stock_picking(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        res = {'picking_in_id': 0, 'picking_out_id': 0}
        obj_pck = self.pool.get('stock.picking')
        ids = isinstance(ids, (int, long)) and [ids] or ids
        for item in self.browse(cr, uid, ids, context={}):
            picking = {
                'name': '/',
                'origin': '[%s] %s' % (item.ref, item.name or ''),
                'date': item.date,
                'invoice_state': 'none',
                'stock_journal_id': item.method_id.stock_journal_id.id,
                'company_id': item.company_id.id,
                'auto_picking': False,  #
                'move_type': 'one',
                'partner_id': item.company_id.partner_id.id,
                'state_rw': 0,
                'note': item.narration,
                }
            picking_in = picking.copy()
            picking_out = picking.copy()
            lines_in, lines_out = self.create_stock_move_lines(
                cr, uid, item, context)
            #~ Out first
            if lines_out:
                picking_out.update({
                    'date': '%s 00:00:00' % item.date,
                    'type': 'out',
                    'move_lines': lines_out})
                res['picking_out_id'] = obj_pck.create(
                    cr, uid, picking_out, context)
            #~ Then in...
            if lines_in:
                picking_in.update({
                    'date': '%s 00:00:01' % item.date,
                    'type': 'in',
                    'move_lines': lines_in})
                res['picking_in_id'] = obj_pck.create(
                    cr, uid, picking_in, context)
        return res

    def create_account_move_lines(self, cr, uid, item, context=None):
        res = []
        for line in item.line_ids:
            categ = line.product_id.categ_id
            name = '(%s) %s' % (line.prod_lot_id.name, line.product_id.name)
            pre_line = {
                'auto': True,
                'company_id': item.company_id.id,
                'name': name,
                'debit': 0,
                'credit': 0,
                'reconcile': False,
                }
            # -stock(cr) -> +scrap(db)
            if not categ.property_stock_variation or \
                    not categ.property_stock_account_output_categ:
                raise osv.except_osv(
                    _('Error!'),
                    _('Can\'t find accounting info for categ: %s\n' +
                      '(stock output & stock variation)') % categ.name)
            accs = [item.account_id and item.account_id.id or
                    categ.property_stock_variation.id,
                    categ.property_stock_account_output_categ.id
                    if line.qty_diff < 0 else
                    categ.property_stock_account_input_categ.id]
            if line.qty_diff < 0:  # -scrap(cr) -> +stock(db)
                accs.reverse()
            amt_fld = ['credit', 'debit']  # Yes: credit, debit
            amount = abs(line.qty_diff) * line.prod_lot_id.property_cost_price
            for x in range(2):
                move_line = pre_line.copy()
                move_line.update({'account_id': accs[x],
                                  amt_fld[x]: round(amount, 2)})
                res.append((0, 0, move_line))
        res.reverse()
        return res

    def create_account_move(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        res = {'move_id': 0}
        obj_move = self.pool.get('account.move')
        obj_per = self.pool.get('account.period')
        for item in self.browse(cr, uid, ids, context={}):
            if item.method_id.type != 'account':
                return res
            period_id = obj_per.find(cr, uid, item.date)[0]
            move = {
                'ref': '[%s] %s' % (item.ref, item.name or ''),
                'journal_id': item.method_id.journal_id.id,
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
            vals.update({'ref': self.pool.get('ir.sequence').
                         get(cr, uid, 'tcv.stock.changes')})
        res = super(tcv_stock_changes, self).create(cr, uid, vals, context)
        return res

    def unlink(self, cr, uid, ids, context=None):
        unlink_ids = []
        for item in self.browse(cr, uid, ids, context={}):
            if item.state in ('cancel'):
                unlink_ids.append(item['id'])
            else:
                raise osv.except_osv(
                    _('Invalid action !'),
                    _('Cannot delete a record that aren\'t cancelled!'))
        res = super(tcv_stock_changes, self).\
            unlink(cr, uid, unlink_ids, context)
        return res

    ##---------------------------------------------------------------- Workflow

    def button_draft(self, cr, uid, ids, context=None):
        vals = {'state': 'draft', 'done_user_id': 0, 'confirm_user_id': 0}
        return self.write(cr, uid, ids, vals, context)

    def button_confirm(self, cr, uid, ids, context=None):
        vals = {'state': 'confirm', 'confirm_user_id': uid}
        return self.write(cr, uid, ids, vals, context)

    def button_done(self, cr, uid, ids, context=None):
        vals = {'state': 'done', 'done_user_id': uid}
        vals.update(self.create_stock_picking(cr, uid, ids, context))
        vals.update(self.create_account_move(cr, uid, ids, context))
        return self.write(cr, uid, ids, vals, context)

    def button_cancel(self, cr, uid, ids, context=None):
        vals = {'state': 'cancel'}
        return self.write(cr, uid, ids, vals, context)

    def test_draft(self, cr, uid, ids, *args):
        return True

    def test_confirm(self, cr, uid, ids, *args):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        for item in self.browse(cr, uid, ids, context={}):
            if not item.line_ids:
                raise osv.except_osv(
                    _('Error!'),
                    _('Please add some lines first'))
            for line in item.line_ids:
                if not line.qty_diff:
                    raise osv.except_osv(
                        _('Error!'),
                        _('The Diff must be <> 0 (%s)') %
                        line.prod_lot_id.name)

                if (not line.qty or not line.new_qty) and \
                        item.method_id.type != 'account':
                    raise osv.except_osv(
                        _('Error!'),
                        _('Must set method to accounting if actual or ' +
                          'new quantity = 0'))
        return True

    def test_done(self, cr, uid, ids, *args):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        for item in self.browse(cr, uid, ids, context={}):
            lot_ids = []
            for line in item.line_ids:
                lot_ids.append(line.prod_lot_id.id)
                if line.qty != line.prod_lot_id.stock_available:
                    raise osv.except_osv(
                        _('Error!'),
                        _('Lot stock changed: %s please remove and reload ' +
                          'data before process') % line.prod_lot_id.name)
        if lot_ids:
            #~ Check if lot in sale_order
            sql = '''
                select distinct lot.name from sale_order_line l
                left join sale_order o on l.order_id = o.id
                left join stock_production_lot lot on l.prod_lot_id = lot.id
                where l.prod_lot_id in (%s) and o.state = 'draft'
                '''
            res = self._check_stock_production_lot(cr, lot_ids, sql)
            if res:
                raise osv.except_osv(
                    _('Error!'),
                    _('Can\'t adjust a lot while is in a sale order:' +
                      '\n%s') % res)
            sql = '''
                select distinct lot.name from account_invoice_line l
                left join account_invoice i on l.invoice_id = i.id
                left join stock_production_lot lot on l.prod_lot_id = lot.id
                where l.prod_lot_id in (%s) and i.state = 'draft'
                '''
            res = self._check_stock_production_lot(cr, lot_ids, sql)
            if res:
                raise osv.except_osv(
                    _('Error!'),
                    _('Can\'t adjust a lot while is in a invoice:' +
                      '\n%s') % res)
            sql = '''
                select distinct lot.name from stock_move m
                left join stock_production_lot lot on m.prodlot_id = lot.id
                where m.prodlot_id in (%s) and
                      m.state not in ('done', 'cancel')
                '''
            res = self._check_stock_production_lot(cr, lot_ids, sql)
            if res:
                raise osv.except_osv(
                    _('Error!'),
                    _('Can\'t adjust a lot while is in a stock move:' +
                      '\n%s') % res)
        return True

    def test_cancel(self, cr, uid, ids, *args):
        return True

tcv_stock_changes()


##----------------------------------------------------- tcv_stock_changes_lines


class tcv_stock_changes_lines(osv.osv):

    _name = 'tcv.stock.changes.lines'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def _get_prod_lot_id_data(self, cr, uid, prod_lot_id, context=None):
        if not prod_lot_id:
            return {}
        obj_lot = self.pool.get('stock.production.lot')
        lot = obj_lot.browse(cr, uid, prod_lot_id, context=None)
        return {
            'product_id': lot.product_id.id,
            'stock_driver': lot.stock_driver,
            'length': lot.length,
            'heigth': lot.heigth,
            'width': lot.width,
            'pieces': int(lot.stock_available / lot.lot_factor +
                          0.000001),  # To avoid rounding issues
            'qty': lot.stock_available,
            'cost_price': lot.property_cost_price,
            }

    def _add_readonly_fields(self, cr, uid, vals, context=None):
        obj_uom = self.pool.get('product.uom')
        if vals.get('prod_lot_id'):
            vals.update(self._get_prod_lot_id_data(
                cr, uid, vals['prod_lot_id'], context))
        vals.update({
            'new_pieces': vals.get('new_pieces', vals['pieces']),
            'new_length': vals.get('new_length', vals['length']),
            'new_heigth': vals.get('new_heigth', vals['heigth']),
            'new_width': vals.get('new_width', vals['width']),
            })
        new_qty = obj_uom._compute_area(
            cr, uid,
            vals.get('stock_driver', 'normal'),
            vals.get('new_pieces'),
            vals.get('new_length'),
            vals.get('new_heigth'),
            vals.get('new_width'),
            context=context) if vals.get('new_pieces') else 0
        vals.update({'new_qty': new_qty,
                     'qty_diff': new_qty - vals['qty']})

    ##--------------------------------------------------------- function fields

    _columns = {
        'line_id': fields.many2one(
            'tcv.stock.changes', 'Parent', required=True, ondelete='cascade'),
        'prod_lot_id': fields.many2one(
            'stock.production.lot', 'Production lot', required=True),
        'product_id': fields.related(
            'prod_lot_id', 'product_id', type='many2one',
            relation='product.product', string='Product',
            store=False, readonly=True),
        'stock_driver': fields.related(
            'product_id', 'stock_driver', type='char', size=12,
            relation='product.product', store=False, readonly=True),
        'length': fields.float(
            'Length (m)', digits_compute=dp.get_precision('Extra UOM data'),
            readonly=True),
        'heigth': fields.float(
            'Heigth (m)', digits_compute=dp.get_precision('Extra UOM data'),
            readonly=True),
        'width': fields.float(
            'Width (m)', digits_compute=dp.get_precision('Extra UOM data'),
            readonly=True),
        'pieces': fields.integer(
            'Pieces', readonly=True),
        'qty': fields.float(
            'Quantity', digits_compute=dp.get_precision('Product UoM'),
            readonly=True),
        'cost_price': fields.float(
            'Cost Price', digits_compute=dp.get_precision('Account'),
            readonly=True),
        'new_length': fields.float(
            'Length (m)', digits_compute=dp.get_precision('Extra UOM data')),
        'new_heigth': fields.float(
            'Heigth (m)', digits_compute=dp.get_precision('Extra UOM data')),
        'new_width': fields.float(
            'Width (m)', digits_compute=dp.get_precision('Extra UOM data')),
        'new_pieces': fields.integer(
            'Pieces', required=True),
        'new_qty': fields.float(
            'Quantity', digits_compute=dp.get_precision('Product UoM'),
            readonly=True),
        'qty_diff': fields.float(
            'Diff', digits_compute=dp.get_precision('Product UoM'),
            readonly=True),
        'location_id': fields.many2one(
            'stock.location', 'Location', readonly=False,
            ondelete='restrict', domain=[('usage', '=', 'internal')],
            help="Actual location for Lot"),
        }

    _defaults = {
        }

    _sql_constraints = [
        ('length_gt_zero', 'CHECK (new_length>=0)',
         'The length must be >= 0!'),
        ('heigth_gt_zero', 'CHECK (new_heigth>=0)',
         'The heigth must be >= 0!'),
        ('width_gt_zero', 'CHECK (new_width>=0)',
         'The width must be >= 0!'),
        ('length_gt_heigth', 'CHECK (length>=heigth)',
         'The length must be >= heigth!'),
        ('pieces_gt_zero', 'CHECK (new_pieces>=0)',
         'The pieces must be >= 0!'),
        ('lot_uniq', 'UNIQUE(line_id,prod_lot_id)',
         'The lot must be unique!'),
        ]

    ##-----------------------------------------------------

    ##----------------------------------------------------- public methods

    ##----------------------------------------------------- buttons (object)

    ##----------------------------------------------------- on_change...

    def on_change_prod_lot_id(self, cr, uid, ids, prod_lot_id):
        res = {}
        if not prod_lot_id:
            return res
        lot_data = self._get_prod_lot_id_data(
            cr, uid, prod_lot_id, context=None)
        if lot_data and \
                lot_data.get('stock_driver') not in ('tile', 'slab', 'block'):
            raise osv.except_osv(
                _('Error!'),
                _('Must indicate a lot with stock driver in ' +
                  'block, slab or tile.'))
        res.update(lot_data)
        new_data = {}
        for key in lot_data:
            new_data.update({'new_%s' % key: lot_data[key]})
        if lot_data.get('stock_driver') in ('slab', 'block') and \
                new_data.get('qty', 0) == 0:
            new_data['new_pieces'] = 1
        new_size = self.on_change_size(
            cr, uid, ids, lot_data['stock_driver'], new_data['new_length'],
            new_data['new_heigth'], new_data['new_width'],
            new_data['new_pieces'], lot_data['qty'])
        new_data.update({'new_qty': new_size['value']['new_qty'],
                         'qty_diff': new_size['value']['qty_diff']})
        res.update(new_data)
        res = {'value': res}
        return res

    def on_change_size(self, cr, uid, ids, stock_driver, new_length,
                       new_heigth, new_width, new_pieces, qty):
        res = {}
        obj_uom = self.pool.get('product.uom')
        new_length, new_heigth, new_width = obj_uom.adjust_sizes(
            new_length, new_heigth, new_width)
        new_qty = obj_uom._compute_area(
            cr, uid, stock_driver, new_pieces, new_length, new_heigth,
            new_width, context=None) if new_pieces else 0
        res.update({'new_qty': new_qty,
                    'qty_diff': new_qty - qty,
                    'new_length': new_length,
                    'new_heigth': new_heigth,
                    'new_width': new_width
                    })
        return {'value': res}

    ##----------------------------------------------------- create write unlink

    def create(self, cr, uid, vals, context=None):
        self._add_readonly_fields(cr, uid, vals, context)
        res = super(tcv_stock_changes_lines, self).\
            create(cr, uid, vals, context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        self._add_readonly_fields(cr, uid, vals, context)
        res = super(tcv_stock_changes_lines, self).\
            write(cr, uid, ids, vals, context)
        return res

    ##----------------------------------------------------- Workflow

tcv_stock_changes_lines()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
