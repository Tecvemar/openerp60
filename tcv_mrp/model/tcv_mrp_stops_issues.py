# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2014-10-30
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

##-------------------------------------------------------- tcv_mrp_stops_issues


class tcv_mrp_stops_issues(osv.osv):

    _name = 'tcv.mrp.stops.issues'

    _description = ''

    _order = 'code'

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
        'code': fields.char(
            'Code', size=8, required=True, readonly=False, search=True),
        'name': fields.char(
            'Name', size=128, required=True, readonly=False),
        'type': fields.selection(
            [('gangsaw', 'Gangsaw'), ('polish', 'Polish')],
            string='Type', required=True),
        }

    _defaults = {
        'type': lambda *a: 'gangsaw',
        }

    _sql_constraints = [
        ('code_uniq', 'UNIQUE(code,type)', 'The code must be unique!'),
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_mrp_stops_issues()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
