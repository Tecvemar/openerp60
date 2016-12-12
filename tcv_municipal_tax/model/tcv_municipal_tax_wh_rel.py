# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2016-12-05
#    Version: 0.0.0.1
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

##------------------------------------------------------------------ tcv_municipal_tax_wh_rel


class tcv_municipal_tax_wh_rel(osv.osv):

    _name = 'tcv.municipal.tax.wh.rel'

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

tcv_municipal_tax_wh_rel()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
