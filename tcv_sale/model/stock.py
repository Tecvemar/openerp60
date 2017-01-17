# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2015-08-12
#    Version: 0.0.0.1
#
#    Description:
#
#
##############################################################################

#~ from datetime import datetime
from osv import osv
from tools.translate import _
#~ import pooler
#~ import decimal_precision as dp
#~ import time
#~ import netsvc

##-------------------------------------------------------- stock_production_lot


class stock_production_lot(osv.osv):

    _inherit = 'stock.production.lot'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        }

    _defaults = {
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    def check_lot_for_sale(self, cr, uid, lot_brw, quantity, context):
        """
        ids: list of lot ids
        Check if this lot is used or compromised in any other document
        """
        res = []
        if lot_brw.stock_available < quantity:
            res.append({'error': _(
                'No stock available for lot: %s') % lot_brw.name})



        return res

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

stock_production_lot()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
