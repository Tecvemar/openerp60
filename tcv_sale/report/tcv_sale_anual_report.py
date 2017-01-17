# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description: Report parser for: tcv_sale_anual_report
#
#
##############################################################################
#~ import time
#~ import pooler
from report import report_sxw
from tools.translate import _
from osv import fields, osv


__TCV_sale_ANUAL_REPORT_TYPES__ = [
    (10, _('Sales by unit and volume (Quantity)')),
    (20, _('Sales by color and quality (Amount)')),
    (30, _('Sales by category (Amount)')),
    (40, _('Sales by category (Quantity)')),
    (35, _('Sales by category (Amount) related partners')),
    (45, _('Sales by category (Quantity) related partners')),
    (50, _('Sales by currency (Amount)')),
    (60, _('Sales by salesman (Amount)')),
    (70, _('Sales by product (Amount)')),  # categ_id filter
    (80, _('Sales by product (Quantity)')),  # categ_id filter
    (90, _('Sales by partner fiscal type (Transactions)')),
    (100, _('Sale analisys - Related partners totals')),
    (110, _('Sale analisys - Related partners m2 (Amount)')),
    (120, _('Sale analisys - Related partners m2 (Quantity)')),
    (130, _('Sale analisys - Related partners other UoM (Amount)')),
    ]


##------------------------------------------------------- tcv_sale_anual_report


