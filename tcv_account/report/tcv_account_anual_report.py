# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description: Report parser for: tcv_account_anual_report
#
#
##############################################################################
import time
#~ import pooler
from report import report_sxw
from tools.translate import _
from osv import fields, osv
from datetime import datetime
from dateutil.relativedelta import relativedelta


__TCV_ACCOUNT_ANUAL_REPORT_TYPES__ = [
    (10, _('Account balance by month')),
    (20, _('Account variation by month')),
    ]


##---------------------------------------------------- tcv_account_anual_report


class tcv_account_anual_report(osv.osv_memory):

    _inherit = 'tcv.monthly.report'

    _name = 'tcv.account.anual.report'

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def default_get(self, cr, uid, fields, context=None):
        data = super(tcv_account_anual_report, self).default_get(
            cr, uid, fields, context)
        data.update({
            'name': _('Annual accounting summary'),
            })
        return data

    def _get_pct_type(self, type):
        res = super(tcv_account_anual_report, self)._get_pct_type(type)
        return res

    def _get_trial_balance(self, cr, uid, ids, params, context):
        obj_per = self.pool.get('account.period')
        obj_tba = self.pool.get('tcv.trial.balance')
        date_start = params.get('date_start')
        date_end = params.get('date_end')
        ini_per_id = obj_per.find(cr, uid, date_start)[0]
        ini_per = obj_per.browse(cr, uid, ini_per_id, context=context)
        end_per_id = obj_per.find(cr, uid, date_end)[0]
        end_per = obj_per.browse(cr, uid, end_per_id, context=context)
        if ini_per.fiscalyear_id.id != end_per.fiscalyear_id.id:
            raise osv.except_osv(
                _('Error!'),
                _('Both dates must belong to same fiscal year'))
        res = []
        if date_end > ini_per.date_stop:
            date_end = ini_per.date_stop
        while date_end < params.get('date_end'):
            values = {
                'date_from': date_start,
                'date_to': date_end,
                'non_zero': False,
                'no_view': params.get('level', 4) == 5,
                'total_view': True,
                'level': params.get('level', 4),
                'show_code': True,
                'use_ident': False,
                'acc_from_id': params.get('acc_from_id', None),
                'acc_to_id': params.get('acc_to_id', None),
                }
            tba_id = obj_tba.create(cr, uid, values, context=None)
            obj_tba.load_wizard_lines(cr, uid, tba_id, context=None)
            res.append(obj_tba.browse(cr, uid, tba_id, context=context))
            bas_date = datetime.strptime(date_end, '%Y-%m-%d')
            per_date = bas_date + relativedelta(days=1)
            ini_per_id = obj_per.find(cr, uid, per_date)[0]
            ini_per = obj_per.browse(cr, uid, ini_per_id, context=context)
            date_start = ini_per.date_start
            date_end = params.get('date_end')
            if date_end > ini_per.date_stop:
                date_end = ini_per.date_stop
        return res

    def _get_account_data_by_month(
            self, cr, uid, ids, params, field, context):
        tba = self._get_trial_balance(cr, uid, ids, params, context)
        lines_ord = []
        data = []
        for obj_tba in tba:
            for l in obj_tba.line_ids:
                acc_name = l.acc_name.strip()
                date = time.strptime(obj_tba.date_from, '%Y-%m-%d')
                if acc_name not in lines_ord:
                    lines_ord.append(acc_name)
                data.append((
                    date.tm_year,
                    date.tm_mon,
                    l.account_id.code.strip(),
                    acc_name,
                    l[field],
                    ))
        return lines_ord, data

    def _get_account_balance_by_month(
            self, cr, uid, ids, params, context):
        return self._get_account_data_by_month(
            cr, uid, ids, params, 'balance', context)

    def _get_account_variation_by_month(
            self, cr, uid, ids, params, context):
        return self._get_account_data_by_month(
            cr, uid, ids, params, 'amount_period', context)

    ##--------------------------------------------------------- function fields

    _columns = {
        'type': fields.selection(
            __TCV_ACCOUNT_ANUAL_REPORT_TYPES__, string='Type', required=True,
            readonly=False),
        'level': fields.integer(
            'Account level', help="0=All levels"),
        'acc_from_id': fields.many2one(
            'account.account', 'Account From', ondelete='restrict'),
        'acc_to_id': fields.many2one(
            'account.account', 'Account To', ondelete='restrict'),
        #~ Must be added to corret % calculation
        'line_ids': fields.one2many(
            'tcv.account.anual.report.lines', 'line_id', 'Lines',
            readonly=True),
        'line_p_ids': fields.one2many(
            'tcv.account.anual.report.lines', 'line_id', 'Lines',
            readonly=True),
        'line_q_ids': fields.one2many(
            'tcv.account.anual.report.lines', 'line_id', 'Lines',
            readonly=True),
        'line_pq_ids': fields.one2many(
            'tcv.account.anual.report.lines', 'line_id', 'Lines',
            readonly=True),
        }

    _defaults = {
        'type': lambda *a: 10,
        'level': lambda *a: 4,
        }

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    def button_load_monthly_lines(self, cr, uid, ids, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        brw = self.browse(cr, uid, ids[0], context={})
        params = self.get_report_default_params(cr, uid, ids, brw)
        params.update({
            'level': brw.level,
            'acc_from_id': brw.acc_from_id,
            'acc_to_id': brw.acc_to_id,
            })
        if params['type'] == 10:
            lines_ord, data = self._get_account_balance_by_month(
                cr, uid, ids, params, context)
            params.update({'add_summary': True})
        elif params['type'] == 20:
            lines_ord, data = self._get_account_variation_by_month(
                cr, uid, ids, params, context)
            params.update({'add_summary': True})
        else:
            lines_ord = []
            data = []
        self.load_report_data(cr, uid, ids, lines_ord, data, params, context)
        return True

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_account_anual_report()


##---------------------------------------------------- tcv_account_report_lines


#~ Must be added to corret % calculation
class tcv_account_report_lines(osv.osv_memory):

    _inherit = 'tcv.monthly.report.lines'

    _name = 'tcv.account.anual.report.lines'

    _columns = {
        'line_id': fields.many2one(
            'tcv.account.anual.report', 'Line', required=True,
            ondelete='cascade'),
        }

tcv_account_report_lines()


##---------------------------------------------------------------------- Parser


class parser_tcv_account_anual_report(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        context = context or {}
        super(parser_tcv_account_anual_report, self).__init__(
            cr, uid, name, context=context)
        self.localcontext.update({
            'get_sel_str': self._get_sel_str,
            'get_summary': self._get_summary,
            })
        self.context = context

    def _get_sel_str(self, type, val):
        if not type or not val:
            return ''
        types = {}
        for item in __TCV_ACCOUNT_ANUAL_REPORT_TYPES__:
            types.update({item[0]: _(item[1])})
        values = {'type': types,
                  }
        return values[type].get(val, '')

    def _get_summary(self, obj_lines, *args):
        '''
        obj_lines: an obj.line_ids (lines to be totalized)
        args: [string] with csv field names to be totalized

        Use in rml:
        [[ repeatIn(get_summary(o.line_ids, ('fld_1,fld_2,...')), 't') ]]
        '''
        totals = {}
        field_list = args[0][0]
        fields = field_list.split(',')
        for key in fields:
            totals[key] = 0
        for line in obj_lines:
            for key in fields:
                totals[key] += line[key]
        return [totals]

report_sxw.report_sxw(
    'report.tcv.account.anual.report.report',
    'tcv.account.anual.report',
    'addons/tcv_monthly_report/report/tcv_monthly_report.rml',
    parser=parser_tcv_account_anual_report,
    header=False
    )
