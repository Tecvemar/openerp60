# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date: 14/08/2012
#    Version: 0.0.0.0
#
#    Description: Main models definitions
#
#
##############################################################################
from datetime import datetime
from osv import fields,osv
from tools.translate import _
import pooler
import decimal_precision as dp
import time

##------------------------------------------------------------------------------------ class tcv_bank_account(osv.osv):

class tcv_bank_account(osv.osv):

    _name = 'tcv.bank.account'

    _description = 'Comany\'s bank accounts'
    
    def account_use_check(self, cr, uid, journal_id, context=None):
        id = self.search(cr, uid, [('journal_id', '=', journal_id)])
        if id:
            acc = self.browse(cr,uid,id[0],context=context)
            if acc:
                return acc.use_check
        return False        
    
    
    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        so_brw = self.browse(cr,uid,ids,context={})
        res = []
        for record in so_brw:
            acc_nr = record.name
            if acc_nr and len(acc_nr) == 20:
                name = '%s-%s-%s-%s'%(acc_nr[:4],acc_nr[4:8],acc_nr[8:10],acc_nr[10:])
            else:
                name = acc_nr
            name = '%s [%s]'%(name,record.bank_id.name)
            res.append((record.id, name))
        return res


    _columns = {
        'name': fields.char(
			'Account number', size=20, required=True, readonly=False),
        'bank_id': fields.many2one(
			'tcv.bank.list', 'Bank', required=True, readonly=False, 
			select=True, ondelete='restrict'),
        'rml_file': fields.char(
			'RML file name', size=64, required=False, readonly=False),
        'active': fields.boolean(
			'Active', required=True),
        'journal_id': fields.many2one(
			'account.journal', 'Journal', required=True, 
			domain="[('type','=','bank')]", ondelete='restrict'),
        'use_check':fields.boolean(
			'Use check', required=True),  
        'use_prefix': fields.selection(
			[('none', 'None'),('prefix', 'Prefix'),
			 ('sufix', 'Sufix'),('both','Both')], 
			string='Use prefix',
			help="Indica si se va a utilizar un prefijo y/o sufijo " + 
			"en el numero de cheque."),
		'format_ch_name': fields.char(
			'Format name', size=64, required=False, readonly=False,
			help="Define el formato para la cadena del numero del " +
			"cheque. Sample = %(prefix)02d%(name)06d%(sufix)02d"),
        'company_id': fields.many2one(
			'res.company','Company',required=True, readonly=True, 
			ondelete='restrict'),
        'currency_id': fields.many2one(
			'res.currency', 'Currency', required=True, readonly=True, 
			ondelete='restrict'),
        'checkbook_ids':fields.one2many(
			'tcv.bank.checkbook','bank_acc_id','Checkbooks'),
        }


    _defaults = {
        'company_id':lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr,uid,'tcv_bank_deposit',context=c),
        'currency_id': lambda self,cr,uid,c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.currency_id.id,
        'active': lambda *a: True,
        'use_check': lambda *a: True,
        'use_prefix': lambda *a: 'none',
        'format_ch_name': lambda *a: '%(name)06d',
        }
        
    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', 'The account number must be unique!'),
        ('journal_id_uniq', 'UNIQUE(journal_id)', 'The journal must be unique!'),
        ]
        
        
    def add_checkbook(self, cr, uid, ids, context=None):
        if not ids: return []
        chbk = self.browse(cr, uid, ids[0], context=context)
        return {
            'name':_('Register new checkbook'),
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'tcv.bank.checkbook',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'domain': '[]',
            'context': {
                'default_bank_acc_id': chbk.id,
                }
        }


tcv_bank_account()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

