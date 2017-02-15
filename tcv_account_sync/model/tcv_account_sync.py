# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date: 23/07/2012
#    Version: 0.0.0.0
#
#    Description: account.account sync config module
#
#
##############################################################################
from datetime import datetime
from osv import fields,osv
from tools.translate import _
import pooler
import decimal_precision as dp
import time

class tcv_account_sync(osv.osv):

    _name = 'tcv.account.sync'

    _description = 'Account.account multi-company sync config data'

    _columns = {
        'company_id': fields.many2one('res.company', 'Company', help='Main company for account sync', required=True, ondelete='restrict'),
        'partner_id':fields.related('company_id','partner_id', type='many2one', relation='res.partner', string='Partner'),  
        'user_id': fields.many2one('res.users', 'User', required=True, readonly=False, select=True, help='User to create/update/delete account data across comanies', ondelete='restrict'),
        }

    _defaults = {
        'company_id':lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr,uid,'tcv.voucher.advance',context=c),
        'user_id': lambda obj, cr, uid, context: uid,
        }
        
    _sql_constraints = [
        ('company_id_uniq', 'UNIQUE(company_id)', 'The company must be unique!'),
        ]    
        
        
    def on_change_company_id(self, cr, uid, ids, company_id):
        res= {}
        if company_id:
            org = self.pool.get('res.company').browse(cr,uid,company_id,context=None)
            res= {'value':{'partner_id':org.partner_id.id}}
        return res

tcv_account_sync()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
