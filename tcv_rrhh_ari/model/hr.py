# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2014-06-25
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

##----------------------------------------------------------------- hr_employee


class hr_employee(osv.osv):

    _inherit = 'hr.employee'

    # The field "code" already exits in hr.employee model!
    _columns = {
        'family_chrg': fields.integer(
            'Family', required=True,
            help="CARGA FAMILIAR (VER INSTRUCTIVO) CANTIDAD"),
        }

    _defaults = {
        'family_chrg': lambda *a: 0,
        }

hr_employee()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
