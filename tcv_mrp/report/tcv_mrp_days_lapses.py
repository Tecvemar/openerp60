# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description: Report parser for: tcv_mrp_days_lapses
#
#
##############################################################################
from report import report_sxw
#~ from datetime import datetime
from osv import fields, osv
#~ from tools.translate import _
#~ import pooler
import decimal_precision as dp
import time
#~ import netsvc


class parser_tcv_mrp_days_lapses(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        context = context or {}
        super(parser_tcv_mrp_days_lapses, self).__init__(
            cr, uid, name, context=context)
        self.localcontext.update({
            'get_summary': self._get_summary,
            })
        self.context = context

    def _get_summary(self, obj):
        fields = (
            'gangsaw_days', 'wait1_days', 'apom_days', 'wait2_days',
            'resin_days', 'wait3_days', 'polish_days', 'finish_days',
            'util_days', 'wait_days', 'total_days',
            )
        totals = {}
        for key in fields:
            totals[key] = 0
        qty = 0
        #~ Compute Totals
        for line in obj.line_ids:
            for key in fields:
                totals[key] += line[key]
            qty += 1
        totals.update({'qty': qty})
        #~ Compute average
        for key in fields:
            totals[key] = round(totals[key] / qty, 2)
        return [totals]


report_sxw.report_sxw(
    'report.tcv.mrp.days.lapses.report',
    'tcv.mrp.days.lapses',
    'addons/tcv_mrp/report/tcv_mrp_days_lapses.rml',
    parser=parser_tcv_mrp_days_lapses,
    header=False
    )


##--------------------------------------------------------- tcv_mrp_days_lapses


class tcv_mrp_days_lapses(osv.osv_memory):

    _name = 'tcv.mrp.days.lapses'

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
        data = super(tcv_mrp_days_lapses, self).default_get(
            cr, uid, fields, context)
        data.update({
            'date_from': time.strftime('%Y-01-01'),
            'date_to': time.strftime('%Y-12-31'),
            })
        return data

    ##--------------------------------------------------------- function fields

    _columns = {
        'date_from': fields.date(
            'Date from', required=True),
        'date_to': fields.date(
            'Date to', required=True),
        'company_id': fields.many2one(
            'res.company', 'Company', required=True, readonly=True,
            ondelete='restrict'),
        'loaded': fields.boolean(
            'Loaded'),
        'line_ids': fields.one2many(
            'tcv.mrp.days.lapses.lines', 'line_id', 'Lines',
            readonly=True),
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
select product_name,
       count(product_name) as qty,
       avg(gangsaw_days) as gangsaw_days,
       avg(wait1_days) as wait1_days,
       avg(apom_days) as apom_days,
       avg(wait2_days) as wait2_days,
       avg(resin_days) as resin_days,
       avg(wait3_days) as wait3_days,
       avg(polish_days) as polish_days,
       avg(finish_days) as finish_days,
       avg(gangsaw_days)+avg(apom_days)+avg(resin_days)+
       avg(polish_days)+avg(finish_days) as util_days,
       avg(wait1_days)+avg(wait2_days)+avg(wait3_days) as wait_days,
       avg(total_days) as total_days
from (
--Compute process lapse
select q.name as product_name,
       abs(extract(days from end_gangsaw - start_gangsaw)) as gangsaw_days,
       abs(extract(days from start_apom - end_gangsaw)) as wait1_days,
       abs(extract(days from end_apom - start_apom)) as apom_days,
       abs(extract(days from start_resin - end_apom)) as wait2_days,
       abs(extract(days from end_resin - start_resin)) as resin_days,
       abs(extract(days from start_polish - end_resin)) as wait3_days,
       abs(extract(days from end_polish - start_polish)) as polish_days,
       abs(extract(days from date_finish - end_polish)) as finish_days,
       abs(extract(days from date_finish - start_gangsaw)) as total_days

from (
select pt.name,
       p.name as process,
       p.ref,
       sp5.ref,
       tmg.date_start as start_gangsaw,
       tmg.date_end as end_gangsaw,
       sp4.ref,
       tmp2.date_start as start_apom,
       tmp2.date_end as end_apom,
       sp3.ref,
       tmr.date_start as start_resin,
       tmr.date_end as end_resin,
       sp2.ref,
       tmp1.date_start as start_polish,
       tmp1.date_end as end_polish,
       sp1.ref,
       fs.date_end as date_finish
from tcv_mrp_finished_slab fs
left join tcv_mrp_finished_slab_output fso on fso.task_id = fs.id
left join product_template pt on fso.product_id = pt.id
left join tcv_mrp_subprocess sp1 on fs.parent_id = sp1.id
left join tcv_mrp_process p on  sp1.process_id = p.id
--Polish data
left join tcv_mrp_subprocess sp2 on sp1.prior_id = sp2.id and
    sp2.template_id = 7
left join tcv_mrp_polish tmp1 on sp2.id = tmp1.parent_id
--Resin data
left join tcv_mrp_subprocess sp3 on sp2.prior_id = sp3.id and
    sp3.template_id = 6
left join tcv_mrp_resin tmr on sp3.id = tmr.parent_id
--Apom data
left join tcv_mrp_subprocess sp4 on sp3.prior_id = sp4.id and
    sp4.template_id = 5
left join tcv_mrp_polish tmp2 on sp4.id = tmp2.parent_id
--Gangsaw data
left join tcv_mrp_subprocess sp5 on sp4.prior_id = sp5.id and
    sp5.template_id in (1, 2, 3, 4)
left join tcv_mrp_gangsaw tmg on sp5.id = tmg.parent_id

where fs.date_end between '%(date_from)s 00:00:00' and
                          '%(date_to)s 23:59:59' and
      sp5.ref is not null
group by pt.name, p.name, p.ref, sp5.ref, tmg.date_start,
         tmg.date_end, sp4.ref, tmp2.date_start,
         tmp2.date_end, sp3.ref, tmr.date_start,
         tmr.date_end, sp2.ref, tmp1.date_start,
         tmp1.date_end, sp1.ref, fs.date_end
         ) as q
) as w
group by w.product_name
order by w.product_name
limit 500
        ''' % {'date_from': brw.date_from,
               'date_to': brw.date_to}
        cr.execute(sql)
        line_ids = []
        for item in cr.dictfetchall():
            line_ids.append(
                (0, 0, {'product_name': item.get('product_name'),
                        'qty': item.get('qty'),
                        'gangsaw_days': item.get('gangsaw_days'),
                        'wait1_days': item.get('wait1_days'),
                        'apom_days': item.get('apom_days'),
                        'wait2_days': item.get('wait2_days'),
                        'resin_days': item.get('resin_days'),
                        'wait3_days': item.get('wait3_days'),
                        'polish_days': item.get('polish_days'),
                        'finish_days': item.get('finish_days'),
                        'util_days': item.get('util_days'),
                        'wait_days': item.get('wait_days'),
                        'total_days': item.get('total_days'),
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

tcv_mrp_days_lapses()


class tcv_mrp_days_lapses_lines(osv.osv_memory):

    _name = 'tcv.mrp.days.lapses.lines'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'line_id': fields.many2one(
            'tcv.mrp.days.lapses', 'Lines', required=True,
            ondelete='cascade'),
        'product_name': fields.char(
            'Product', size=64, required=False, readonly=True,
            help="Fineshed product's name"),
        'qty': fields.integer(
            'Quantity', readonly=True,
            help="Production cicles quantity"),
        'gangsaw_days': fields.float(
            'Gangsawed', digits_compute=dp.get_precision('Account'),
            readonly=False,
            help="Average gangsaw time in days"),
        'wait1_days': fields.float(
            'Wait 1', digits_compute=dp.get_precision('Account'),
            readonly=False,
            help="Average wait time between gangsaw and pumiced in days"),
        'apom_days': fields.float(
            'Pumiced', digits_compute=dp.get_precision('Account'),
            readonly=False,
            help="Average pumiced time in days"),
        'wait2_days': fields.float(
            'Wait 2', digits_compute=dp.get_precision('Account'),
            readonly=False,
            help="Average wait time between pumiced and resin in days"),
        'resin_days': fields.float(
            'Resined', digits_compute=dp.get_precision('Account'),
            readonly=False,
            help="Average resin time in days"),
        'wait3_days': fields.float(
            'Wait 3', digits_compute=dp.get_precision('Account'),
            readonly=False,
            help="Average wait time between resin and polish in days"),
        'polish_days': fields.float(
            'Polished', digits_compute=dp.get_precision('Account'),
            readonly=False,
            help="Average polish time in days"),
        'finish_days': fields.float(
            'Inventoried', digits_compute=dp.get_precision('Account'),
            readonly=False,
            help="Average wait time between polish and inventory in days"),
        'util_days': fields.float(
            'Util days', digits_compute=dp.get_precision('Account'),
            readonly=False,
            help="Average effective time between gangsaw start and " +
            "inventory in days"),
        'wait_days': fields.float(
            'Wait days', digits_compute=dp.get_precision('Account'),
            readonly=False,
            help="Average wait time between gangsaw start and " +
            "inventory in days"),
        'total_days': fields.float(
            'Total days', digits_compute=dp.get_precision('Account'),
            readonly=False,
            help="Average total time between gangsaw start and " +
            "inventory in days"),
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

tcv_mrp_days_lapses_lines()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
