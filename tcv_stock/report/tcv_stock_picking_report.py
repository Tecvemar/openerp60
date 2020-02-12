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

from datetime import datetime
from osv import fields, osv
from tools.translate import _
import pooler
import decimal_precision as dp
import time
import netsvc

##---------------------------------------------------- tcv_stock_picking_report


class tcv_stock_picking_report(osv.osv):

    _name = 'tcv.stock.picking.report'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'name': fields.char(
            'Name', size=64, required=False, readonly=False),
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
