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
#~ from datetime import datetime
from osv import fields, osv
#~ from tools.translate import _
#~ import pooler
#~ import decimal_precision as dp
#~ import time
#~ import netsvc


class tcv_cost_management(osv.osv_memory):

    _name = 'tcv.cost.management'

    _description = ''

    _columns = {
        'name': fields.char(
            'name', size=64, required=False, readonly=False),
        }

    _defaults = {
        }

    def get_tcv_cost(self, cr, uid, prod_lot_id=None, product_id=None,
                     context=None):
        context = context or {}
        if prod_lot_id:
            obj_lot = self.pool.get('stock.production.lot')
            lot = obj_lot.browse(cr, uid, prod_lot_id, context)
            if lot and lot.property_cost_price:
                return lot.property_cost_price
            elif lot.product_id and not \
                    context.get('property_cost_price_only'):
                return lot.product_id.property_standard_price or \
                    lot.product_id.standard_price
        if product_id:
            obj_prd = self.pool.get('product.product')
            prd = obj_prd.browse(cr, uid, product_id, context)
            if prd:
                return prd.property_standard_price or prd.standard_price
        return 0


tcv_cost_management()
