# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date: 20/08/2012
#    Version: 0.0.0.0
#
#    Description: Handle cancel_voucher (check options)
#
#
##############################################################################
from datetime import datetime
from osv import fields,osv
from tools.translate import _
import pooler
import decimal_precision as dp
import time

##---------------------------------------------------------------------------------------- tcv_account_voucher_cancel

class tcv_account_voucher_cancel(osv.osv_memory):

    _name = 'tcv.account.voucher.cancel'

    _description = 'Handle cancel_voucher (check options)'

    ##------------------------------------------------------------------------------------

    ##------------------------------------------------------------------------------------ function fields

    _columns = {'set_state_to': fields.selection([('available', 'Available'),('cancel', 'Cancelled')], string='Leave check in state', required=True, readonly=False),
        }

    _defaults = {
        }

    _sql_constraints = [        
        ]

    ##------------------------------------------------------------------------------------

    ##------------------------------------------------------------------------------------ on_change...

    ##------------------------------------------------------------------------------------ create write unlink

    ##------------------------------------------------------------------------------------ Workflow

tcv_account_voucher_cancel()
