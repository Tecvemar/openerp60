# -*- encoding: utf-8 -*-
##############################################################################
#    Company:
#    Author: Gabriel
#    Creation Date: 2016-02-23
#    Version: 1.0
#
#    Description:
#
#
##############################################################################

#~ from datetime import datetime
from osv import fields, osv
#~ from tools.translate import _
#~ import pooler
import decimal_precision as dp
import time
#~ import netsvc

##-------------------------------------------------------------------- tcv_igtf


class tcv_igtf(osv.osv):

    _name = 'tcv.igtf'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'company_id': fields.many2one(
            'res.company', 'Company', required=True, readonly=True,
            ondelete='restrict'),
        'name': fields.char(
            'Name', size=64, required=False, readonly=False),
        'rate': fields.float(
            'Rate', required=True, digits_compute=dp.get_precision('Account'),
            help="Rate value must be expressed in percent."),
        'date_start': fields.date(
            'Date start', required=True,
            help="Date of entry into effect of IGTF."),
        'date_end': fields.date(
            'Date end', required=False,
            help="End date of the term of IGTF."),
        'active': fields.boolean(
            'Active', required=True),
        'account_id': fields.many2one(
            'account.account', 'Account', required=True, ondelete='restrict',
            help="Account to record the expense caused."),
        'journal_ids': fields.many2many(
            'account.journal', 'igtf_journal_rel', 'igtf_id',
            'journal_id', 'Journals', readonly=False, ondelete='restrict',
            domain=[('type', '=', 'bank')],
            help="Bank journal's that will automatically apply the IGTF."),
        'exempt_partner_ids': fields.many2many(
            'res.partner', 'igtf_partner_rel', 'igtf_id',
            'partner_id', 'Partners', readonly=False, ondelete='restrict',
            domain=[('supplier', '=', True)],
            help="Partner's not subject to the IGTF."),
        'igtf_account_ids': fields.one2many(
            'tcv.igtf.accounts', 'igtf_account_id', 'Accounts'),
        }

    _defaults = {
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company').
        _company_default_get(cr, uid, self._name, context=c),
        'date_start': lambda *a: time.strftime('%Y-%m-%d'),
        'date_end': lambda *a: '2999-12-31',
        'active': lambda *a: True,
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    def apply_igtf(self, cr, uid, ids, acc_move_line, igtf, context):
        if not acc_move_line.credit:
            return False
        if (acc_move_line.journal_id.id in
                [x.id for x in igtf.journal_ids] and
                acc_move_line.partner_id.id not in
                [x.id for x in igtf.exempt_partner_ids] and
                acc_move_line.account_id.id ==
                acc_move_line.journal_id.default_credit_account_id.id):
            return True
        return False

    def gen_account_move_line(self, cr, uid, ids, acc_move_line, igtf,
                              context):
        res = []
        igtf_ammount = round((acc_move_line.credit * igtf.rate) / 100, 2)
        debit = {
            'auto': True,
            'company_id': acc_move_line.company_id.id,
            'partner_id': acc_move_line.partner_id.id,
            'account_id': igtf.account_id.id,
            'name': acc_move_line.name,
            'debit': igtf_ammount,
            'credit': 0,
            'reconcile': False,
            'currency_id': None,
            }
        credit = {
            'auto': True,
            'company_id': acc_move_line.company_id.id,
            'partner_id': acc_move_line.partner_id.id,
            'account_id': acc_move_line.account_id.id,
            'name': '[%s] %s' % (igtf.name, acc_move_line.name),
            'debit': 0,
            'credit': igtf_ammount,
            'reconcile': False,
            'currency_id': None,
            }
        res.append(credit)
        res.append(debit)
        return res

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_igtf()


##----------------------------------------------------------- tcv_igtf_accounts


class tcv_igtf_accounts(osv.osv):

    _name = 'tcv.igtf.accounts'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'igtf_account_id': fields.many2one(
            'tcv.igtf', 'IGTF account', required=True, ondelete='cascade'),
        'account_id': fields.many2one(
            'account.account', 'Account', required=True, ondelete='restrict'),
        'type': fields.selection(
            [('1', 'Efectivo'), ('2', 'Especies'), ('3', 'Nota de crédito'),
             ('4', 'Compensación'), ('5', 'Novacion'), ('6', 'Condonación'),
             ('7', 'Cesión')],
            string='Type', required=True),
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

tcv_igtf_accounts()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
