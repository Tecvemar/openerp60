# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Gabriel Gamez
#    Creation Date: 25/06/2012
#    Version: 0.0.0.1
#
#    Description: Define los parametros de configuracion del modulo Caja Chica.
#
#
##############################################################################
#~ from datetime import datetime
from osv import fields, osv
#~ from tools.translate import _
#~ import pooler
import decimal_precision as dp
#~ import time

#~ class tcv_petty_cash_config(osv.osv):
#~
    #~ _name = 'tcv.petty.cash.config'
#~
    #~ _description = 'Datos de configuracion del modulo tcv_petty_cash'
#~
    #~ _columns = {
        #~ 'company_id':fields.many2one('res.company','Company', required=True, readonly=True, ondelete='restrict'),
        #~ 'detail_ids':fields.one2many('tcv.petty.cash.config.detail','detail_id','Details', ondelete='cascade'),
        #~ 'acc_petty_cash_refund':fields.many2one('account.account', 'Petty cash refund account', required=True, ondelete='restrict'),
        #~ }
#~
    #~ _rec_name = "company_id"
#~
#~
    #~ _defaults = {
        #~ 'company_id':lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr,uid,'tcv_bank_config',context=c),
        #~ }
#~
    #~ _sql_constraints = [
        #~ ('company_id_uniq', 'UNIQUE(company_id)', 'The company must be unique!'),
        #~ ]
#~
#~ tcv_petty_cash_config()


class tcv_petty_cash_config_detail(osv.osv):

    _name = 'tcv.petty.cash.config.detail'

    _description = 'Petty cash config'

    _columns = {
        'name':fields.char('Name', size=64, required=True),
        'journal_id':fields.many2one('account.journal', 'Journal', required=True, ondelete='restrict', domain="[('type','=','cash')]"),
        #~ 'detail_id':fields.many2one('tcv.petty.cash.config', 'Petty cash config', required=True, ondelete='cascade'),
        'currency_id': fields.many2one('res.currency', 'Currency', required=True, readonly=True, ondelete='restrict', states={'draft':[('readonly',False)]}),
        'amount':fields.float('Petty cash amount', digits_compute=dp.get_precision('Account'), required=True),
        'max_amount':fields.float('Max amount', digits_compute=dp.get_precision('Account'), required=True, help="Max amunt for single payent (0 = no limit)"),
        'user_id':fields.many2one('res.users', 'Custodian', help='User responsible for petty cash', required=True),
        'active': fields.boolean('Active', required=True),
        'acc_petty_cash_refund':fields.many2one('account.account', 'Petty cash refund account', required=True, ondelete='restrict'),
        'company_id':fields.many2one('res.company','Company', required=True, readonly=True, ondelete='restrict'),
        }

    _defaults = {
        'currency_id': lambda self,cr,uid,c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.currency_id.id,
        'amount':0.0,
        'max_amount':0.0,
        'active': lambda *a: True,
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company').
        _company_default_get(cr, uid, self._name, context=c),
        }

    _sql_constraints = [
        ('journal_id_uniq', 'UNIQUE(journal_id)', 'The journal must be unique!'),
        ('amount_range', 'CHECK(amount > 0)', 'The petty cash amount must be > 0.'),
        ('max_amount_range', 'CHECK(max_amount >= 0)', 'The petty cash amount must be >= 0.'),
        ('name_uniq', 'UNIQUE(name)', 'The name must be unique!'),
        ]

tcv_petty_cash_config_detail()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
