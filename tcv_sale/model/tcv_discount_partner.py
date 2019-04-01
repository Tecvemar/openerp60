# -*- encoding: utf-8 -*-
##############################################################################
#    Company:
#    Author: David Bernal
#    Creation Date: 2019-03-14
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
import decimal_precision as dp
#~ import time
#~ import netsvc

##------------------------------------------------------------ tcv_discount_partner


class tcv_discount_partner(osv.osv):

    _name = 'tcv.discount.partner'

    _description = 'Dicount for Partnerts'

    _order = 'discount_percentage desc'

    ##-----------------------------------------------------------------------to

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'name': fields.char(
            'Name', size=64, required=False, readonly=False),
        'discount_percentage': fields.float('Discount Percentage',
            digits_compute=dp.get_precision('Account'),
            required=True, readonly=False,
            ),
        }

    _defaults = {
        }

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', 'The name must be unique!'),
        ('discount_percentage_unique', 'UNIQUE(discount_percentage)',
         'The discount must be unique!'),
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_discount_partner()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
