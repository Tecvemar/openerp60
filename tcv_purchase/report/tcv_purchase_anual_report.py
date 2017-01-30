# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description: Report parser for: tcv_purchase_anual_report
#
#
##############################################################################
#~ import time
#~ import pooler
from report import report_sxw
from tools.translate import _
from osv import fields, osv


__TCV_purchase_ANUAL_REPORT_TYPES__ = [
    (10, _('Block purchases by product (Volume)')),
    (20, _('Block purchases by product (Pieces)')),
    (30, _('Block purchases by product (Amount)')),
    ]


##------------------------------------------------------- tcv_purchase_anual_report


class tcv_purchase_anual_report(osv.osv_memory):

    _inherit = 'tcv.monthly.report'

    _name = 'tcv.purchase.anual.report'

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def default_get(self, cr, uid, fields, context=None):
        data = super(tcv_purchase_anual_report, self).default_get(
            cr, uid, fields, context)
        data.update({
            'name': _('Annual Summary of purchases'),
            })
        return data

    def _get_pct_type(self, type):
        res = super(tcv_purchase_anual_report, self)._get_pct_type(type)
        return res

    def _get_block_purchases_by_product_volume(
            self, cr, uid, ids, params, context):
        lines_ord = []
        sql = """
        select pt.id, pt.name from product_template pt
        left join product_product pp on pt.id = pp.id
        where pp.stock_driver='block'
        order by pt.name
        """
        cr.execute(sql)
        for row in cr.fetchall():
            lines_ord.append(row[1])
        params.update(
            {'amount_field': context.get('amount_field', 'amount')})
        sql = """
        select year, month, default_code as code, name,
               %(amount_field)s as quantity
        from (
            select pp.default_code, pt.name as name,
                   extract(year from ai.date_invoice) AS year,
                   extract(month from ai.date_invoice) AS month,
                   sum(ail.quantity) as quantity,
                   sum(ail.pieces) as pieces,
                   sum(ail.quantity * ail.price_unit) as amount
            from account_invoice ai
            left join account_invoice_line ail on ai.id = ail.invoice_id
            left join product_product pp on ail.product_id=pp.id
            left join product_template pt on ail.product_id=pt.id
            left join res_currency c on ai.currency_id = c.id
            where ai.type = 'in_invoice' and ai.state in ('open','paid') and
                  pp.stock_driver='block' and
                  ai.date_invoice between '%(date_start)s 00:00:00' and
                                          '%(date_end)s 23:59:59' and
                  ai.company_id = %(company_id)s
            group by 1,2,3,4
        ) as q
        """ % params
        cr.execute(sql)
        data = cr.fetchall()
        return lines_ord, data


    ##--------------------------------------------------------- function fields

    _columns = {
        'type': fields.selection(
            __TCV_purchase_ANUAL_REPORT_TYPES__, string='Type', required=True,
            readonly=False),
        #~ Must be added to corret % calculation
        'line_ids': fields.one2many(
            'tcv.purchase.anual.report.lines', 'line_id', 'Lines',
            readonly=True),
        'line_p_ids': fields.one2many(
            'tcv.purchase.anual.report.lines', 'line_id', 'Lines',
            readonly=True),
        'line_q_ids': fields.one2many(
            'tcv.purchase.anual.report.lines', 'line_id', 'Lines',
            readonly=True),
        'line_pq_ids': fields.one2many(
            'tcv.purchase.anual.report.lines', 'line_id', 'Lines',
            readonly=True),
        }

    _defaults = {
        'type': lambda *a: 10,
        'remove_zero': lambda *a: True,
        }

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    def button_load_monthly_lines(self, cr, uid, ids, context=None):
        context = context or {}
        ids = isinstance(ids, (int, long)) and [ids] or ids
        brw = self.browse(cr, uid, ids[0], context={})
        params = self.get_report_default_params(cr, uid, ids, brw)
        if params['type'] in (10, 20, 30):
            fields = {
                10: 'quantity', 20: 'pieces', 30: 'amount',
                }
            context = context or {}
            context.update({'amount_field': fields[params['type']]})
            lines_ord, data = self._get_block_purchases_by_product_volume(
                cr, uid, ids, params, context)
            if params['type'] == 20:
                params.update({'digits': 0})
        else:
            lines_ord = []
            data = []
        self.load_report_data(cr, uid, ids, lines_ord, data, params, context)
        return True

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_purchase_anual_report()


##------------------------------------------------- tcv_purchase_anual_report_lines


#~ Must be added to corret % calculation
class tcv_purchase_anual_report_lines(osv.osv_memory):

    _inherit = 'tcv.monthly.report.lines'

    _name = 'tcv.purchase.anual.report.lines'

    _columns = {
        'line_id': fields.many2one(
            'tcv.purchase.anual.report', 'Line', required=True,
            ondelete='cascade'),
        }

tcv_purchase_anual_report_lines()


##---------------------------------------------------------------------- Parser


class parser_tcv_purchase_anual_report(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        context = context or {}
        super(parser_tcv_purchase_anual_report, self).__init__(
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
        for item in __TCV_purchase_ANUAL_REPORT_TYPES__:
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
    'report.tcv.purchase.anual.report.report',
    'tcv.purchase.anual.report',
    'addons/tcv_monthly_report/report/tcv_monthly_report.rml',
    parser=parser_tcv_purchase_anual_report,
    header=False
    )
