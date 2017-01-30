# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2013-09-06
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

##---------------------------------------------------------- tcv_check_template


class tcv_check_template(osv.osv):

    _name = 'tcv.check.template'

    _description = ''

    _order = 'name'

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'name': fields.char('Name', size=64, required=True, readonly=False),
        'line_ids': fields.one2many('tcv.check.template.lines', 'line_id',
                                    'Lines'),
        }

    _defaults = {
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    def button_load_template(self, cr, uid, ids, context=None):
        obj_lin = self.pool.get('tcv.check.template.lines')
        for item in self.browse(cr, uid, ids, context={}):
            if not item.line_ids:
                for t in obj_lin._template_fields:
                    obj_lin.create(cr, uid, {'line_id': item.id,
                                             'name': t[0],
                                             'x': 0,
                                             'y': 0}, context)
        return True

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_check_template()


##---------------------------------------------------- tcv_check_template_lines


class tcv_check_template_lines(osv.osv):

    _name = 'tcv.check.template.lines'

    _description = ''

    _template_fields = [('amount', 'Amount'),
                        ('beneficiary', 'Beneficiary'),
                        ('nat_line_1', 'Str amount 1'),
                        ('nat_line_2', 'Str amount 2'),
                        ('city_date', 'City & date'),
                        ('date_year', 'Year'),
                        ('restricted', 'Restricted'),
                        ('delta', 'Delta')]

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'line_id': fields.many2one('tcv.check.template', 'String',
                                   required=True, ondelete='cascade'),
        'name': fields.selection(_template_fields, string='Field',
                                 required=True, readonly=True),
        'x': fields.integer('X', required=True),
        'y': fields.integer('Y', required=True),
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

tcv_check_template_lines()


##---------------------------------------------------- tcv_check_template_users


class tcv_check_template_users(osv.osv):

    _name = 'tcv.check.template.users'

    _description = ''

    _rec_name = 'user_id'

    ##-------------------------------------------------------------------------

    def default_get(self, cr, uid, fields, context=None):
        context = context or {}
        data = super(tcv_check_template_users, self).default_get(
            cr, uid, fields, context)
        if context.get('active_model') == u'account.voucher' and \
                context.get('active_id'):
            obj_vou = self.pool.get('account.voucher')
            vou = obj_vou.browse(
                cr, uid, context.get('active_id'), context=context)
            data.update({
                'bank_acc_id': vou.check_id.bank_acc_id and
                vou.check_id.bank_acc_id.id})
        return data

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'user_id': fields.many2one('res.users', 'User', readonly=True,
                                   required=True, select=True,
                                   ondelete='restrict'),
        'bank_acc_id': fields.many2one('tcv.bank.account', 'Bank account',
                                       required=True, ondelete='restrict',
                                       domain="[('use_check', '=', True)]"),
        'template_id': fields.many2one('tcv.check.template', 'Template',
                                       required=True, select=True,
                                       ondelete='restrict'),
        }

    _defaults = {
        'user_id': lambda s, c, u, ctx: u,
        }

    _sql_constraints = [
        ('user_uniq', 'UNIQUE(user_id, bank_acc_id)',
         'The name must be unique!'),
        ]

    ##-----------------------------------------------------

    ##----------------------------------------------------- public methods

    ##----------------------------------------------------- buttons (object)

    ##----------------------------------------------------- on_change...

    ##----------------------------------------------------- create write unlink

    ##----------------------------------------------------- Workflow

tcv_check_template_users()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
