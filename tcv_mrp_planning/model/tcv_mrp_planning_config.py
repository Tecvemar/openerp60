# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2015-09-25
#    Version: 0.0.0.1
#
#    Description:
#
#
##############################################################################
#~
#~ from datetime import datetime
from osv import fields, osv
#~ from tools.translate import _
#~ import pooler
#~ import decimal_precision as dp
#~ import time
#~ import netsvc

##----------------------------------------------------- tcv_mrp_planning_config


class tcv_mrp_planning_config(osv.osv):

    _name = 'tcv.mrp.planning.config'

    _description = ''

    _order = 'sequence,name'

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'name': fields.char(
            'Name', size=64, required=False, readonly=False),
        'product_id1': fields.many2one(
            'product.product', 'Block', ondelete='restrict'),
        'product_id2': fields.many2one(
            'product.product', 'Process', ondelete='restrict'),
        'product_id3': fields.many2one(
            'product.product', 'Finished', ondelete='restrict'),
        'sequence': fields.integer(
            'Sequence'),
        'quarry_location_id': fields.many2one(
            'stock.location', 'Quarry location', readonly=False,
            ondelete='restrict',
            help=""),
        'plant_location_id': fields.many2one(
            'stock.location', 'Plant location', readonly=False,
            ondelete='restrict',
            help=""),
        'stock_location_id': fields.many2one(
            'stock.location', 'Stock location', readonly=False,
            ondelete='restrict',
            help=""),
        }

    _defaults = {
        'quarry_location_id': lambda *a: 3511,
        'plant_location_id': lambda *a: 3510,
        'stock_location_id': lambda *a: 105,
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_mrp_planning_config()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
