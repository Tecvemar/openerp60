# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Gabriel Gamez
#    Creation Date: 07/06/2012
#    Version: 0.0.0.1
#
#    Description: Define los parametros de configuracion del modulo Deposito bancario.
#
#
##############################################################################
from datetime import datetime
from osv import fields,osv
from tools.translate import _
import decimal_precision as dp


class tcv_bounced_cheq_config(osv.osv):

    _name = 'tcv.bounced.cheq.config'

    _description = 'Datos de configuracion del modulo tcv_bounced_cheq_config'

    _columns = {
        'company_id': fields.many2one('res.company','Company', required=True, readonly=False),
        'journal_id': fields.many2one('account.journal', 'Bounced cheq journal', required=True, domain=[('type','=','general',)], help='Indicate the journal for bounced cheq register, must be general type.'),
        'use_fee':fields.boolean('Charge fee for bounced check', help='Indicates if the company charges a fee when check is bounced', required=True),       
        'document_type': fields.selection([('invoice', 'Invoice'),('refund', 'Invoice refund (Debit note)')], string='Type', help='The type of autocreated document'),
        'fee_amount':fields.float('Fee amount', digits_compute=dp.get_precision('Account'), help='Net amount for fee charge (whitout taxes)'),
        'fee_product_id': fields.many2one('product.product', 'Product', domain="[('type','=','service')]", ondelete='restrict', help='Product for document'),
        'fee_journal_id':fields.many2one('account.journal', 'Journal', ondelete='restrict', help='Journal for register document'),
        'notify_salesman':fields.boolean('Notify salesman', help='Send internal message to salesman when chech is bounced', required=True),       
        #~ 'auto_create':fields.boolean('Auto create', help='Autocreate the fee document when bounced check is validated', required=True),
        #~ 'debit_state': fields.selection([('draft', 'Draft'),('open', 'Open')], string='Document state', required=True, readonly=True, help='Leave the document in this state (when autocreated)'),
       }
        
    _rec_name = "company_id"
        

    _defaults = {
        'company_id':lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr,uid,'tcv_bank_deposit',context=c),
        'use_fee': lambda *a: False,
        'fee_amount': lambda *a: 0.0,
        }

    _sql_constraints = [
        ('company_id_uniq', 'UNIQUE(company_id)', 'The company must be unique!'),
        ]
        
        
    def company_config_get(self,cr,uid,company_id,context=None):
        obj_cfg = self.pool.get('tcv.bounced.cheq.config')
        cfg_id = obj_cfg.search(cr,uid,[('company_id','=',company_id)])
        if cfg_id and len(cfg_id) == 1:
            cfg_id = cfg_id[0]
        else:
            raise osv.except_osv(_('Error!'),_("Invalid configuration settings. Please check:\n\nAccounting ->\n\tConfiguration ->\n\t\tFinancial Accounting ->\n\t\t\tBank and Cash ->\n\t\t\t\tBounced Cheq"))
        return obj_cfg.browse(cr, uid, cfg_id, context)    
        
    
    def on_change_fee_product_id(self, cr, uid, ids, fee_product_id):
        context={}
        res= {}
        if fee_product_id:
            product = self.pool.get('product.product').browse(cr,uid,fee_product_id,context=context)
            res= {'value':{'fee_amount':product.property_list_price}}
        return res

tcv_bounced_cheq_config()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
