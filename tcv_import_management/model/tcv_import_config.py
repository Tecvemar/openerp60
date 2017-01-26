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

##----------------------------------------------------------- tcv_import_config


class tcv_import_config(osv.osv):

    _name = 'tcv.import.config'

    _description = ''

    ##-------------------------------------------------------------------------

    ##--------------------------------------------------------- function fields

    _columns = {
        'company_id': fields.many2one(
            'res.company', 'Company', required=True, readonly=True,
            ondelete='restrict'),
        'journal_id': fields.many2one(
            'account.journal', 'Journal', required=True,
            domain="[('type','=','purchase')]", ondelete='restrict'),
        'account_id': fields.many2one(
            'account.account', 'Account', required=True,
            help="Account for import expenses applied"),
        }

    _defaults = {
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company').
        _company_default_get(cr, uid, self._name, context=c),
        }

    _sql_constraints = [
        ('company_id_uniq', 'UNIQUE(company_id)',
         'The company must be unique!'),
        ]

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_import_config()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
