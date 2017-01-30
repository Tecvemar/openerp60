# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2013-09-23
#    Version: 0.0.0.1
#
#    Description:
#
#
##############################################################################

#~ from datetime import datetime
from osv import fields, osv
from tools.translate import _
#~ import pooler
#~ import decimal_precision as dp
#~ import time
#~ import netsvc

##------------------------------------------------------- tcv_employee_2_account


class tcv_employee_2_account(osv.osv_memory):

    _name = 'tcv.employee.2.account'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def default_get(self, cr, uid, fields, context=None):
        context = context or {}
        data = super(tcv_employee_2_account, self).default_get(cr, uid, fields,
                                                              context)
        if context.get('active_model') == 'hr.employee' and \
                context.get('active_id'):
            obj_emp = self.pool.get('hr.employee')
            emp_brw = obj_emp.browse(cr, uid, context.get('active_id'),
                                     context=context)
            data.update({
                'employee_id': emp_brw.id,
                })
            if emp_brw.receivable_account_id:
                data.update({
                    'parent_id': emp_brw.receivable_account_id.parent_id.id,
                    'type': emp_brw.receivable_account_id.type,
                    'user_type': emp_brw.receivable_account_id.user_type.id,
                    'account_id': emp_brw.receivable_account_id.id,
                    })
        return data

    ##--------------------------------------------------------- function fields

    _columns = {
        'employee_id': fields.many2one(
            'hr.employee', 'Employee', required=True, readonly=True,
            ondelete='restrict'),
        'parent_id': fields.many2one(
            'account.account', 'Parent account', required=True,
            ondelete='cascade', domain=[('type','=','view')]),
        'type': fields.selection([
            ('view', 'View'),
            ('other', 'Regular'),
            ('receivable', 'Receivable'),
            ('payable', 'Payable'),
            ('liquidity','Liquidity'),
            ('consolidation', 'Consolidation'),
            ('closed', 'Closed'),
            ], 'Internal Type', required=True),
        'user_type': fields.many2one(
            'account.account.type', 'Account Type', required=True),
        'account_id': fields.many2one(
            'account.account', 'Account', readonly=True,
            ondelete='restrict'),
        }

    _defaults = {
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    def button_create_account(self, cr, uid, ids, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        obj_acc = self.pool.get('account.account')
        obj_emp = self.pool.get('hr.employee')
        for item in self.browse(cr, uid, ids, context={}):
            code = '%s%05d' % (item.parent_id.code,
                               item.employee_id.partner_id.id)
            account_id = obj_acc.search(cr, uid, [('code', '=', code)])
            if account_id:
                raise osv.except_osv(
                    _('Error!'),
                    _('The account %s already exist!') % code)
            name = '%s - %s' % (item.parent_id.name,
                               item.employee_id.partner_id.name)
            account = {'code': code,
                       'name': name,
                       'type': item.type,
                       'user_type': item.user_type.id,
                       'reconcile': True,
                       'auto': False,
                       'sync_type': 'no_sync',
                       'company_id': self.pool.get('res.company').
                       _company_default_get(cr, uid, self._name,
                       context=context),
                       }
            acc_id = obj_acc.create(cr, uid, account, context)
            obj_emp.write(cr, uid, [item.employee_id.id],
                       {'receivable_account_id': acc_id}, context=context)
        return {'type': 'ir.actions.act_window_close'}

    ##------------------------------------------------------------ on_change...

    def on_change_parent_id(self, cr, uid, ids, parent_id, employee_id):
        res = {}
        ids = isinstance(ids, (int, long)) and [ids] or ids
        if parent_id:
            obj_acc = self.pool.get('account.account')
            obj_emp = self.pool.get('hr.employee')
            acc_brw = obj_acc.browse(cr, uid, parent_id, context=None)
            emp_brw = obj_emp.browse(cr, uid, employee_id, context=None)
            code = '%s%05d' % (acc_brw.code, emp_brw.partner_id.id)
            account_id = obj_acc.search(cr, uid, [('code', '=', code)])
            if account_id:
                res.update({'account_id': account_id[0]})
        return {'value': res}

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_employee_2_account()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
