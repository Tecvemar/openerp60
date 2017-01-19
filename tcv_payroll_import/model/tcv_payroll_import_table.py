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

##---------------------------------------------------- tcv_payroll_import_table


class tcv_payroll_import_table(osv.osv):

    _name = 'tcv.payroll.import.table'

    _description = ''

    _order = 'code'

    ##-------------------------------------------------------------------------

    def name_get(self, cr, uid, ids, context):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        res = []
        for item in self.browse(cr, uid, ids, context={}):
            res.append((item.id, '[%s] %s' % (item.code, item.name)))
        return res

    def name_search(self, cr, user, name, args=None, operator='ilike',
                    context=None, limit=100):
        res = super(tcv_payroll_import_table, self).\
            name_search(cr, user, name, args, operator, context, limit)
        if not res and name:
            ids = self.search(
                cr, user, [('code', 'ilike', name.upper())] + args,
                limit=limit)
            if ids:
                res = self.name_get(cr, user, ids, context=context)
        return res

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    def _compute_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for item in self.browse(cr, uid, ids, context=context):
            need_review = False
            for line in item.line_ids:
                need_review = need_review or line.need_review
            res[item.id] = {'need_review': need_review}
        return res

    ##-------------------------------------------------------------------------

    _columns = {
        'code': fields.char(
            'Code', size=16, required=True, readonly=False),
        'name': fields.char(
            'Name', size=64, required=True, readonly=False),
        'line_ids': fields.one2many(
            'tcv.payroll.import.table.lines', 'table_id', 'Lines'),
        'company_id': fields.many2one(
            'res.company', 'Company', required=True, readonly=True,
            ondelete='restrict'),
        'need_review': fields.function(
            _compute_all, method=True, type='bool', string='Need review',
            multi='all'),
        }

    _defaults = {
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company').
        _company_default_get(cr, uid, self._name, context=c),
        }

    _sql_constraints = [
        ('code_uniq', 'UNIQUE(code)', 'The code must be unique!'),
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_payroll_import_table()


class tcv_payroll_import_table_lines(osv.osv):

    _name = 'tcv.payroll.import.table.lines'

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
        'table_id': fields.many2one(
            'tcv.payroll.import.table', 'Table', required=True,
            ondelete='cascade'),
        'concept_id': fields.many2one(
            'tcv.payroll.import.data', 'Concept', required=True,
            ondelete='restrict', domain=[('type', '=', 'concept')]),
        'account_id': fields.many2one(
            'account.account', 'Account', required=False,
            ondelete='restrict', domain=[('type', '!=', 'view')]),
        'payable_acc_id': fields.many2one(
            'account.account', 'For others acc', required=False,
            ondelete='restrict', domain=[('type', '!=', 'view')]),
        'move_type': fields.selection(
            [('normal', 'Normal'),
             ('for_others', 'For others'),
             ('emp_receivable', 'Acc. emp. receivable'),
             ],
            string='Move type', required=True, readonly=False),
        'need_review': fields.boolean(
            'Need data', required=True),
        }

    _defaults = {
        'move_type': lambda *a: 'normal',
        'need_review': lambda *a: False,
        }

    _sql_constraints = [
        ('concept_uniq', 'UNIQUE(concept_id, table_id)',
         'The concept must be unique for this table!'),
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
        vals.update({'need_review': context.get('need_review')})
        res = super(tcv_payroll_import_table_lines, self).\
            write(cr, uid, ids, vals, context)
        return res

    ##---------------------------------------------------------------- Workflow

tcv_payroll_import_table_lines()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
