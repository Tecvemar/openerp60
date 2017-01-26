# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description: Report parser for: tcv_import_management
#
#
##############################################################################
#~ import time
#~ import pooler
from report import report_sxw
#~ from tools.translate import _


class parser_tcv_import_management(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        context = context or {}
        super(parser_tcv_import_management, self).__init__(
            cr, uid, name, context=context)
        self.localcontext.update({
            'get_currency_rate': self._get_currency_rate,
            'get_account_lines': self._get_account_lines,
            'get_summary': self._get_summary,
            })
        self.context = context

    def _get_currency_rate(self, obj):
        #~ obj: self.pool.get('account.invoice').browse
        obj_inv = self.pool.get('account.invoice')
        # implemented in tcv_purchase
        rate = obj_inv.get_invoice_currency_rate(
            self.cr, self.uid, obj)
        return rate

    def _get_account_lines(self, obj):
        sql = '''
        select aa.code, aa.name, count(q.id) as lines,
               sum(debit) as debit, sum(credit) as credit
        from (
            select aml.*
            from tcv_import_management im
            left join account_invoice ai on ai.import_id = im.id
            left join account_move am on am.id = ai.move_id
            left join account_move_line aml on aml.move_id = am.id
            where ai.import_id = %(id)s
            union
            select aml.*
            from account_invoice ai
            left join dua_form df on df.id = ai.dua_form_id
            left join customs_form cf on cf.dua_form_id = df.id
            left join account_move am on am.id = cf.move_id
            left join account_move_line aml on aml.move_id = am.id
            where ai.import_id = %(id)s and ai.dua_form_id is not null
            ) as q
        left join account_account aa on q.account_id = aa.id
        where aa.type not in ('payable', 'receivable')
        group by aa.code, aa.name
        order by aa.code
        ''' % {'id': obj.id}
        self.cr.execute(sql)
        return self.cr.dictfetchall()

    def _get_summary(self, obj_lines, *args):
        '''
        obj_lines: an obj.line_ids (lines to be totalized)
        args: List, see below

        Use in rml:
        [[ repeatIn(get_summary(o.line_ids, ['fields in csv string']), 't') ]]
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
    'report.tcv.import.management.report',
    'tcv.import.management',
    'addons/tcv_import_management/report/tcv_import_management.rml',
    parser=parser_tcv_import_management,
    header=False,
    )
