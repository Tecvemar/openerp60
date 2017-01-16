# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description: Report parser for: tcv_legal_diary
#
#
##############################################################################
from report import report_sxw
from tools.translate import _
#~ from datetime import datetime
from osv import fields, osv
#~ import pooler
import decimal_precision as dp
import time
#~ import netsvc


__TOTAL_CODE__ = 'z' * 20


class parser_tcv_legal_diary(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        context = context or {}
        super(parser_tcv_legal_diary, self).__init__(
            cr, uid, name, context=context)
        self.localcontext.update({
            'get_name': self._get_name,
            })
        self.context = context

    def _get_name(self, o):
        name = _('Legal diary')
        return name

report_sxw.report_sxw(
    'report.tcv.legal.diary.report',
    'tcv.legal.diary',
    'addons/tcv_account/report/tcv_legal_diary.rml',
    parser=parser_tcv_legal_diary,
    header=False
    )


##------------------------------------------------------------- tcv_legal_diary


class tcv_legal_diary(osv.osv_memory):

    _name = 'tcv.legal.diary'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def default_get(self, cr, uid, fields, context=None):
        data = super(tcv_legal_diary, self).default_get(
            cr, uid, fields, context)
        if not data.get('period_id'):
            date = time.strftime('%Y-%m-%d')
            obj_per = self.pool.get('account.period')
            period_id = obj_per.find(cr, uid, date)[0]
            data.update({'period_id': period_id})
        return data

    def _add_account(self, account, debit, credit, level):
        res = []
        if account.type == 'view' and \
                account.level < level:
            res.append({
                'code': account.code,
                'account_id': account.id,
                })
            code_tot = '%s%s' % (account.code, __TOTAL_CODE__)
            res.append({
                'code': code_tot,
                'account_id': account.id,
                'total': True,
                'debit': debit,
                'credit': credit,
                })
        else:
            res.append({
                'code': account.code,
                'account_id': account.id,
                'debit': debit,
                'credit': credit,
                })
        return res

    ##--------------------------------------------------------- function fields

    _columns = {
        'period_id': fields.many2one(
            'account.period', 'Period', required=True, ondelete="restrict"),
        'line_ids': fields.one2many(
            'tcv.legal.diary.lines', 'line_id', 'Account balance',
            readonly=True),
        'loaded': fields.boolean(
            'Loaded'),
        'non_zero': fields.boolean(
            'No zero lines', help="Hide 0 balance accounts"),
        'show_code': fields.boolean(
            'Show code', help="Show accounts code"),
        'use_ident': fields.boolean(
            'Use ident', help="Use identation"),
        'level': fields.integer(
            'Account level', help="0=All levels"),
        'company_id': fields.many2one(
            'res.company', 'Company', required=True, readonly=True,
            ondelete='restrict'),
        }

    _defaults = {
        'loaded': lambda *a: False,
        'non_zero': lambda *ad: True,
        'show_code': lambda *a: False,
        'use_ident': lambda *a: True,
        'level': lambda *a: 3,
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company').
        _company_default_get(cr, uid, self._name, context=c),
        }

    _sql_constraints = [
        ('level_range', 'CHECK(level between 0 and 9)',
         'The level must be in 0-9 range!'),
        ('print_cols_range', 'CHECK(print_cols between 1 and 2)',
         'The Print columns must be 1 or 2!'),
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    def clear_wizard_lines(self, cr, uid, item, context):
        unlink_ids = []
        for l in item.line_ids:
            unlink_ids.append(l.id)
        obj_lin = self.pool.get('tcv.legal.diary.lines')
        if unlink_ids:
            obj_lin.unlink(cr, uid, unlink_ids, context=context)
        return unlink_ids

    ##-------------------------------------------------------- buttons (object)

    def load_wizard_lines(self, cr, uid, ids, context):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        obj_tba = self.pool.get('tcv.trial.balance')
        obj_tbl = self.pool.get('tcv.trial.balance.lines')
        obj_acc = self.pool.get('account.account')
        #~ tot_23 = 0
        lines = []
        for item in self.browse(cr, uid, ids, context={}):
            self.clear_wizard_lines(cr, uid, item, context)
            # Create trial balance
            values = {
                'date_from': item.period_id.date_start,
                'date_to': item.period_id.date_stop,
                'non_zero': item.non_zero,
                'total_view': True,
                'level': item.level or None,
                }
            tba_id = obj_tba.create(cr, uid, values, context)
            obj_tba.load_wizard_lines(cr, uid, tba_id, context)
            level = item.level or 99
            # Get ids from trial balance lines
            acc_ids = obj_acc.search(cr, uid, [])
            diary_acc_ids = obj_tbl.search(
                cr, uid, [('account_id', 'in', acc_ids),
                          ('line_id', '=', tba_id)])
            # Add trial balance & totals lines
            totals = {'debit': 0, 'credit': 0}
            for l in obj_tbl.browse(cr, uid, diary_acc_ids, context=context):
                lines.extend(self._add_account(
                    l.account_id, l.debit, l.credit, level))
                if l.account_id.level == 1:
                    totals['debit'] += l.debit
                    totals['credit'] += l.credit
            lines.append({
                'code': __TOTAL_CODE__,
                'total': True,
                'debit': totals['debit'],
                'credit': totals['credit'],
                })
            line_ids = sorted(lines, key=lambda k: k['code'])
            self.write(cr, uid, [item.id], {
                'line_ids': [(0, 0, x) for x in line_ids],
                'loaded': True}, context)
        return True

    ##------------------------------------------------------------ on_change...

    def on_change_data(self, cr, uid, ids, period_id):
        res = {}
        res.update({'loaded': False})
        return {'value': res}

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_legal_diary()


class tcv_legal_diary_lines(osv.osv_memory):

    _name = 'tcv.legal.diary.lines'

    _description = ''

    _order = 'code'

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    def _compute_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for item in self.browse(cr, uid, ids, context=context):
            if item.line_id.show_code:
                acc_name = '[%s] %s' % (item.account_id.code,
                                        item.account_id.name)
            else:
                acc_name = item.account_id.name
            ident = ' ' * 8 if item.line_id.use_ident else ''

            if item.total:
                acc_name = _('TOTAL %s') % acc_name
            if item.code == __TOTAL_CODE__:
                res[item.id] = {'acc_name': _('General total')}
            else:
                res[item.id] = {
                    'acc_name': '%s%s' % (ident * (item.account_id.level - 1),
                                          acc_name),
                    }
            res[item.id].update({'balance': item.debit - item.credit})
        return res

    ##-------------------------------------------------------------------------

    _columns = {
        'line_id': fields.many2one(
            'tcv.legal.diary', 'String', required=True, ondelete='cascade'),
        'code': fields.char(
            'Code', size=64, required=False, readonly=False),
        'account_id': fields.many2one(
            'account.account', 'Account', required=False, ondelete='restrict'),
        'acc_name': fields.function(
            _compute_all, method=True, type='char', size=128,
            string='Account', multi='all'),
        'total': fields.float(
            'Total'),
        'type': fields.related(
            'account_id', 'type', type='char', size=16, store=False),
        'debit': fields.float(
            'Debit', digits_compute=dp.get_precision('Account'),
            required=True),
        'credit': fields.float(
            'Credit', digits_compute=dp.get_precision('Account'),
            required=True),
        'balance': fields.function(
            _compute_all, method=True, type='float',
            string='Balance', multi='all'),
        }

    _defaults = {
        'total': lambda *a: False,
        'debit': lambda *a: 0,
        'credit': lambda *a: 0,
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_legal_diary_lines()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
