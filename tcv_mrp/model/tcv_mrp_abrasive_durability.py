# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description:
#
#
##############################################################################
from osv import fields, osv
import decimal_precision as dp
import time


##------------------------------------------ tcv_mrp_abrasive_durability


class tcv_mrp_abrasive_durability(osv.osv):

    _name = 'tcv.mrp.abrasive.durability'

    _description = ''

    ##------------------------------------------------------------------

    ##-------------------------------------------------- function fields

    _columns = {
        'ref': fields.char(
            'Reference', size=16, required=True, readonly=False),
        'date': fields.date(
            'Date', required=True, select=True),
        'name': fields.char(
            'Name', size=64, required=True, readonly=False),
        'note': fields.char(
            'Note', size=64, readonly=False),
        'categ_id': fields.many2one(
            'product.category', 'Category', required=True,
            change_default=True,
            domain="[('type','=','normal')]",
            help="Select category for the current table " +
            "(accounting related"),
        'line_ids': fields.one2many(
            'tcv.mrp.abrasive.durability.lines', 'line_id', 'Detail'),
        }

    _defaults = {
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        }

    _sql_constraints = [
        ]

    ##------------------------------------------------------------------

    def _get_total_cost_m2(self, cr, uid, abrasive_id, context=None):
        item = self.browse(cr, uid, abrasive_id, context)
        total_cost_m2 = 0
        for line in item.line_ids:
            total_cost_m2 += line.price_m2
        return total_cost_m2

    ##----------------------------------------------------- on_change...

    ##---------------------------------------------- create write unlink

    ##--------------------------------------------------------- Workflow

tcv_mrp_abrasive_durability()


##------------------------------------ tcv_mrp_abrasive_durability_lines


class tcv_mrp_abrasive_durability_lines(osv.osv):

    _name = 'tcv.mrp.abrasive.durability.lines'

    _description = ''

    _order = 'head'

    ##------------------------------------------------------------------

    ##-------------------------------------------------- function fields

    def _compute_all(self, cr, uid, ids, name, arg, context=None):
        if context is None:
            context = {}
        if not len(ids):
            return []
        res = {}
        obj_cst = self.pool.get('tcv.cost.management')
        obj_lin = self.pool.get('tcv.mrp.abrasive.durability.lines')
        for line in obj_lin.browse(cr, uid, ids, context=context):
            prod_lot_id = line.prod_lot_id.id if line.prod_lot_id else None
            price_unit = obj_cst.get_tcv_cost(
                cr, uid, prod_lot_id, line.product_id.id, context)
            price_set = price_unit * line.set_of
            price_m2 = round(price_set / line.durability, 6)
            res[line.id] = {'price_unit': price_unit,
                            'price_set': price_set,
                            'price_m2': price_m2,
                            'estimated_m2': int(
                                line.product_id.qty_available /
                                line.set_of) * line.durability
                            }
        return res

    ##------------------------------------------------------------------

    _columns = {
        'line_id': fields.many2one(
            'tcv.mrp.abrasive.durability', 'Detail', required=True,
            ondelete='cascade'),
        'head': fields.integer(
            'Head #', required=True),
        'product_id': fields.many2one(
            'product.product', 'Product', ondelete='restrict', required=True),
        'prod_lot_id': fields.many2one(
            'stock.production.lot', 'lot Nº', required=False),
        'set_of': fields.integer(
            'Set of', required=True,
            help="Quantity of units in a set"),
        'durability': fields.integer(
            'Durability (m2)', required=True,
            help="Quantity of m2 procesed by set"),
        'price_unit': fields.function(
            _compute_all, method=True,
            type='float', string='Unit cost',
            digits_compute=dp.get_precision('Account'),
            multi='all', store=False),
        'price_set': fields.function(
            _compute_all, method=True, type='float', string='Set cost',
            digits_compute=dp.get_precision('Account'), multi='all'),
        'price_m2': fields.function(
            _compute_all, method=True, type='float', string='m2 cost',
            digits=(12, 6), multi='all', help="Estimated cost per m2"),
        'estimated_m2': fields.function(
            _compute_all, method=True, type='integer', string='m2 estimated',
            multi='all',
            help="Estimated production capacity with the available stock"),

        }

    _defaults = {
        'set_of': lambda *a: 6,
        }

    _sql_constraints = [
        ('head_unique', 'UNIQUE(line_id,head)', 'The head # must be uniqe'),
        ('head_range', 'CHECK(head between 1 and 24)',
         'The head # must be in 1-24 range'),
        ('set_of_range', 'CHECK(set_of between 5 and 6)',
         'The head # must be in 5-6 range'),
    ]

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_mrp_abrasive_durability_lines()
