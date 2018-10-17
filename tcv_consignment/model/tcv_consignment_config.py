# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2018-10-17
#    Version: 0.0.0.1
#
#    Description:
#
#
##############################################################################

# ~ from datetime import datetime
from osv import fields, osv
# ~ from tools.translate import _
# ~ import pooler
# ~ import decimal_precision as dp
# ~ import time
# ~ import netsvc

##------------------------------------------------------ tcv_consignment_config


class tcv_consignment_config(osv.osv):

    _name = 'tcv.consignment.config'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'name': fields.char(
            'Name', size=64, required=False, readonly=False),
        'partner_id': fields.many2one(
            'res.partner', 'Partner', change_default=True,
            readonly=False, required=True, ondelete='restrict'),
        'stock_location_id': fields.many2one(
            'stock.location', 'Stock location', change_default=True,
            readonly=False, required=True, ondelete='restrict',
            help="Destination location for material placed on consignment"),
        'stock_journal_id': fields.many2one(
            'stock.journal', 'Stock journal', change_default=True,
            readonly=False, required=True, ondelete='restrict',
            help="Stock journal to register moves"),
        'inventory_account_id': fields.many2one(
            'account.account', 'Inventory accoount', change_default=True,
            readonly=False, required=True, ondelete='restrict',
            help="Accounting account for the value of consigned inventory"),
        'order_policy': fields.selection([
            ('prepaid', 'Payment Before Delivery'),
            ('manual', 'Shipping & Manual Invoice'),
            ('postpaid', 'Invoice On Order After Delivery'),
            ('picking', 'Invoice From The Picking'),
            ], 'Shipping Policy', required=True, readonly=False,
            help="""The Shipping Policy is used to synchronise invoice and
            delivery operations.
    - The 'Pay Before delivery' choice will first generate the invoice and then
        generate the picking order after the payment of this invoice.
    - The 'Shipping & Manual Invoice' will create the picking order directly
        and wait for the user to manually click on the 'Invoice' button to
        generate the draft invoice.
    - The 'Invoice On Order After Delivery' choice will generate the draft
        invoice based on sales order after all picking lists have been
        finished.
    - The 'Invoice From The Picking' choice is used to create an invoice during
        the picking process."""),
        'payment_term': fields.many2one(
            'account.payment.term', 'Payment Term'),
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


tcv_consignment_config()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
