# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description: Report parser for: tcv_ari_personal_wiz
#
#
##############################################################################
from osv import fields, osv
from tools.translate import _
#~ import pooler
#~ import decimal_precision as dp
#~ import time
#~ import netsvc


##-------------------------------------------------------- tcv_ari_personal_wiz


class tcv_ari_personal_wiz(osv.osv_memory):

    _name = 'tcv.ari.personal.wiz'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def default_get(self, cr, uid, fields, context=None):
        data = super(tcv_ari_personal_wiz, self).default_get(
            cr, uid, fields, context)
        if data.get('user_id') and data.get('company_id'):
            obj_emp = self.pool.get('hr.employee')
            obj_afr = self.pool.get('tcv.rrhh.ari.forms')
            obj_ari = self.pool.get('tcv.rrhh.ari')
            emp_ids = obj_emp.search(
                cr, uid, [('user_id', '=', data.get('user_id')),
                          ('company_id', '=', data.get('company_id'))])
            if emp_ids and len(emp_ids) == 1:
                data.update({'employee_id': emp_ids[0]})
            else:
                raise osv.except_osv(
                    _('Error!'),
                    _('Can\'t find your employee id data, set employee\'s ' +
                      '"User" data field'))
            ari_ids = obj_ari.search(cr, uid, [('state', '=', 'draft')])
            arf_ids = obj_afr.search(
                cr, uid, [('employee_id', '=', data.get('employee_id')),
                          ('ari_id', 'in', ari_ids)],
                order='date DESC', limit=1)
            for item in obj_afr.browse(cr, uid, arf_ids, context=context):
                if item.ari_id.state == 'draft':
                    data['form_id'] = item.id
        return data

    ##--------------------------------------------------------- function fields

    _columns = {
        'user_id': fields.many2one(
            'res.users', 'User', readonly=True, select=True,
            ondelete='restrict'),
        'employee_id': fields.many2one(
            'hr.employee', "Employee", required=True, ondelete='restrict',
            readonly=True),
        'form_id': fields.many2one(
            'tcv.rrhh.ari.forms', 'ARI Form', change_default=True,
            readonly=True, ondelete='restrict'),
        'company_id': fields.many2one(
            'res.company', 'Company', required=True, readonly=True,
            ondelete='restrict'),
        }

    _defaults = {
        'user_id': lambda s, c, u, ctx: u,
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company').
        _company_default_get(cr, uid, self._name, context=c),
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_ari_personal_wiz()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
