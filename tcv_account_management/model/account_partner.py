# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date: 16/07/2012
#    Version: 0.0.0.0
#
#    Description: Add advance's configurations to account_management
#
#
##############################################################################
## Se modifica para incorporar los campos requeridos para establecer la
## clasificación contable de los anticipos
##############################################################################
from osv import osv
from osv import fields

class res_partner_account(osv.osv):

    _inherit = 'res.partner.account'

    _columns = {
        'use_advance': fields.boolean('Use advance'),
        'property_parent_advance': fields.property(
            'account.account',
            type='many2one',
            relation='account.account',
            string="Cuenta Anfitriona",
            method=True,
            view_load=True,
            domain="[('type', '=', 'view'),('level','=',level),('level','>',0)]",
            help='',
            readonly=False),
        'property_account_advance_default': fields.property(
            'account.account',
            type='many2one',
            relation='account.account',
            string="Cuenta Contable por Defecto",
            method=True,
            view_load=True,
            domain="[('type', '!=', 'view'),('parent_id', '=', property_account_advance), ('company_id', '=', company_id), ('reconcile', '=', True), ('user_type', '=', user_type_advance), ('type', '=', type),]",
            help='',
            required=True,
            readonly=False),
        'user_type_advance': fields.many2one(
            'account.account.type',
            'Tipo de Cuenta',
            ondelete='restrict'),
        }

    _defaults = {
        'use_advance': lambda *a: True,
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company').
        _company_default_get(cr, uid, self._name, context=c),
        }

res_partner_account()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
