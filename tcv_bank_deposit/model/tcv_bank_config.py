# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Gabriel Gamez
#    Creation Date: 07/06/2012
#    Version: 0.0.0.1
#
#    Description: Define los parametros de configuracion del modulo
#    Deposito bancario.
#
##############################################################################
#~ from datetime import datetime
from osv import fields, osv
#~ from tools.translate import _


class tcv_bank_config(osv.osv):

    _name = 'tcv.bank.config'

    _description = 'Datos de configuracion del modulo tcv_bank_deposit'

    _columns = {
        'company_id': fields.many2one(
            'res.company', 'Company', required=True, readonly=True,
            ondelete='restrict'),
        'detail_ids': fields.one2many(
            'tcv.bank.config.detail', 'detail_id', 'Details',
            ondelete='cascade'),
        'acc_bank_comis': fields.many2one(
            'account.account', 'Bank comission account', required=True,
            ondelete='restrict'),
        'acc_prepaid_tax': fields.many2one(
            'account.account', 'Prepaid tax account', required=True,
            ondelete='restrict'),
        }

    _rec_name = "company_id"

    _defaults = {
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company').
        _company_default_get(cr, uid, 'tcv_bank_config', context=c),
        }

    _sql_constraints = [
        ('company_id_uniq',
         'UNIQUE(company_id)',
         'The company must be unique!'),
        ]

tcv_bank_config()


class tcv_bank_config_detail(osv.osv):

    _name = 'tcv.bank.config.detail'

    _description = 'Details of the deposit bank'

    _columns = {
        'name': fields.char(
            'Reference', size=64),
        'journal_id': fields.many2one(
            'account.journal', 'Journal', required=True,
            ondelete='restrict', domain="[('type','=','cash')]"),
        'detail_id': fields.many2one(
            'tcv.bank.config', 'Bank config', required=True,
            ondelete='cascade'),
        'type': fields.selection(
            [('cash', 'Cash'), ('cheq', 'Cheq'),
             ('debit', 'Debit/credit card')],
            string='Type', required=True),
        'force_detail': fields.boolean(
            'Force detail',
            help="Set if you like to force individual selection and " +
            "conciliation of journal moves"),
        'bank_comission': fields.float(
            'Bank comission (%)', digits=(12, 8)),
        'prepaid_tax': fields.float(
            'Prepaid tax (%)', digits=(12, 8)),
        'bank_journal_id': fields.many2one(
            'account.journal', 'Bank journal',
            help="Here insert the reference for the bank journal",
            ondelete='restrict'),
        'active': fields.boolean(
            'Active', required=True),

        }

    _defaults = {
        'type': 'cash',
        'force_detail': True,
        'bank_comission': 0.0,
        'prepaid_tax': 0.0,
        'active': lambda *a: True,
        }

    _sql_constraints = [
        ('journal_id_uniq',
         'UNIQUE(journal_id)',
         'The journal must be unique!'),
        ('bank_comission_range',
         'CHECK(bank_comission between 0 and 100)',
         'The bank comssion must be in 0-100 range'),
        ]

tcv_bank_config_detail()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