class tcv_sale_anual_report(osv.osv_memory):

    _inherit = 'tcv.monthly.report'

    _name = 'tcv.sale.anual.report'

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def default_get(self, cr, uid, fields, context=None):
        data = super(tcv_sale_anual_report, self).default_get(
            cr, uid, fields, context)
        data.update({
            'name': _('Annual Summary of sales'),
            })
        return data

    def _get_pct_type(self, type):
        res = super(tcv_sale_anual_report, self)._get_pct_type(type)
        if type in (30, 35):
            res = 'row'
        elif type in (40, 45, 100, 110, 120, 130):
            res = 'col'
        return res

    def _get_sales_by_product_and_volume_units(
            self, cr, uid, ids, params, context):
        lines_ord = []
        sql = """
        select category_id, name from product_uom
        order by category_id, name
        """
        cr.execute(sql)
        for row in cr.fetchall():
            lines_ord.append(row[1])
        sql = """
        select extract(year from i.date_invoice) AS year,
               extract(month from i.date_invoice) AS month,
               u.name as code, u.name,
               sum(l.quantity) as quantity
        from account_invoice_line l
        left join account_invoice i on l.invoice_id = i.id
        left join product_uom u on l.uos_id = u.id
        where i.date_invoice between '%(date_start)s 00:00:00' and
                                     '%(date_end)s 23:59:59' and
              i.type = 'out_invoice' and
              i.state in ('open','paid') and
              i.company_id = %(company_id)s
        group by year, month, u.name, u.name
        order by 1,2,3
        """ % params
        cr.execute(sql)
        data = cr.fetchall()
        return lines_ord, data

    def _get_sales_by_color_and_quality_units(
            self, cr, uid, ids, params, context):
        lines_ord = []
        sql = """
        select distinct u.name as code,
               coalesce(pf.name || ', ' || u.name || ', ' || c.symbol) as name
        from account_invoice_line l
        left join account_invoice i on l.invoice_id = i.id
        left join res_currency c on i.currency_id = c.id
        left join product_uom u on l.uos_id = u.id
        left join product_product pr on l.product_id = pr.id
        left join product_product_features pf on pr.color_id = pf.id
        where i.type = 'out_invoice' and
              i.state in ('open','paid') and
              i.company_id = %(company_id)s
        group by u.name, pf.name, c.symbol
        order by 2
        """ % params
        cr.execute(sql)
        for row in cr.fetchall():
            lines_ord.append(row[1])
        sql = """
        select extract(year from i.date_invoice) AS year,
               extract(month from i.date_invoice) AS month,
               u.name as code,
               coalesce(pf.name || ', ' || u.name || ', ' || c.symbol) as name,
               sum(l.quantity*l.price_unit) as quantity
        from account_invoice_line l
        left join account_invoice i on l.invoice_id = i.id
        left join res_currency c on i.currency_id = c.id
        left join product_uom u on l.uos_id = u.id
        left join product_product pr on l.product_id = pr.id
        left join product_product_features pf on pr.color_id = pf.id
        where i.date_invoice between '%(date_start)s 00:00:00' and
                                     '%(date_end)s 23:59:59' and
              i.type = 'out_invoice' and
              i.state in ('open','paid') and
              i.company_id = %(company_id)s
        group by year, month, u.name, pf.name, c.symbol
        order by 1,2,3
        """ % params
        cr.execute(sql)
        data = cr.fetchall()
        return lines_ord, data

    def _get_related_partner(self, cr, uid, context):
        related_partner = ''
        if context.get('related_partner'):
            obj_partner = self.pool.get('res.partner')
            partner_ids = obj_partner.search(
                cr, uid, [('category_id', '=', 14)])
            if partner_ids:
                partner_list = str(tuple(partner_ids))
                related_partner = 'and i.partner_id in %s' % partner_list
        return related_partner

    def _get_sales_by_categoty(
            self, cr, uid, ids, params, context):
        context = context or {}
        lines_ord = []
        params.update({
            'related_partner': self._get_related_partner(cr, uid, context),
            'amount_field': context.get('amount_field', 'l.quantity'),
            })
        sql = """
        select distinct pc.code,
               coalesce(pc.name || ', ' || u.name || ', ' || c.symbol) as name
        from account_invoice_line l
        left join account_invoice i on l.invoice_id = i.id
        left join res_currency c on i.currency_id = c.id
        left join product_uom u on l.uos_id = u.id
        left join product_template pt on l.product_id = pt.id
        left join product_category pc on pt.categ_id = pc.id
        where i.type = 'out_invoice' and
              i.state in ('open','paid') and
              i.company_id = %(company_id)s
              %(related_partner)s
        group by pc.code, u.name, pc.name, c.symbol
        order by 2
        """ % params
        cr.execute(sql)
        for row in cr.fetchall():
            lines_ord.append(row[1])
        sql = """
        select extract(year from i.date_invoice) AS year,
               extract(month from i.date_invoice) AS month,
               pc.code as code,
               coalesce(pc.name || ', ' || u.name || ', ' || c.symbol) as name,
               sum(%(amount_field)s) as quantity
        from account_invoice_line l
        left join account_invoice i on l.invoice_id = i.id
        left join product_uom u on l.uos_id = u.id
        left join res_currency c on i.currency_id = c.id
        left join product_template pt on l.product_id = pt.id
        left join product_category pc on pt.categ_id = pc.id
        where i.date_invoice between '%(date_start)s 00:00:00' and
                                     '%(date_end)s 23:59:59' and
                                     i.type = 'out_invoice' and
                                     i.state in ('open','paid')
              %(related_partner)s
        group by year, month, pc.code, u.name, pc.name, c.symbol
        """ % params
        cr.execute(sql)
        data = cr.fetchall()
        return lines_ord, data

    def _get_sales_by_currency_amount(
            self, cr, uid, ids, params, context):
        lines_ord = []
        sql = """
        select distinct c.symbol as code,
               coalesce(c.name || ' (' || c.symbol || ')') as name
        from account_invoice_line l
        left join account_invoice i on l.invoice_id = i.id
        left join res_currency c on i.currency_id = c.id
        where i.type = 'out_invoice' and
              i.state in ('open','paid') and
              i.company_id = %(company_id)s
        group by c.name, c.symbol
        order by 2
        """ % params
        cr.execute(sql)
        for row in cr.fetchall():
            lines_ord.append(row[1])
        sql = """
        select extract(year from i.date_invoice) AS year,
               extract(month from i.date_invoice) AS month,
               c.symbol as code,
               coalesce(c.name || ' (' || c.symbol || ')') as name,
               sum(l.quantity*l.price_unit) as quantity
        from account_invoice_line l
        left join account_invoice i on l.invoice_id = i.id
        left join res_currency c on i.currency_id = c.id
        where i.date_invoice between '%(date_start)s 00:00:00' and
                                     '%(date_end)s 23:59:59' and
              i.type = 'out_invoice' and
              i.state in ('open','paid') and
              i.company_id = %(company_id)s
        group by year, month, c.name, c.symbol
        """ % params
        cr.execute(sql)
        data = cr.fetchall()
        return lines_ord, data

    def _get_sales_by_salesman_amount(
            self, cr, uid, ids, params, context):
        lines_ord = []
        sql = """
        select distinct r.name || c.symbol as code,
               coalesce(r.name || ', ' || c.symbol) as name
        from account_invoice_line l
        left join account_invoice i on l.invoice_id = i.id
        left join res_currency c on i.currency_id = c.id
        left join res_users r on i.user_id = r.id
        where i.type = 'out_invoice' and
              i.date_invoice between '%(date_start)s 00:00:00' and
                                     '%(date_end)s 23:59:59' and
              i.state in ('open','paid') and
              i.company_id = %(company_id)s
        group by r.name, c.symbol
        order by 2
        """ % params
        cr.execute(sql)
        for row in cr.fetchall():
            lines_ord.append(row[1])
        sql = """
        select extract(year from i.date_invoice) AS year,
               extract(month from i.date_invoice) AS month,
               r.name || c.symbol as code,
               coalesce(r.name || ', ' || c.symbol) as name,
               sum(l.quantity*l.price_unit) as quantity
        from account_invoice_line l
        left join account_invoice i on l.invoice_id = i.id
        left join res_currency c on i.currency_id = c.id
        left join res_users r on i.user_id = r.id
        where i.type = 'out_invoice' and
              i.date_invoice between '%(date_start)s 00:00:00' and
                                     '%(date_end)s 23:59:59' and
              i.state in ('open','paid') and
              i.company_id = %(company_id)s
        group by year, month, c.name, c.symbol, r.name
        """ % params
        cr.execute(sql)
        data = cr.fetchall()
        return lines_ord, data

    def _get_sales_by_product(
            self, cr, uid, ids, params, context):
        params.update({
            'amount_field': context.get('amount_field', 'l.quantity'),
            'categ_filter': context.get('categ_filter', '')
            })
        lines_ord = []
        sql = """
        select distinct pp.default_code,
               coalesce(pt.name || ', ' || u.name || ', ' || c.symbol) as name
        from account_invoice_line l
        left join account_invoice i on l.invoice_id = i.id
        left join res_currency c on i.currency_id = c.id
        left join product_uom u on l.uos_id = u.id
        left join product_template pt on l.product_id = pt.id
        left join product_category pc on pt.categ_id = pc.id
        left join product_product pp on l.product_id = pp.id
        where i.type = 'out_invoice' and
              i.state in ('open','paid') and
              i.company_id = %(company_id)s
              %(categ_filter)s
        group by pp.default_code, u.name, pt.name, c.symbol
        order by 2
        """ % params
        cr.execute(sql)
        for row in cr.fetchall():
            lines_ord.append(row[1])
        sql = """
        select extract(year from i.date_invoice) AS year,
               extract(month from i.date_invoice) AS month,
               pp.default_code as code,
               coalesce(pt.name || ', ' || u.name || ', ' || c.symbol) as name,
               sum(%(amount_field)s) as quantity
        from account_invoice_line l
        left join account_invoice i on l.invoice_id = i.id
        left join product_uom u on l.uos_id = u.id
        left join res_currency c on i.currency_id = c.id
        left join product_template pt on l.product_id = pt.id
        left join product_product pp on l.product_id = pp.id
        where i.date_invoice between '%(date_start)s 00:00:00' and
                                     '%(date_end)s 23:59:59' and
              i.type = 'out_invoice' and i.state in ('open','paid')
              %(categ_filter)s
        group by year, month, pp.default_code, u.name, pt.name, c.symbol
        """ % params
        cr.execute(sql)
        data = cr.fetchall()
        return lines_ord, data

    def _get_sales_by_partner_type(
            self, cr, uid, ids, params, context):
        lines_ord = ['Tax Payer', 'Non-Tax Payer']
        sql = """
        select extract(year from ai.date_invoice) AS year,
                       extract(month from ai.date_invoice) AS month,
                       rp.vat_subjected as code,
                       case when rp.vat_subjected then 'Tax Payer' else
                       'Non-Tax Payer' end as name,
                       count(ai.id) as quantity
        from account_invoice ai
        left join res_partner rp on ai.partner_id = rp.id
        where ai.date_invoice between '%(date_start)s 00:00:00' and
                                      '%(date_end)s 23:59:59' and
              ai.state in ('open','paid') and ai.type = 'out_invoice' and
              ai.company_id = %(company_id)s
        group by year, month,rp.vat_subjected
        order by 1,2,3
        """ % params
        cr.execute(sql)
        data = cr.fetchall()
        return lines_ord, data

    def _get_sale_analisys_for_related_partners(
            self, cr, uid, ids, params, context):
        lines_ord = [
            u"DISTRIBUIDORA ACROPOLIS, C.A, Bs",
            u"DISTRIBUIDORA ACROPOLIS GUAYANA, C.A, Bs",
            u"DISTRIBUIDORA ACROPOLIS MONAGAS, C.A., Bs",
            u"REVESTIMIENTO DACROPOLIS C.A., Bs",
            u"DISTRIBUIDORA ACROPOLIS BARQUISIMETO, C.A., Bs",
            u"DISTRIBUIDORA ACROPOLIS FALCÓN,C.A., Bs",
            u"GRANITOS DEL ORINOCO, S.A., Bs",
            u"Otros, Bs",
            u"Otros, US$",
            ]
        params.update(
            {'amount_field': context.get('amount_field', 'amount')})
        sql = """
        select year, month, partner_id as code, name,
               %(amount_field)s as quantity
        from (
            select 0 as partner_id, 'Otros' || ', ' || symbol as name,
               extract(year from ai.date_invoice) AS year,
               extract(month from ai.date_invoice) AS month,
                   sum(ail.quantity * ail.price_unit) as amount,
                   sum(case when ail.uos_id = 11 then
                       ail.quantity * ail.price_unit else 0 end) as amount_m2,
                   sum(case when ail.uos_id = 11 then
                       ail.quantity else 0 end) as qty_m2,
                   sum(case when ail.uos_id != 11 then
                       ail.quantity*ail.price_unit else 0 end) as amount_other
            from account_invoice ai
            left join account_invoice_line ail on ai.id = ail.invoice_id
            left join res_currency c on ai.currency_id = c.id
            left join product_template pt on ail.product_id = pt.id
            where ai.type = 'out_invoice' and ai.state in ('open','paid') and
                  pt.categ_id in (49, 50, 52, 53) and
                  ai.date_invoice between '%(date_start)s 00:00:00' and
                                          '%(date_end)s 23:59:59' and
                  ai.company_id = %(company_id)s and
                  ai.partner_id not in (select partner_id
                                        from res_partner_category_rel
                                        where category_id = 14)
            group by 1,2,3,4
            union
            select ai.partner_id, rp.name || ', ' || symbol as name,
               extract(year from ai.date_invoice) AS year,
               extract(month from ai.date_invoice) AS month,
                   sum(ail.quantity * ail.price_unit) as amount,
                   sum(case when ail.uos_id = 11 then
                       ail.quantity * ail.price_unit else 0 end) as amount_m2,
                   sum(case when ail.uos_id = 11 then
                       ail.quantity else 0 end) as qty_m2,
                   sum(case when ail.uos_id != 11 then
                       ail.quantity*ail.price_unit else 0 end) as amount_other
            from account_invoice ai
            left join account_invoice_line ail on ai.id = ail.invoice_id
            left join res_currency c on ai.currency_id = c.id
            left join res_partner rp on ai.partner_id = rp.id
            left join product_template pt on ail.product_id = pt.id
            where ai.type = 'out_invoice' and ai.state in ('open','paid') and
                  pt.categ_id in (49, 50, 52, 53) and
                  ai.date_invoice between '%(date_start)s 00:00:00' and
                                          '%(date_end)s 23:59:59' and
                  ai.company_id = %(company_id)s and
                  ai.partner_id in (select partner_id
                                    from res_partner_category_rel
                                    where category_id = 14)
            group by 1,2,3,4
        ) as q
        """ % params
        cr.execute(sql)
        data = cr.fetchall()
        return lines_ord, data

    ##--------------------------------------------------------- function fields

    _columns = {
        'type': fields.selection(
            __TCV_sale_ANUAL_REPORT_TYPES__, string='Type', required=True,
            readonly=False),
        #~ Must be added to corret % calculation
        'line_ids': fields.one2many(
            'tcv.sale.anual.report.lines', 'line_id', 'Lines',
            readonly=True),
        'line_p_ids': fields.one2many(
            'tcv.sale.anual.report.lines', 'line_id', 'Lines',
            readonly=True),
        'line_q_ids': fields.one2many(
            'tcv.sale.anual.report.lines', 'line_id', 'Lines',
            readonly=True),
        'line_pq_ids': fields.one2many(
            'tcv.sale.anual.report.lines', 'line_id', 'Lines',
            readonly=True),
        #~ Special filters
        'categ_id': fields.many2one(
            'product.category', 'Procuct\'s category'),
        }

    _defaults = {
        'type': lambda *a: 30,
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
        if params['type'] == 10:
            lines_ord, data = self._get_sales_by_product_and_volume_units(
                cr, uid, ids, params, context)
        elif params['type'] == 20:
            lines_ord, data = self._get_sales_by_color_and_quality_units(
                cr, uid, ids, params, context)
        elif params['type'] in (30, 35, 40, 45):
            fields = {
                30: 'l.quantity*l.price_unit',
                35: 'l.quantity*l.price_unit',
                40: 'l.quantity',
                45: 'l.quantity',
                }
            context = context or {}
            context.update({
                'amount_field': fields[params['type']],
                })
            if params['type'] in (35, 45):
                context.update({'related_partner': True})
            lines_ord, data = self._get_sales_by_categoty(
                cr, uid, ids, params, context)
            params.update({'digits': 0})
        elif params['type'] == 50:
            lines_ord, data = self._get_sales_by_currency_amount(
                cr, uid, ids, params, context)
        elif params['type'] == 60:
            lines_ord, data = self._get_sales_by_salesman_amount(
                cr, uid, ids, params, context)
        elif params['type'] in (70, 80):
            fields = {
                70: 'l.quantity*l.price_unit',
                80: 'l.quantity',
                }
            context = context or {}
            categ_filter = brw.categ_id and \
                'and categ_id = %s' % brw.categ_id.id or ''
            context.update({
                'amount_field': fields[params['type']],
                'categ_filter': categ_filter,
                })
            lines_ord, data = self._get_sales_by_product(
                cr, uid, ids, params, context)
        elif params['type'] == 90:
            lines_ord, data = self._get_sales_by_partner_type(
                cr, uid, ids, params, context)
            params.update({'add_summary': True,
                           'digits': 0,
                           })
        elif params['type'] in (100, 110, 120, 130):
            fields = {
                100: 'amount', 110: 'amount_m2',
                120: 'qty_m2', 130: 'amount_other',
                }
            if params['type'] == 110:
                params.update({'add_summary': True})
            context = context or {}
            context.update({'amount_field': fields[params['type']]})
            lines_ord, data = self._get_sale_analisys_for_related_partners(
                cr, uid, ids, params, context)
        else:
            lines_ord = []
            data = []
        self.load_report_data(cr, uid, ids, lines_ord, data, params, context)
        return True

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_sale_anual_report()


##------------------------------------------------- tcv_sale_anual_report_lines


#~ Must be added to corret % calculation
class tcv_sale_anual_report_lines(osv.osv_memory):

    _inherit = 'tcv.monthly.report.lines'

    _name = 'tcv.sale.anual.report.lines'

    _columns = {
        'line_id': fields.many2one(
            'tcv.sale.anual.report', 'Line', required=True,
            ondelete='cascade'),
        }

tcv_sale_anual_report_lines()


##---------------------------------------------------------------------- Parser


class parser_tcv_sale_anual_report(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        context = context or {}
        super(parser_tcv_sale_anual_report, self).__init__(
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
        for item in __TCV_sale_ANUAL_REPORT_TYPES__:
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
    'report.tcv.sale.anual.report.report',
    'tcv.sale.anual.report',
    'addons/tcv_monthly_report/report/tcv_monthly_report.rml',
    parser=parser_tcv_sale_anual_report,
    header=False
    )
