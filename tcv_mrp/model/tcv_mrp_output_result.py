# -*- encoding: utf-8 -*-
##############################################################################
#    Company: 
#    Author: ggamez
#    Creation Date: 2016-07-18
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

##------------------------------------------------------------------ tcv_mrp_output_result


class tcv_mrp_output_result(osv.osv):

    _name = 'tcv.mrp.output.result'

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

tcv_mrp_output_result()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
