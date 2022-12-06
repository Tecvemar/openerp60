# -*- encoding: utf-8 -*-
##############################################################################
#    Company:
#    Author: Gabriel
#    Creation Date: 2014-07-22
#    Version: 1.0
#
#    Description:
#
#
###############################################################################

#~ from datetime import datetime
from osv import fields, osv
#~ from tools.translate import _
#~ import pooler
#~ import decimal_precision as dp
#~ import time
#~ import netsvc

##------------------------------------------------- tcv_internal_forms_personal


class tcv_internal_forms_personal(osv.osv):

    _name = 'tcv.internal.forms.personal'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'personal_id': fields.many2one(
            'tcv.internal.forms', 'Personal id', required=True,
            ondelete='cascade'),
        'employee_id': fields.many2one(
            'hr.employee', 'Employee', change_default=True,
            readonly=False, required=True, ondelete='restrict'),
        'type': fields.selection(
            [('creator', 'Creator'), ('reviewed', 'Reviewed'),
            ('validator', 'Validator')],
            string='Type', required=True, readonly=False),
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

tcv_internal_forms_personal()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
