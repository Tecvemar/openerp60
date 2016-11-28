# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description: Report parser for: tcv_mrp_blade_yield
#
#
##############################################################################
#~ import time
#~ import pooler
from report import report_sxw
#~ from tools.translate import _


class parser_tcv_mrp_blade_yield(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        if context is None:
            context = {}
        super(parser_tcv_mrp_blade_yield, self).\
            __init__(cr, uid, name, context=context)
        self.localcontext.update({
            'get_lines': self._get_lines,
            })
        self.context = context

    def _get_lines(self, obj):
        date_from = obj.date_from
        date_to = obj.date_to
        sql = '''
select name, hardness, count(name) as item_count,
       round(avg(net_heigth), 3) as net_heigth,
       round(cast(avg(blade_heigth) as numeric), 3) as blade_heigth,
       round(cast(avg(blade_yield) as numeric), 3) as blade_yield,
       round(cast(avg(blade_yield) - stddev_samp(blade_yield) as numeric), 3)
           as min_yield,
       round(cast(avg(blade_yield) + stddev_samp(blade_yield) as numeric), 3)
           as max_yield
from (
    select pt.name, pp.hardness, b.net_heigth,
           (b.blade_start - b.blade_end) * 1.0 as blade_heigth,
           (b.blade_start - b.blade_end) - b.net_heigth as blade_yield
    from tcv_mrp_gangsaw g
    left join tcv_mrp_gangsaw_blocks b on b.gangsaw_id = g.id
    left join product_product pp on b.product_id = pp.id
    left join product_template pt on b.product_id = pt.id
    where g.date_end between '%s 00:00:00' and '%s 23:59:59'
    ) as q
group by name, hardness
order by 1
        ''' % (date_from, date_to)
        self.cr.execute(sql)
        return self.cr.dictfetchall()

report_sxw.report_sxw('report.tcv.mrp.blade.yield.report',
                      'tcv.mrp.blade.yield.wizard',
                      'addons/tcv_mrp/report/tcv_mrp_blade_yield.rml',
                      parser=parser_tcv_mrp_blade_yield,
                      header=False
                      )
