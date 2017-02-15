# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date: 16/07/2012
#    Version: 0.0.0.0
#
#    Description: Se sobreescribe para incorporar los campos property para 
#       los anticipos 
#
##############################################################################
from datetime import datetime
from osv import fields,osv
from tools.translate import _
import pooler
import decimal_precision as dp
import time

class res_partner(osv.osv):
    _inherit = 'res.partner'

    _columns = {
        'property_account_advance': fields.property(
            'account.account',
            type='many2one',
            relation='account.account',
            string="Account Advance",
            method=True,
            view_load=True,
            domain="[('type', '=', 'receivable')]",
            help="This account will be used instead of the default one as the advance account for the current partner",
            required=False,
            readonly=False),    
        'property_account_prepaid': fields.property(
            'account.account',
            type='many2one',
            relation='account.account',
            string="Account Prepaid",
            method=True,
            view_load=True,
            domain="[('type', '=', 'payable')]",
            help="This account will be used instead of the default one as the prepaid account for the current partner",
            required=False,
            readonly=False),
            }
           
    def _gen_property_account(self, cr, uid, ids, vals, field, account_kind, context=None):
        res = {}
        partner = self.browse(cr, uid, ids)[0]
        rpa_obj = self.pool.get('res.partner.account')
        rpa = rpa_obj.browse(cr, uid, vals[account_kind])
        account_name = partner.name
        parent_name = rpa.property_parent_advance.name
        aa_obj = self.pool.get('account.account')
        if (account_kind == 'account_kind_rec' and (partner.customer or vals.get('customer'))) or \
           (account_kind == 'account_kind_pay' and (partner.supplier or vals.get('supplier'))):
            code = '%s%00005d'%(rpa.property_parent_advance.code,partner.id)
        else:
            code = rpa.property_account_advance_default.code
        account_id = aa_obj.search(cr, uid, [('code', '=', code)])
        if not account_id:  
            user = self.pool.get('res.users').browse(cr,uid,uid,context=context)
            new_account = {'name':'CXC %s'%(partner['name']),
                       'code':code,
                       'name': u'%s - %s'%(parent_name, account_name),
                       'parent_id':rpa.property_parent_advance.id,
                       'company_id':user.company_id.id,
                       'type':rpa.type,
                       'user_type':rpa.user_type_advance.id,
                       'reconcile':True,
                       'auto':False,
                       'active': True,
                       'currency_mode':'current',
                       }
            account_id = aa_obj.create(cr, uid, new_account,context)
        else:
            account_id = account_id[0]    
        return {field:account_id}


    def write(self, cr, uid, ids, vals, context=None):
        
        if type(ids) != list:
            ids = [ids]
        for id in ids:    
            if vals.get('account_kind_rec'):
                vals.update(self._gen_property_account(cr, uid, [id], vals, 'property_account_advance', 'account_kind_rec', context=None))
            if vals.get('account_kind_pay'):
                vals.update(self._gen_property_account(cr, uid, [id], vals, 'property_account_prepaid', 'account_kind_pay',context=None))
        res = super(res_partner, self).write(cr, uid, ids, vals, context)
        return res
        
res_partner()            

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
