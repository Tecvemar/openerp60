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

##----------------------------------------------------- tcv_payroll_import_data


class tcv_payroll_import_data(osv.osv):

    _name = 'tcv.payroll.import.data'

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

    def name_search(self, cr, user, name, args=None, operator='ilike',
                    context=None, limit=100):
        res = super(tcv_payroll_import_data, self).\
            name_search(cr, user, name, args, operator, context, limit)
        if not res and name:
            ids = self.search(
                cr, user, [('code', 'ilike', name.upper())] + args,
                limit=limit)
            if ids:
                res = self.name_get(cr, user, ids, context=context)
        return res

    ##--------------------------------------------------------- function fields

    _columns = {
        'code': fields.char(
            'Code', size=16, required=True, readonly=False),
        'name': fields.char(
            'Name', size=64, required=True, readonly=False),
        'type': fields.selection(
            [('contract', 'Contract'), ('concept', 'Concept')],
            string='Type', required=True, readonly=True),
        'company_id': fields.many2one(
            'res.company', 'Company', required=True, readonly=True,
            ondelete='restrict'),
        'need_review': fields.boolean(
            'Need data', required=True),
        'account_kind_rec': fields.property(
            'res.partner.account', type='many2one',
            relation='res.partner.account', string='Receivable Account type',
            method=True, view_load=True,
            domain="[('type', '=', 'receivable')]",
            help="Set receivable account type for customer retated to " +
            "emplolee", required=False, readonly=False),
        'account_kind_pay': fields.property(
            'res.partner.account', type='many2one',
            relation='res.partner.account', string='Payable Account type',
            method=True, view_load=True,
            domain="[('type', '=', 'payable')]",
            help="Set payable account type for supplier retated to emplolee",
            required=False, readonly=False),
        'payable_account_id': fields.many2one(
            'account.account', 'Account', required=False, ondelete='restrict',
            help="Set the payable account to replace default (set in " +
            "concept's table)"),
        }

    _defaults = {
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company').
        _company_default_get(cr, uid, self._name, context=c),
        'need_review': lambda *a: False,
        }

    _sql_constraints = [
        ('code_uniq', 'UNIQUE(code,type)', 'The code must be unique!'),
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    def write(self, cr, uid, ids, vals, context=None):
        context = context or {}
        vals.update({'need_review': context.get('need_review')})
        res = super(tcv_payroll_import_data, self).\
            write(cr, uid, ids, vals, context)
        return res

    ##---------------------------------------------------------------- Workflow

tcv_payroll_import_data()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
