# -*- encoding: utf-8 -*-
##############################################################################
#    Company:
#    Author: David Bernal
#    Creation Date: 2020-02-12
#    Version: 1.0
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

##---------------------------------------------------- tcv_stock_picking_report


class tcv_stock_picking_report(osv.osv_memory):

    _name = 'tcv.stock.picking.report'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'date_start': fields.date(
            'Date Start', required=True),
        'date_end': fields.date(
            'Date End', required=True),
        'partner_ids': fields.many2many(
            'res.partner', 'picking_report', 'picking_report_id',
            'partner_id', 'Partners', readonly=False),
        'product_ids': fields.many2many(
            'product.product', 'picking_report', 'picking_report_id',
            'product_id', 'Products', readonly=False),
        'type': fields.selection(
            [('Iternal', 'iternal'), ('In', 'in'), ('Out', 'out')],
            string='Type Picking', required=True, readonly=False),
        'state_done':fields.boolean('Done'),
        'state_cancel':fields.boolean('Cancel'),
        'state_draft':fields.boolean('Draft'),
        'state_assigned':fields.boolean('Assigned'),
        'state_confirmed':fields.boolean('Confirmed'),
        'journal_id': fields.many2one(
            'stock.journal', 'Journal', required=True,
            domain="[('type','=','cash')]", ondelete='restrict'),
        'driver_id': fields.many2one(
            'tcv.driver.vehicle', 'Driver', required=False,
            domain="[('type','=','driver')]", ondelete='restrict'),
        'vehicle_id': fields.many2one(
            'tcv.driver.vehicle', 'Vehicle', required=False,
            domain="[('type','=','vehicle')]", ondelete='restrict'),
        }

    _defaults = {
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow


tcv_stock_picking_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
