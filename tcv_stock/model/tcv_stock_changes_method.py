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
#~ from tools.translate import _
#~ import pooler
#~ import decimal_precision as dp
#~ import time
#~ import netsvc

##---------------------------------------------------- tcv_stock_changes_method


class tcv_stock_changes_method(osv.osv):

    _name = 'tcv.stock.changes.method'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'name': fields.char(
            'Name', size=64, required=False, readonly=False),
        'journal_id': fields.many2one(
            'account.journal', 'Journal', required=False,
            domain="[('type','=','general')]", ondelete='restrict',
            help="Journal for account move (if required)"),
        'stock_journal_id': fields.many2one(
            'stock.journal', 'Stock Journal', required=True,
            select=True, ondelete='restrict',
            help="Stock Journal for stock move"),
        'location_id': fields.many2one(
            'stock.location', 'Location', required=True, ondelete='restrict',
            domain="[('scrap_location','=',True)]",
            help="Location for/to scrap"),
        'type': fields.selection(
            [('account', 'Accounting'), ('stock', 'Stocking')],
            string='Type', required=True),
        }

    _defaults = {
        'type': lambda *a: 'account',
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_stock_changes_method()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
