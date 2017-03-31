# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description: Report parser for: tcv_sale_top_10
#
#
##############################################################################

from osv import osv, fields
from tools.translate import _
from report import report_sxw


__tcv_sale_top_10_types__ = [
    ('customers_by_amount_ord', 'Customers by amount (Orders)'),
    ('customers_by_qty_ord', 'Customers by quantity (Orders)'),
    ('customers_by_amount_inv', 'Customers by amount (Invoices)'),
    ('customers_by_qty_inv', 'Customers by quantity (Invoices)'),
    ('products_by_amount_ord', 'Products by amount (Orders)'),
    ('products_by_qty_ord', 'Products by quantity (Orders)'),
    ('products_by_amount_inv', 'Products by amount (Invoices)'),
    ('products_by_qty_inv', 'Products by quantity (Invoices)'),
    ]


##----------------------------------------------- parser_tcv_sale_top_10_report


class parser_tcv_sale_top_10_report(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        context = context or {}
        super(parser_tcv_sale_top_10_report, self).__init__(
            cr, uid, name, context=context)
        self.localcontext.update({
            'get_str_type': self._get_str_type,
            'get_summary': self._get_summary,
            })
        self.context = context

    def _get_str_type(self, type):
        for item in __tcv_sale_top_10_types__:
            if type == item[0]:
                return item[1]
        return ''

    def _get_summary(self, obj_lines, *args):
        '''
        obj_lines: an obj.line_ids (lines to be totalized)
        args: [string] with csv field names to be totalized

        Use in rml:
        [[ repeatIn(get_summary(o.line_ids, ('fld_1', 'fld_2'..)), 't') ]]
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
    'report.tcv.sale.top.10.report',
    'tcv.sale.top.10',
    'addons/tcv_monthly_report/report/tcv_top_ten_report.rml',
    parser=parser_tcv_sale_top_10_report,
    header=False
    )

##------------------------------------------------------------- tcv_sale_top_10


class tcv_sale_top_10(osv.osv_memory):

    _inherit = 'tcv.top.ten.report'

    _name = 'tcv.sale.top.10'

    _description = ''

    ##-------------------------------------------------------------------------

    def default_get(self, cr, uid, fields, context=None):
        data = super(tcv_sale_top_10, self).default_get(
            cr, uid, fields, context)
        data.update({
            'name': _('Sales top 10'),
            })
        return data

    ##------------------------------------------------------- _internal methods

    def _customers_by_amount_ord(self, cr, uid, item, context):
        """ Function doc """
        res = {}
        params = self._get_sql_params(item)
        sql = """
        select rp.name as name,
               sum(l.product_uom_qty) as quantity,
               sum(l.product_uom_qty*l.price_unit) as amount
        from sale_order_line l
        left join sale_order i on l.order_id = i.id
        left join product_uom u on l.product_uom = u.id
        left join product_template pt on l.product_id = pt.id
        left join product_product pp on l.product_id = pp.id
        left join product_category pc on pt.categ_id = pc.id
        left join res_partner rp on i.partner_id = rp.id
        where i.date_order between %(date_start)s and
                                   %(date_end)s and
                                   i.state not in ('draft','cancel')
        group by rp.name
        order by 3 desc
        limit %(limit)s
        """
        cr.execute(sql, params)
        values = cr.dictfetchall()
        if values:
            res.update({'line_ids': [(0,0,x) for x in values]})
        return res

    def _customers_by_qty_ord(self, cr, uid, item, context):
        """ Function doc """
        res = {}
        params = self._get_sql_params(item)
        sql = """
        select rp.name as name,
               sum(l.product_uom_qty) as quantity,
               sum(l.product_uom_qty*l.price_unit) as amount
        from sale_order_line l
        left join sale_order i on l.order_id = i.id
        left join product_uom u on l.product_uom = u.id
        left join product_template pt on l.product_id = pt.id
        left join product_product pp on l.product_id = pp.id
        left join product_category pc on pt.categ_id = pc.id
        left join res_partner rp on i.partner_id = rp.id
        where i.date_order between %(date_start)s and
                                   %(date_end)s and
                                   i.state not in ('draft','cancel')
        group by rp.name
        order by 2 desc
        limit %(limit)s
        """
        cr.execute(sql, params)
        values = cr.dictfetchall()
        if values:
            res.update({'line_ids': [(0,0,x) for x in values]})
        return res

    def _customers_by_amount_inv(self, cr, uid, item, context):
        """ Function doc """
        res = {}
        params = self._get_sql_params(item)
        sql = """
        select rp.name as name,
               sum(l.quantity) as quantity,
               sum(l.quantity*l.price_unit) as amount
        from account_invoice_line l
        left join account_invoice i on l.invoice_id = i.id
        left join product_uom u on l.uos_id = u.id
        left join res_currency c on i.currency_id = c.id
        left join product_template pt on l.product_id = pt.id
        left join product_category pc on pt.categ_id = pc.id
        left join res_partner rp on i.partner_id = rp.id
        where i.date_invoice between %(date_start)s and
                                     %(date_end)s and
                                     i.type = 'out_invoice' and
                                     i.state in ('open','paid')
        group by rp.ref, rp.name, u.name, c.symbol
        order by 3 desc
        limit %(limit)s
        """
        cr.execute(sql, params)
        values = cr.dictfetchall()
        if values:
            res.update({'line_ids': [(0,0,x) for x in values]})
        return res

    def _customers_by_qty_inv(self, cr, uid, item, context):
        """ Function doc """
        res = {}
        params = self._get_sql_params(item)
        sql = """
        select rp.name as name,
               sum(l.quantity) as quantity,
               sum(l.quantity*l.price_unit) as amount
        from account_invoice_line l
        left join account_invoice i on l.invoice_id = i.id
        left join product_uom u on l.uos_id = u.id
        left join res_currency c on i.currency_id = c.id
        left join product_template pt on l.product_id = pt.id
        left join product_category pc on pt.categ_id = pc.id
        left join res_partner rp on i.partner_id = rp.id
        where i.date_invoice between %(date_start)s and
                                     %(date_end)s and
                                     i.type = 'out_invoice' and
                                     i.state in ('open','paid')
        group by rp.ref, rp.name, u.name, c.symbol
        order by 2 desc
        limit %(limit)s
        """
        cr.execute(sql, params)
        values = cr.dictfetchall()
        if values:
            res.update({'line_ids': [(0,0,x) for x in values]})
        return res


    def _products_by_amount_ord(self, cr, uid, item, context):
        """ Function doc """
        res = {}
        params = self._get_sql_params(item)
        sql = """
        select pt.name as name,
               sum(l.product_uom_qty) as quantity,
               sum(l.product_uom_qty*l.price_unit) as amount
        from sale_order_line l
        left join sale_order i on l.order_id = i.id
        left join product_uom u on l.product_uom = u.id
        left join product_template pt on l.product_id = pt.id
        left join product_product pp on l.product_id = pp.id
        left join product_category pc on pt.categ_id = pc.id
        left join res_partner rp on i.partner_id = rp.id
        where i.date_order between %(date_start)s and
                                   %(date_end)s and
                                   i.state not in ('draft','cancel')
        group by pt.name
        order by 3 desc
        limit %(limit)s
        """
        cr.execute(sql, params)
        values = cr.dictfetchall()
        if values:
            res.update({'line_ids': [(0,0,x) for x in values]})
        return res

    def _products_by_qty_ord(self, cr, uid, item, context):
        """ Function doc """
        res = {}
        params = self._get_sql_params(item)
        sql = """
        select pt.name as name,
               sum(l.product_uom_qty) as quantity,
               sum(l.product_uom_qty*l.price_unit) as amount
        from sale_order_line l
        left join sale_order i on l.order_id = i.id
        left join product_uom u on l.product_uom = u.id
        left join product_template pt on l.product_id = pt.id
        left join product_product pp on l.product_id = pp.id
        left join product_category pc on pt.categ_id = pc.id
        left join res_partner rp on i.partner_id = rp.id
        where i.date_order between %(date_start)s and
                                   %(date_end)s and
                                   i.state not in ('draft','cancel')
        group by pt.name
        order by 2 desc
        limit %(limit)s
        """
        cr.execute(sql, params)
        values = cr.dictfetchall()
        if values:
            res.update({'line_ids': [(0,0,x) for x in values]})
        return res

    def _products_by_amount_inv(self, cr, uid, item, context):
        """ Function doc """
        res = {}
        params = self._get_sql_params(item)
        sql = """
        select pt.name as name,
               sum(l.quantity) as quantity,
               sum(l.quantity*l.price_unit) as amount
        from account_invoice_line l
        left join account_invoice i on l.invoice_id = i.id
        left join product_uom u on l.uos_id = u.id
        left join res_currency c on i.currency_id = c.id
        left join product_template pt on l.product_id = pt.id
        left join product_product pp on l.product_id = pp.id
        left join product_category pc on pt.categ_id = pc.id
        left join res_partner rp on i.partner_id = rp.id
        where i.date_invoice between %(date_start)s and
                                     %(date_end)s and
                                     i.type = 'out_invoice' and
                                     i.state in ('open','paid')
        group by  pp.default_code, pt.name, u.name, c.symbol
        order by 3 desc
        limit %(limit)s
        """
        cr.execute(sql, params)
        values = cr.dictfetchall()
        if values:
            res.update({'line_ids': [(0,0,x) for x in values]})
        return res

    def _products_by_qty_inv(self, cr, uid, item, context):
        """ Function doc """
        res = {}
        params = self._get_sql_params(item)
        sql = """
        select pt.name  as name,
               sum(l.quantity) as quantity,
               sum(l.quantity*l.price_unit) as amount
        from account_invoice_line l
        left join account_invoice i on l.invoice_id = i.id
        left join product_uom u on l.uos_id = u.id
        left join res_currency c on i.currency_id = c.id
        left join product_template pt on l.product_id = pt.id
        left join product_product pp on l.product_id = pp.id
        left join product_category pc on pt.categ_id = pc.id
        left join res_partner rp on i.partner_id = rp.id
        where i.date_invoice between %(date_start)s and
                                     %(date_end)s and
                                     i.type = 'out_invoice' and
                                     i.state in ('open','paid')
        group by  pp.default_code, pt.name, u.name, c.symbol
        order by 2 desc
        limit %(limit)s
        """
        cr.execute(sql, params)
        values = cr.dictfetchall()
        if values:
            res.update({'line_ids': [(0,0,x) for x in values]})
        return res


    ##--------------------------------------------------------- function fields

    _columns = {
        'type': fields.selection(
            __tcv_sale_top_10_types__, string='Type', required=True,
            readonly=False),
        }

    _defaults = {
        'type': lambda *a: 'customers_by_amount_ord',
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    def load_report_data(self, cr, uid, item, context):
        '''
            Replace in inheriteds models
        '''
        res = {}
        if item.type == 'customers_by_amount_ord':
            res = self._customers_by_amount_ord(cr, uid, item, context)
        elif item.type == 'customers_by_qty_ord':
            res = self._customers_by_qty_ord(cr, uid, item, context)
        elif item.type == 'customers_by_amount_inv':
            res = self._customers_by_amount_inv(cr, uid, item, context)
        elif item.type == 'customers_by_qty_inv':
            res = self._customers_by_qty_inv(cr, uid, item, context)
        elif item.type == 'products_by_amount_ord':
            res = self._products_by_amount_ord(cr, uid, item, context)
        elif item.type == 'products_by_qty_ord':
            res = self._products_by_qty_ord(cr, uid, item, context)
        elif item.type == 'products_by_amount_inv':
            res = self._products_by_amount_inv(cr, uid, item, context)
        elif item.type == 'products_by_qty_inv':
            res = self._products_by_qty_inv(cr, uid, item, context)
        return res

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_sale_top_10()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
