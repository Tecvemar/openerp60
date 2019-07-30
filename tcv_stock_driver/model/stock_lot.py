# -*- encoding: utf-8 -*-
##############################################################################
#    Company:
#    Author: David Bernal
#    Creation Date: 2019-07-29
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

##------------------------------------------------------------------ name_


class name_(osv.osv):

    _name = 'name.'

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

name_()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
# -*- encoding: utf-8 -*-
##############################################################################
#    Company:
#    Author: David Bernal
#    Creation Date: 2019-07-18
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

##------------------------------------------------------------------ stock_lot


class stock_lot(osv.osv):

    _inherit = 'stock.production.lot'

    _description = 'Stock Lot'

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'product_qty': fields.float('Product Quantity', readonly=True),
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

stock_lot()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
