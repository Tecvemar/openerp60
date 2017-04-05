# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Gabriel Gamez
#    Creation Date: 2015-07-01
#    Version: 0.0.0.1
#
#    Description:
#
#
##############################################################################

#~ from datetime import datetime
from osv import fields, osv
from tools.translate import _
#~ import pooler
import decimal_precision as dp
import time
#~ import netsvc

##-------------------------     -----------------tcv_check_report_wizard


class tcv_check_report_wizard(osv.osv_memory):

    _name = 'tcv.check.report.wizard'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def default_get(self, cr, uid, fields, context=None):
        data = super(tcv_check_report_wizard, self).\
            default_get(cr, uid, fields, context)
        data.update({'date_from': time.strftime('%Y-%m-%d'),
                     'date_to': time.strftime('%Y-%m-%d'),
                     'loaded': False,
                     })
        return data

    ##--------------------------------------------------------- function fields

    _columns = {
        'bank_acc_id': fields.many2one(
            'tcv.bank.account', 'Bank account', required=True,
            ondelete='restrict', domain="[('use_check', '=', True)]"),
        'date_from': fields.date(
            'Date from', required=True),
        'date_to': fields.date(
            'Date to', required=True),
        'loaded': fields.boolean(
            'Loaded'),
        'company_id': fields.many2one(
            'res.company', 'Company', required=True, readonly=True,
            ondelete='restrict'),
        'line_ids': fields.one2many(
            'tcv.check.report.wizard.lines', 'line_id', 'Checks'),
        }

    _defaults = {
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company').
        _company_default_get(cr, uid, self._name, context=c),
        }

    _sql_constraints = [
        ]

    ##------------------------------------------------------------------

    ##--------------------------------------------------- public methods

    def clear_wizard_lines(self, cr, uid, item, context):
        unlink_ids = []
        for l in item.line_ids:
            unlink_ids.append(l.id)
        obj_lin = self.pool.get('tcv.check.report.wizard.lines')
        if unlink_ids:
            obj_lin.unlink(cr, uid, unlink_ids, context=context)
        self.write(
            cr, uid, [item.id],
            {'loaded': False}, context=context)
        return unlink_ids

    def load_wizard_lines(self, cr, uid, ids, context):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        lines = []
        obj_chk = self.pool.get('tcv.bank.checks')
        for item in self.browse(cr, uid, ids, context={}):
            self.clear_wizard_lines(cr, uid, item, context)
            check_ids = obj_chk.search(
                cr, uid,
                [('date', '>=', item.date_from),
                 ('date', '<=', item.date_to),
                 ('bank_acc_id', '=', item.bank_acc_id.id),
                 ('state', '=', 'issued')
                 ])
            if check_ids:
                lines = [(0, 0, {'check_id': x, 'selected': True})
                         for x in check_ids]
                self.write(
                    cr, uid, [item.id],
                    {'line_ids': lines, 'loaded': True}, context=context)
        return True

    ##-------------------------------------------------------- buttons (object)

    def tcv_txt_check_export_vzla(self, cr, uid, ids, context=None):
        context = context or {}
        ids = isinstance(ids, (int, long)) and [ids] or ids
        crw_brw = self.browse(cr, uid, ids, context={})[0]
        crw_data = {
            'company_id': crw_brw.company_id.id,
            'company_vat': crw_brw.company_id.partner_id.rif,
            'total_amount': 0.0,
            'bank_acc_id': crw_brw.bank_acc_id.id,
            'bank_acc_number': crw_brw.bank_acc_id.name,
            'check_ids': [],
            }
        for check in crw_brw.line_ids:
            if check.selected:
                crw_data['total_amount'] += check.amount
                if len(check.full_name) == 8:
                    number = check.full_name
                elif check.prefix and \
                        len(check.full_name) + len(check.prefix) == 8:
                    number = '%s%s' % (check.prefix, check.full_name)
                else:
                    raise osv.except_osv(
                        _('Error!'),
                        _('The check\'s number must have 8 digits'))
                chk_data = {
                    'check_id': check.check_id.id,
                    'beneficiary': check.beneficiary,
                    'number': number,
                    'amount': check.amount,
                    'date': check.date,
                    'concept': check.name,
                    }
                crw_data['check_ids'].append(chk_data)
        return {'name': _('Export TXT Venezuela'),
                'type': 'ir.actions.act_window',
                'res_model': 'tcv.txt.check.export.vzla',
                'view_type': 'form',
                'view_id': False,
                'view_mode': 'form',
                'nodestroy': True,
                'target': 'new',
                'domain': "",
                'context': {'crw_data': crw_data}}

    ##------------------------------------------------------------ on_change...

    def on_change_bank_acc_id(self, cr, uid, ids, bank_acc_id):
        res = {}
        res.update({'loaded': False})
        return {'value': res}

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_check_report_wizard()


##------------------------------------ tcv_check_report_wizard_lines


class tcv_check_report_wizard_lines(osv.osv_memory):

    _name = 'tcv.check.report.wizard.lines'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'line_id': fields.many2one(
            'tcv.check.report.wizard', 'String', required=True,
            ondelete='cascade'),
        'check_id': fields.many2one(
            'tcv.bank.checks', 'Check', required=True,
            ondelete='restrict'),
        'beneficiary': fields.related(
            'check_id', 'beneficiary', type='char', size=64,
            string='Beneficiary', store=False, readonly=True),
        'prefix': fields.char(
            'Ch prefix', size=2, required=False, readonly=False),
        'full_name': fields.related(
            'check_id', 'full_name', type='char', size=64,
            string='Number', store=False, readonly=True),
        'amount': fields.related(
            'check_id', 'amount', type='float',
            digits_compute=dp.get_precision('Account'),
            string='Amount', store=False, readonly=True),
        'date': fields.related(
            'check_id', 'date', type='date', string='Date', store=False,
            readonly=True, required=True),
        'voucher_id': fields.related(
            'check_id', 'voucher_id', type='many2one',
            relation='account.voucher', string='Voucher',
            store=False, readonly=True),
        'name': fields.related(
            'voucher_id', 'name', type='char', size=64,
            string='Memo', store=False, readonly=True),
        'selected': fields.boolean(
            'Select'),
        }

    _defaults = {
        'selected': lambda *a: False,

        }

    _sql_constraints = [
        ]

    ##------------------------------------------------------------------

    ##--------------------------------------------------- public methods

    ##------------------------------------------------- buttons (object)

    ##----------------------------------------------------- on_change...

    ##---------------------------------------------- create write unlink

    ##--------------------------------------------------------- Workflow

tcv_check_report_wizard_lines()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
