# -*- encoding: utf-8 -*-
##############################################################################
#    Company:
#    Author: Gabriel
#    Creation Date: 2014-08-11
#    Version: 2.0
#
#    Description:Revisado para produccion 23/10/2014
#
#
##############################################################################

from datetime import datetime
from osv import fields, osv
from tools.translate import _
import pooler
import decimal_precision as dp
import time
import netsvc

##-------------------------------------------------------------- tcv_block_file


class tcv_block_file(osv.osv):

    _name = 'tcv.block.file'

    _description = ''


    ##-------------------------------------------------------------------------
    STATE_SELECTION = [
        ('draft', 'Draft'),
        ('done','Done'),
        ]

    ##------------------------------------------------------- _internal methods

    def _get_prod_lot_id_data(self, cr, uid, prod_lot_id, context=None):
        if not prod_lot_id:
            return {}
        obj_lot = self.pool.get('stock.production.lot')
        lot_brw = obj_lot.browse(cr, uid, prod_lot_id, context={})
        location_id = obj_lot.get_actual_lot_location(cr, uid, prod_lot_id)
        obj_iln = self.pool.get('account.invoice.line')
        iln_ids = obj_iln.search(cr, uid, [('prod_lot_id', '=', prod_lot_id)])
        return {'product_id': lot_brw.product_id.id,
                'length': lot_brw.length,
                'heigth': lot_brw.heigth,
                'width': lot_brw.width,
                'location_id': location_id and location_id[0] \
                    if len(location_id) == 1 else 0,
                'quality_id': lot_brw.product_id.quality_id.id,
                'volume': lot_brw.lot_factor,
                'price_unit': lot_brw.property_cost_price,
                'total_cost': lot_brw.property_cost_price * lot_brw.lot_factor,
                'total_weight': lot_brw.product_id.weight * lot_brw.lot_factor,
                }

    def _compute_document_ids(self, cr, uid, ids, name, args, context=None):
        res = {}
        #~ obj_pln = self.pool.get(context.get('pool_model'))
        sql = context.get('sql_query')
        for item in self.browse(cr, uid, ids, context=context):
            cr.execute(sql % item.prod_lot_id.id)
            document_ids = cr.fetchall()
            res[item.id] = [x[0] for x in document_ids]
        return res

    def _compute_purchase_ids(self, cr, uid, ids, name, args, context=None):
        context = context or {}
        context.update({
            'sql_query': '''select distinct order_id
                            from purchase_order_line
                            where prod_lot_id = %s'''})
        return self._compute_document_ids(
            cr, uid, ids, name, args, context=context)

    def _compute_invoice_ids(self, cr, uid, ids, name, args, context=None):
        context = context or {}
        context.update({
            'sql_query': '''select distinct invoice_id
                            from account_invoice_line
                            where prod_lot_id = %s'''})
        return self._compute_document_ids(
            cr, uid, ids, name, args, context=context)

    def _compute_cost_ids(self, cr, uid, ids, name, args, context=None):
        context = context or {}
        context.update({
            'sql_query': '''select distinct line_id
                            from tcv_block_cost_lots
                            where prod_lot_id = %s'''})
        return self._compute_document_ids(
            cr, uid, ids, name, args, context=context)

    def _compute_mrp_ids(self, cr, uid, ids, name, args, context=None):
        context = context or {}
        context.update({
            'sql_query': '''select distinct id
                            from tcv_mrp_gangsaw_blocks
                            where prod_lot_id = %s'''})
        return self._compute_document_ids(
            cr, uid, ids, name, args, context=context)

    def _compute_stock_ids(self, cr, uid, ids, name, args, context=None):
        context = context or {}
        context.update({
            'sql_query': '''select distinct id
                            from stock_move
                            where prodlot_id = %s'''})
        return self._compute_document_ids(
            cr, uid, ids, name, args, context=context)

    def _compute_measures(self, cr, uid, measures, context=None):
        obj_uom = self.pool.get('product.uom')
        volume = obj_uom._compute_area_block(
            cr, uid,
            measures.get('length', 0),
            measures.get('heigth', 0),
            measures.get('width', 0),
            )
        volume_tvm = obj_uom._compute_area_block(
            cr, uid,
            measures.get('length_tvm', 0),
            measures.get('heigth_tvm', 0),
            measures.get('width_tvm', 0),
            )
        volume_mrp = obj_uom._compute_area_block(
            cr, uid,
            measures.get('length_mrp', 0),
            measures.get('heigth_mrp', 0),
            measures.get('width_mrp', 0),
            )
        length_dif = measures.get('length', 0) - measures.get('length_tvm', 0)
        heigth_dif = measures.get('heigth', 0) - measures.get('heigth_tvm', 0)
        width_dif = measures.get('width', 0) - measures.get('width_tvm', 0)
        volume_dif = volume - volume_tvm
        measures.update({
            'volume_tvm': volume_tvm,
            'volume_mrp': volume_mrp,
            'length_dif': length_dif,
            'heigth_dif': heigth_dif,
            'width_dif': width_dif,
            'volume_dif': volume_dif,
            })
        return measures


    ##--------------------------------------------------------- function fields

    def _compute_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for item in self.browse(cr, uid, ids, context=context):
            res[item.id] = {}
        return res

    _columns = {
        'date': fields.date(
            'Date', required=False, readonly=True, select=True),
        'prod_lot_id': fields.many2one(
            'stock.production.lot','Production lot', required=True,
            domain=[('stock_driver','=','block')], states={
            'draft': [('readonly', False)]}, readonly=True),
        'product_id': fields.many2one(
            'product.product', 'Product', readonly=True, ondelete='restrict'),
        'location_id': fields.many2one(
            'stock.location', 'Location id', readonly=True),
        'quality_id': fields.many2one(
            'product.product.features', 'Quality', readonly=True,
            domain=[('type','=','quality')], ondelete='restrict'),
        'length': fields.float(
            'Length', digits_compute=dp.get_precision('Extra UOM data'),
            readonly=True),
        'heigth': fields.float(
            'Heigth', digits_compute=dp.get_precision('Extra UOM data'),
            readonly=True),
        'width': fields.float(
            'Width', digits_compute=dp.get_precision('Extra UOM data'),
            readonly=True),
        'volume': fields.float(
            'Volume', digits_compute=dp.get_precision('Product UoM'),
            readonly=True),
        'length_tvm': fields.float(
            'Length tvm', digits_compute=dp.get_precision('Extra UOM data'),
            states={'draft': [('readonly', False)]}, readonly=True),
        'heigth_tvm': fields.float(
            'Heigth tvm', digits_compute=dp.get_precision('Extra UOM data'),
            states={'draft': [('readonly', False)]}, readonly=True),
        'width_tvm': fields.float(
            'Width tvm', digits_compute=dp.get_precision('Extra UOM data'),
            states={'draft': [('readonly', False)]}, readonly=True),
        'volume_tvm': fields.float(
            'Volume tvm', digits_compute=dp.get_precision('Product UoM'),
            readonly=True),
        'length_dif': fields.float(
            'Length dif', digits_compute=dp.get_precision('Extra UOM data'),
            readonly=True),
        'heigth_dif': fields.float(
            'Heigth dif', digits_compute=dp.get_precision('Extra UOM data'),
            readonly=True),
        'width_dif': fields.float(
            'Width dif', digits_compute=dp.get_precision('Extra UOM data'),
            readonly=True),
        'volume_dif': fields.float(
            'Volume dif', digits_compute=dp.get_precision('Product UoM'),
            readonly=True),
        'length_mrp': fields.float(
            'Length mrp', digits_compute=dp.get_precision('Extra UOM data'),
            states={'draft': [('readonly', False)]}, readonly=True),
        'heigth_mrp': fields.float(
            'Heigth mrp', digits_compute=dp.get_precision('Extra UOM data'),
            states={'draft': [('readonly', False)]}, readonly=True),
        'width_mrp': fields.float(
            'Width mrp', digits_compute=dp.get_precision('Extra UOM data'),
            states={'draft': [('readonly', False)]}, readonly=True),
        'volume_mrp': fields.float(
            'Volume Mrp', digits_compute=dp.get_precision('Product UoM'),
            readonly=True),
        'price_unit': fields.float(
            'Unit price', digits_compute=dp.get_precision('Account'),
            readonly=True),
        'total_cost': fields.function(_compute_all, method=True,
            type='float', string='Total cost',
            digits_compute=dp.get_precision('Account'), multi='all'),
        'total_weight': fields.function(_compute_all, method=True,
            type='float', string='Total weight',
            digits_compute=dp.get_precision('Account'), multi='all'),
        'hairs': fields.boolean(
            'Hairs', required=True, states={'draft': [('readonly', False)]},
            readonly=True),
        'cracks': fields.boolean(
            'Cracks', required=True, states={'draft': [('readonly', False)]},
            readonly=True),
        'veins': fields.boolean(
            'Veins', required=True, states={'draft': [('readonly', False)]},
            readonly=True),
        'studs': fields.boolean(
            'Studs', required=True, states={'draft': [('readonly', False)]},
            readonly=True),
        'regular': fields.boolean(
            'Regular', required=True, states={'draft': [('readonly', False)]},
            readonly=True),
        'purchase_ids': fields.function(
            _compute_purchase_ids, method=True, relation='purchase.order',
            type='one2many', string='Purchase orders'),
        'invoice_ids': fields.function(
            _compute_invoice_ids, method=True, relation='account.invoice',
            type='one2many', string='Invoices'),
        'cost_ids': fields.function(
            _compute_cost_ids, method=True, relation='tcv.block.cost',
            type='one2many', string='Block costs'),
        'mrp_ids': fields.function(
            _compute_mrp_ids, method=True, relation='tcv.mrp.gangsaw.blocks',
            type='one2many', string='MRP'),
        'stock_ids': fields.function(
            _compute_stock_ids, method=True, relation='stock.move',
            type='one2many', string='Stock move'),
        'state': fields.selection(
            STATE_SELECTION, string='State', required=True, readonly=True),
        }

    _defaults = {
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        'state': lambda *a: 'draft',
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    #~ def on_change_prod_lot_id(self, cr, uid, ids, prod_lot_id):
        #~ res = {'product_id': 0,
               #~ 'length': 0,
               #~ 'heigth': 0,
               #~ 'width': 0,
               #~ 'location_id': 0,
               #~ 'quality_id': 0,
               #~ 'volume': 0,
               #~ 'price_unit': 0,
               #~ 'total_cost': 0,}
        #~ if not prod_lot_id:
            #~ return {'value': res}
        #~ res.update(self._get_prod_lot_id_data(cr, uid, prod_lot_id))
        #~ return {'value': res}

    def on_change_measures(self, cr, uid, ids, prod_lot_id,
                           length, heigth, width,
                           length_tvm, heigth_tvm, width_tvm,
                           length_mrp, heigth_mrp, width_mrp):
        res = {'product_id': 0,
               'length': 0,
               'heigth': 0,
               'width': 0,
               'location_id': 0,
               'quality_id': 0,
               'volume': 0,
               'price_unit': 0,
               'total_cost': 0,
               'total_weight': 0,}
        if not prod_lot_id:
            return {'value': res}
        measures = self._get_prod_lot_id_data(cr, uid, prod_lot_id)
        measures.update({'length_tvm': length_tvm,
                         'heigth_tvm': heigth_tvm,
                         'width_tvm': width_tvm,
                         'length_mrp': length_mrp,
                         'heigth_mrp': heigth_mrp,
                         'width_mrp': width_mrp,
                         })
        res = self._compute_measures(cr, uid, measures)
        return {'value': res}

    ##----------------------------------------------------- create write unlink

    def create(self, cr, uid, vals, context=None):
        if vals.get('prod_lot_id'):
            vals.update(self._get_prod_lot_id_data(
                cr, uid, vals['prod_lot_id'], context))
            vals.update(self._compute_measures(
                cr, uid, vals, context=context))
        res = super(tcv_block_file, self).create(cr, uid, vals, context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        for item in self.browse(cr, uid, ids, context={}):
            prod_lot_id = vals.get('prod_lot_id', item.prod_lot_id.id)
            if prod_lot_id:
                vals.update(self._get_prod_lot_id_data(
                    cr, uid, prod_lot_id, context))
                vals.update({
                    'length_tvm': vals.get('length_tvm', item.length_tvm),
                    'heigth_tvm': vals.get('heigth_tvm', item.heigth_tvm),
                    'width_tvm': vals.get('width_tvm', item.width_tvm),
                    'length_mrp': vals.get('length_mrp', item.length_mrp),
                    'heigth_mrp': vals.get('heigth_mrp', item.heigth_mrp),
                    'width_mrp': vals.get('width_mrp', item.width_mrp),
                    })
                vals.update(self._compute_measures(
                    cr, uid, vals, context=context))
            res = super(tcv_block_file, self).write(cr, uid, item.id,
                                                    vals, context)
        return res

    ##---------------------------------------------------------------- Workflow

    def button_done(self, cr, uid, ids, context=None):
        vals = {'state': 'done'}
        return self.write(cr, uid, ids, vals, context)

    def button_draft(self, cr, uid, ids, context=None):
        vals = {'state': 'draft'}
        return self.write(cr, uid, ids, vals, context)


    def test_done(self, cr, uid, ids, *args):
        return True

    def test_draft(self, cr, uid, ids, *args):
        return True

tcv_block_file()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
