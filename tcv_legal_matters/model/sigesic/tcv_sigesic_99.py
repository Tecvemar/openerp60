# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2014-02-17
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

##------------------------------------------------------------ tcv_sigesic_9901


class tcv_sigesic_9901(osv.osv):

    _name = 'tcv.sigesic.9901'

    _description = 'HS Codes'

    ##-------------------------------------------------------------------------

    def name_get(self, cr, uid, ids, context):
        if not len(ids):
            return []
        res = []
        so_brw = self.browse(cr, uid, ids, context)
        for item in so_brw:
            res.append((item.id, '%s' % (item.code)))
        return res

    def name_search(self, cr, user, name, args=None, operator='ilike',
                    context=None, limit=100):
        #~ Based on account.account.name_search...
        res = super(tcv_sigesic_9901, self).\
            name_search(cr, user, name, args, operator, context, limit)
        if not res and name:
            ids = self.search(cr, user, [('code', '=like', name + "%")] + args,
                              limit=limit)
            if ids:
                res = self.name_get(cr, user, ids, context=context)
        return res

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'code': fields.char('Code', size=16, select=True, required=False,
                            readonly=False),
        'name': fields.char('Name', size=128, required=False, readonly=False),
        'description': fields.char('Description', size=256, required=False,
                                   readonly=False),
        'ministry': fields.char('Ministry', size=16, required=False,
                                readonly=False),
        'list_num': fields.selection([('1', 'List 1'), ('2', 'List 2')],
                                     string='List', required=False,
                                     readonly=False),

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

tcv_sigesic_9901()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
