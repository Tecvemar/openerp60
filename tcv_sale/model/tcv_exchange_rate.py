# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: David Bernal
#    Creation Date: 2020-11-23
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

##----------------------------------------------------------- tcv_exchange_rate


class tcv_exchange_rate(osv.osv):

    _name = 'tcv.exchange.rate'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'name': fields.char(
            'Name', size=64, required=False, readonly=False),
        'date': fields.date(
            'Date', required=True, readonly=False, select=True),
        'rate': fields.float(
            'Actual Rate', digits_compute=dp.get_precision('Account'),
            required=True),
        'bcv_rate': fields.float(
            'BCV Rate', digits_compute=dp.get_precision('Account'),
            required=False),
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


tcv_exchange_rate()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
