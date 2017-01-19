# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2014-06-18
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

##------------------------------------------------------ tcv_payroll_import_job


class tcv_payroll_import_job(osv.osv):

    _name = 'tcv.payroll.import.job'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def name_get(self, cr, uid, ids, context):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        res = []
        for item in self.browse(cr, uid, ids, context={}):
            res.append((item.id, '[%s] %s' % (item.hr_job_id.code,
                                              item.hr_job_id.name)))
        return res
#~
    #~ def name_search(self, cr, user, name, args=None, operator='ilike',
                    #~ context=None, limit=100):
        #~ res = super(tcv_payroll_import_job, self).\
            #~ name_search(cr, user, name, args, operator, context, limit)
        #~ if not res and name:
            #~ ids = self.search(
                #~ cr, user, [('code', 'ilike', name.upper())] + args,
                #~ limit=limit)
            #~ if ids:
                #~ res = self.name_get(cr, user, ids, context=context)
        #~ return res

    ##--------------------------------------------------------- function fields

    _columns = {
        'hr_job_id': fields.many2one(
            'hr.job', 'Job', required=False, ondelete='restrict'),
        #~ 'code': fields.char(
            #~ 'Code', size=16, required=True, readonly=False),
        #~ 'name': fields.char(
            #~ 'Name', size=64, required=True, readonly=False),
        'concepts_table_id': fields.many2one(
            'tcv.payroll.import.table', 'Concept\'s table', required=False,
            ondelete='restrict'),
        'analytic_account_id': fields.many2one(
            'account.analytic.account', 'Analytic Account', readonly=False,
            ondelete='restrict',),
        'payable_account_id': fields.many2one(
            'account.account', 'Payable account', required=False,
            ondelete='restrict', domain=[('type', '=', 'payable')]),
        'company_id': fields.many2one(
            'res.company', 'Company', required=True, readonly=True,
            ondelete='restrict'),
        'need_review': fields.boolean(
            'Need data', required=True),
        }

    _defaults = {
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company').
        _company_default_get(cr, uid, self._name, context=c),
        'need_review': lambda *a: False,
        }

    _sql_constraints = [
        ('hr_job_id', 'UNIQUE(hr_job_id)', 'The job must be unique!'),
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    def write(self, cr, uid, ids, vals, context=None):
        '''
        Assign: context = {'need_review': True}
        to set need_review value else need_review = false
        '''
        context = context or {}
        vals.update({'need_review': context.get('need_review', False)})
        res = super(tcv_payroll_import_job, self).\
            write(cr, uid, ids, vals, context)
        return res

    ##---------------------------------------------------------------- Workflow

tcv_payroll_import_job()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
