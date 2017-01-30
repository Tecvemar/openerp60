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
        #~ 'code': fields.char(
            #~ 'Code', size=16, required=True, readonly=False),
        'receivable_account_id': fields.many2one(
            'account.account', 'Account', required=False, ondelete='restrict',
            help="The account for employee receivable account moves"),
        }

    _sql_constraints = [
        #~ ('code_uniq', 'UNIQUE(code)', 'The code must be unique!'),
        ]

hr_employee()


##---------------------------------------------------------------------- hr_job


class hr_job(osv.osv):

    _inherit = 'hr.job'

    def name_get(self, cr, uid, ids, context):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        res = []
        for item in self.browse(cr, uid, ids, context={}):
            res.append((item.id, '[%s] %s' % (item.code, item.name)))
        return res

    def name_search(self, cr, user, name, args=None, operator='ilike',
                    context=None, limit=100):
        res = super(hr_job, self).\
            name_search(cr, user, name, args, operator, context, limit)
        if not res and name:
            ids = self.search(
                cr, user, [('code', 'ilike', name.upper())] + args,
                limit=limit)
            if ids:
                res = self.name_get(cr, user, ids, context=context)
        return res

    _columns = {
        'code': fields.char(
            'Code', size=16, required=True, readonly=False),
        }

    _sql_constraints = [
        ('code_uniq', 'UNIQUE(code)', 'The code must be unique!'),
        ]

hr_job()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
