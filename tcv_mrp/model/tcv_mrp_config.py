# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
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

##-------------------------------------------------------------- tcv_mrp_config


class tcv_mrp_config(osv.osv):

    _name = 'tcv.mrp.config'

    _description = ''

    ##-------------------------------------------------------------------------

    ##--------------------------------------------------------- function fields

    _columns = {
        'company_id': fields.many2one(
            'res.company', 'Company', required=True,
            readonly=True, ondelete='restrict'),
        'location_id': fields.many2one(
            'stock.location', 'Location', required=True, select=True,
            ondelete='restrict', help=""),
        'stock_journal_id': fields.many2one(
            'stock.journal', 'Stock Journal', required=True, select=True,
            ondelete='restrict', help=""),
        'rounding_account_id': fields.many2one(
            'account.account', 'Rounding account', required=True,
            help="Account for rounding diff"),
        'block_check_user_id': fields.many2one(
            'res.users', 'Block check user', readonly=False, select=True,
            ondelete='restrict',
            help="Responsible user for block\'s cost"),
        }

    _defaults = {
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company').
        _company_default_get(cr, uid, 'obj_name', context=c),
        }

    _sql_constraints = [
        ('company_id_uniq', 'UNIQUE(company_id)',
         'The company must be unique!'),
        ]

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_mrp_config()
