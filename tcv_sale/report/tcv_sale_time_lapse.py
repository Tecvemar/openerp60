# -*- encoding: utf-8 -*-
##############################################################################
#    Company:
#    Author: Gabriel
#    Creation Date: 2015-12-09
#    Version: 1.0
#
#    Description:
#
#
##############################################################################
from report import report_sxw
#~ from datetime import datetime
from osv import fields, osv
#~ from tools.translate import _
#~ import pooler
#~ import decimal_precision as dp
import time
#~ import netsvc


class parser_tcv_sale_time_lapse(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        context = context or {}
        super(parser_tcv_sale_time_lapse, self).__init__(
            cr, uid, name, context=context)
        self.localcontext.update({
            'get_summary': self._get_summary,
            })
        self.context = context

    def _get_summary(self, obj_lines, *args):
        '''
        obj_lines: an obj.line_ids (lines to be totalized)
        args: [string] with csv field names to be totalized

        Use in rml:
        [[ repeatIn(get_summary(o.line_ids, ['field_1,field_2'], 't') ]]
        '''
        totals = {}
        field_list = args[0][0]
        fields = field_list.split(',')
        for key in fields:
            totals[key] = 0
        qty = 0.0
        for line in obj_lines:
            qty += 1.0
            for key in fields:
                totals[key] += line[key]
        for key in fields:
            totals[key] = round(totals[key] / qty, 2)
        return [totals]

report_sxw.report_sxw(
    'report.tcv.sale.time.lapse.report',
    'tcv.sale.time.lapse',
    'addons/tcv_sale/report/tcv_sale_time_lapse.rml',
    parser=parser_tcv_sale_time_lapse,
    header=False
    )

##--------------------------------------------------------- tcv_sale_time_lapse


class tcv_sale_time_lapse(osv.osv_memory):

    _name = 'tcv.sale.time.lapse'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def _clear_lines(self, cr, uid, ids, context):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        unlink_ids = []
        for item in self.browse(cr, uid, ids, context={}):
            for l in item.line_ids:
                unlink_ids.append((2, l.id))
            self.write(
                cr, uid, ids, {'line_ids': unlink_ids}, context=context)
        return True

    def default_get(self, cr, uid, fields, context=None):
        data = super(tcv_sale_time_lapse, self).default_get(
            cr, uid, fields, context)
        data.update({
            'date_from': time.strftime('%Y-01-01'),
            'date_to': time.strftime('%Y-12-31'),
            })
        return data

    ##--------------------------------------------------------- function fields

    _columns = {
        'date_from': fields.date(
            'Date from', required=True, readonly=True,
            states={'draft': [('readonly', False)]}, select=True),
        'date_to': fields.date(
            'Date to', required=True, readonly=True,
            states={'draft': [('readonly', False)]}, select=True),
        'company_id': fields.many2one(
            'res.company', 'Company', required=True, readonly=True,
            ondelete='restrict'),
        'line_ids': fields.one2many(
            'tcv.sale.time.lapse.lines', 'line_id', 'Line ids',
            readonly=True),
        'loaded': fields.boolean(
            'Loaded'),
        }

    _defaults = {
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company').
        _company_default_get(cr, uid, self._name, context=c),
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    def button_load_in_process(self, cr, uid, ids, context=None):
        #~ Get in Process
        ids = isinstance(ids, (int, long)) and [ids] or ids
        brw = self.browse(cr, uid, ids[0], context={})
        #~ This sql query returns a view with products in process
        sql = '''
select pt.name,
       round(avg(extract(days from ai.date_invoice - spl.date)+1)) as
       avg_lapse,
       round(min(extract(days from ai.date_invoice - spl.date)+1)) as
       min_lapse,
       round(max(extract(days from ai.date_invoice - spl.date))+1) as
       max_lapse,
       count(ail.id) as slabs,
       sum(case when extract(days from ai.date_invoice - spl.date)+1
       between  0 and 15 then 1 else 0 end) as days0_15,
       sum(case when extract(days from ai.date_invoice - spl.date)+1
       between 16 and 30 then 1 else 0 end) as days16_30,
       sum(case when extract(days from ai.date_invoice - spl.date)+1
       between 31 and 45 then 1 else 0 end) as days31_45,
       sum(case when extract(days from ai.date_invoice - spl.date)+1 > 45
       then 1 else 0 end) as days45_more
from account_invoice_line ail
left join account_invoice ai on ail.invoice_id = ai.id
left join product_template pt on ail.product_id = pt.id
left join stock_production_lot spl on ail.prod_lot_id = spl.id
where pt.categ_id = 49 and ai.type = 'out_invoice' and
      ai.state in ('open', 'paid') and
      ai.date_invoice between '%(date_from)s' and
                              '%(date_to)s' and
      spl.date > '2014-01-01'
group by pt.name
order by pt.name
        ''' % {'date_from': brw.date_from,
               'date_to': brw.date_to}
        cr.execute(sql)
        line_ids = []
        for item in cr.dictfetchall():
            line_ids.append(
                (0, 0, {'name': item.get('name'),
                        'avg_lapse': item.get('avg_lapse'),
                        'min_lapse': item.get('min_lapse'),
                        'max_lapse': item.get('max_lapse'),
                        'slabs': item.get('slabs'),
                        'days0_15': item.get('days0_15'),
                        'days16_30': item.get('days16_30'),
                        'days31_45': item.get('days31_45'),
                        'days45_more': item.get('days45_more'),
                        }))
        if line_ids:
            self._clear_lines(cr, uid, ids, context)
            self.write(cr, uid, ids, {
                'line_ids': line_ids, 'loaded': bool(line_ids)},
                context=context)
        return True

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_sale_time_lapse()


##--------------------------------------------------- tcv_sale_time_lapse_lines


class tcv_sale_time_lapse_lines(osv.osv_memory):

    _name = 'tcv.sale.time.lapse.lines'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'line_id': fields.many2one(
            'tcv.sale.time.lapse', 'Lines', required=True,
            ondelete='cascade', readonly=True),
        'name': fields.char(
            'Name', size=64),
        'avg_lapse': fields.integer(
            'Avg lapse'),
        'min_lapse': fields.integer(
            'Min lapse'),
        'max_lapse': fields.integer(
            'Max lapse'),
        'slabs': fields.integer(
            'Slabs'),
        'days0_15': fields.integer(
            'Days 0-15'),
        'days16_30': fields.integer(
            'Days 16-30'),
        'days31_45': fields.integer(
            'Days 31-45'),
        'days45_more': fields.integer(
            'Days >45'),
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

tcv_sale_time_lapse_lines()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
