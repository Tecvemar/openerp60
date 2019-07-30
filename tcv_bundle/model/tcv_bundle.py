# -*- encoding: utf-8 -*-
##############################################################################
#    Company:
#    Author: Gabriel
#    Creation Date: 2015-07-22
#    Version: 1.0
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

##------------------------------------------------------------------ tcv_bundle


class tcv_bundle(osv.osv):

    _name = 'tcv.bundle'

    _description = 'Modulo para administrar bundle'

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def _check_product(self, cr, uid, ids, context=None):
        '''
        Check if the account voucher is duplicates
        fields to be compared:
            type
            partner_id
            amount
            journal_id
            reference
            payment_doc
            id (to avoid "self.id" error)
        returns True if not duplicated
        '''
        res = True
        for item in self.browse(cr, uid, ids, context=context):
            product_id = item.product_id.id
            for line in item.line_ids:
                res = res and line.product_id.id == product_id
        return res

    def button_available(self, cr, uid, ids, context=None):
        vals = {'state': 'available'}
        res = self.write(cr, uid, ids, vals, context)
        return res

    def button_draft(self, cr, uid, ids, context=None):
        vals = {'state': 'draft'}
        res = self.write(cr, uid, ids, vals, context)
        return res

    ##--------------------------------------------------------- function fields

    def _compute_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for item in self.browse(cr, uid, ids, context=context):
            data = {'pieces': 0,
                    'product_qty': 0.0}
            for lot in item.line_ids:
                data['pieces'] += 1
                data['product_qty'] += lot.lot_factor
            res[item.id] = data
        return res

    def _compute_lot_list(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for item in self.browse(cr, uid, ids, context=context):
            l = []
            for line in item.line_ids:
                l.append(line.prod_lot_id.full_name)
            res[item.id] = {'lot_list': ', '.join(l)}
        return res

    _columns = {
        'name': fields.char(
            'Name', size=16, required=True, readonly=True,
            states={'draft': [('readonly', False)]}),
        'company_id': fields.many2one(
            'res.company', 'Company', required=True, readonly=True,
            states={'draft': [('readonly', False)]}, ondelete='restrict'),
        'product_id': fields.many2one(
            'product.product', 'Product', ondelete='restrict', required=True,
            readonly=True, states={'draft': [('readonly', False)]}),
        'location_id': fields.many2one(
            'stock.location', 'Location', readonly=False,
            ondelete='restrict'),
        'pieces': fields.function(
            _compute_all, method=True, type='float', string='Pieces',
            multi='all', digits=0, readonly=True,
            states={'draft': [('readonly', False)]}),
        'product_qty': fields.function(
            _compute_all, method=True, type='float', string='Quantity',
            digits_compute=dp.get_precision('Product UoM'), multi='all',
            readonly=True, states={'draft': [('readonly', False)]}),
        'image': fields.binary(
            "Image", help="Select image here", readonly=True,
            states={'draft': [('readonly', False)]}),
        'weight_net': fields.float(
            'Weight net', digits_compute=dp.get_precision('Account'),
            readonly=True, states={'draft': [('readonly', False)]}),
        'date': fields.date(
            'Date', required=True, readonly=True,
            states={'draft': [('readonly', False)]}, select=True),
        'line_ids': fields.one2many(
            'tcv.bundle.lines', 'bundle_id', 'Lots', readonly=True,
            states={'draft': [('readonly', False)]}),
        'lot_list': fields.function(
            _compute_lot_list, method=True, type='char', string='lot list',
            size=256, store=False, multi='all', readonly=True,
            states={'draft': [('readonly', False)]}),
        'reserved': fields.boolean(
            'Reserved', required=True, readonly=False,
            states={'draft': [('readonly', False)]}),
        'state': fields.selection(
            [('draft', 'Draft'), ('available', 'Available')],
            string='Status', required=True, readonly=True),
        'print': fields.boolean(
            'Imprimir'),

        }

    _defaults = {
        'name': lambda *a: '/',
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company').
        _company_default_get(cr, uid, self._name, context=c),
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        'state': lambda *a: 'draft',
        'reserved': lambda *a: False,
        }

    _constraints = [
        (_check_product,
         'Error ! Product mismatch.',
         ['product_id', 'parent.product_id'])
        ]

    _sql_constraints = [
        ('name_uniq',
            'UNIQUE(name)',
            'The name must be unique!'),
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    def create(self, cr, uid, vals, context=None):
        if not vals.get('name') or vals.get('name') == '/':
            vals.update({'name': self.pool.get('ir.sequence').get(
                cr, uid, 'tcv.bundle')})
        obj_bun = self.pool.get('tcv.bundle')
        if vals.get('bundle_id') and vals.get('product_id'):
            bun_brw = obj_bun.browse(
                cr, uid, vals['bundle_id'], context=context)
            if vals['product_id'] != bun_brw.product_id.id:
                raise osv.except_osv(
                    _('Error!'),
                    _('The bundle product and lot product must be the same.'))
        res = super(tcv_bundle, self).create(cr, uid, vals, context)
        return res

    def unlink(self, cr, uid, ids, context=None):
        for item in self.browse(cr, uid, ids, context={}):
            if item.state != 'draft':
                raise osv.except_osv(
                    _('Error!'),
                    _('Can\'t delete a bundle while state <> "Draft".'))
            elif item.reserved:
                raise osv.except_osv(
                    _('Error!'),
                    _('Can\'t delete a reserved bundle.'))
        res = super(tcv_bundle, self).unlink(cr, uid, ids, context)
        return res

    ##---------------------------------------------------------------- Workflow

tcv_bundle()


##------------------------------------------------------------ tcv_bundle_lines


class tcv_bundle_lines(osv.osv):

    _name = 'tcv.bundle.lines'

    _description = 'Bundle product lines'

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'bundle_id': fields.many2one(
            'tcv.bundle', 'String', required=True, ondelete='cascade'),
        'product_bundle_id': fields.related(
            'bundle_id', 'product_id', type='many2one',
            relation='product.product', string='Product',
            store=False, readonly=True),
        'prod_lot_id': fields.many2one(
            'stock.production.lot', 'Production lot', required=True),
        'product_id': fields.related(
            'prod_lot_id', 'product_id', type='many2one',
            relation='product.product', string='Product',
            store=False, readonly=True),
        'lot_factor': fields.related(
            'prod_lot_id', 'lot_factor', type='float', string='Vol (m3)',
            store=False, digits_compute=dp.get_precision('Product UoM'),
            readonly=True),
        'length': fields.related(
            'prod_lot_id', 'length', type='float', string='Length',
            store=False, digits_compute=dp.get_precision('Extra UOM data'),
            readonly=True),
        'width': fields.related(
            'prod_lot_id', 'width', type='float', string='Width', store=False,
            digits_compute=dp.get_precision('Extra UOM data'), readonly=True),
        'heigth': fields.related(
            'prod_lot_id', 'heigth', type='float', string='Heigth',
            store=False, digits_compute=dp.get_precision('Extra UOM data'),
            readonly=True),
        }

    _defaults = {
        }

    _sql_constraints = [
        ('prod_lot_uniq',
            'UNIQUE(prod_lot_id)',
            'The prod lot must be unique!'),
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    def on_change_prod_lot_id(self, cr, uid, ids, prod_lot_id):
        res = {}
        if prod_lot_id:
            lot = self.pool.get('stock.production.lot').browse(
                cr, uid, prod_lot_id, context=None)
            res = {'value': {}}
            res['value'].update({'product_id': lot.product_id.id,
                                 'length': lot.length,
                                 'width': lot.width,
                                 'heigth': lot.heigth,
                                 'lot_factor': lot.lot_factor})
        return res

    ##----------------------------------------------------- create write unlink


    ##---------------------------------------------------------------- Workflow

tcv_bundle_lines()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
