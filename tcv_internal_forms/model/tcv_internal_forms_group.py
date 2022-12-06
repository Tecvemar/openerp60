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
##############################################################################

#~ from datetime import datetime
from osv import fields, osv
#~ from tools.translate import _
#~ import pooler
#~ import decimal_precision as dp
#~ import time
#~ import netsvc

##---------------------------------------------------- tcv_internal_forms_group


class tcv_internal_forms_group(osv.osv):

    _name = 'tcv.internal.forms.group'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def name_get(self, cr, uid, ids, context):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        res = []
        for item in self.browse(cr, uid, ids, context={}):
            res.append((item.id, '[%s] %s' % (item.code, item.name)))
        return res

    ##--------------------------------------------------------- function fields

    _columns = {
        'name': fields.char(
            'Name', size=64, required=False, readonly=False),
        'code': fields.char(
            'Code', size=3, required=False, readonly=False),
        'group_ids': fields.one2many(
            'tcv.internal.forms', 'group_id', 'Group id'),
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

tcv_internal_forms_group()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
