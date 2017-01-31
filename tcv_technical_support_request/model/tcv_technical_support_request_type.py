# -*- encoding: utf-8 -*-
##############################################################################
#    Company:
#    Author: Gabriel
#    Creation Date: 2014-08-08
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

##------------------------------------------ tcv_technical_support_request_type


class tcv_technical_support_request_type(osv.osv):

    _name = 'tcv.technical.support.request.type'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'type_ids': fields.one2many('tcv.technical.support.request',
            'type_id', 'Type'),
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

tcv_technical_support_request_type()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
