# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description: Report parser for: tcv_mrp_supplies_by_product
#
#
##############################################################################
#~ import time
#~ import pooler
from report import report_sxw
#~ from tools.translate import _


class parser_tcv_mrp_supplies_by_product(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        if context is None:
            context = {}
        super(parser_tcv_mrp_supplies_by_product, self).\
            __init__(cr, uid, name, context=context)
        self.localcontext.update({
            'get_report_groups': self._get_report_groups,
            'get_groups_lines': self._get_groups_lines,
            'get_groups_total': self._get_groups_total,
            })
        self.context = context

    def _get_report_groups(self, obj):
        date_from = obj.date_from
        date_to = obj.date_to
        sql = '''
        select distinct p.name as supplie
        from tcv_mrp_gangsaw g
        left join tcv_mrp_gangsaw_supplies s on s.task_id = g.id
        left join product_template p on s.product_id = p.id
        where g.date_end between '%s 00:00:00' and '%s 23:59:59'
        order by p.name
        ''' % (date_from, date_to)
        self.cr.execute(sql)
        return self.cr.dictfetchall()

    def _get_groups_lines(self, obj, grp):
        date_from = obj.date_from
        date_to = obj.date_to
        sql = '''
select supplie, name, count(name) as item_count,
       round(avg(yield), 3) as avg_yield,
       round(avg(yield) - stddev_samp(yield), 3) as min_yield,
       round(avg(yield) + stddev_samp(yield), 3) as max_yield,
        min(yield) as minimun, max(yield) as maximun
from (
    select product_id, name, supplie, area, vol, total_vol,
           round(vol/total_vol, 3) as sup_pct, quantity,
           round(quantity*round(vol/total_vol, 3),4) as used_qty,
           round((quantity*round(vol/total_vol, 3))/area,3) as yield
    from (
        select b.product_id, p.name,
               round((b.net_length*b.net_heigth*b.slab_qty),4) as area,
               round((length*heigth*width),4) as vol,
               tb.total_vol,
               p2.name as supplie,
               s.quantity
        from tcv_mrp_gangsaw g
        left join tcv_mrp_gangsaw_blocks b on b.gangsaw_id = g.id
        left join tcv_mrp_subprocess sp on g.parent_id = sp.id
        left join tcv_mrp_template t on sp.template_id = t.id
        left join stock_production_lot l on b.prod_lot_id = l.id
        left join product_template p on b.product_id = p.id
        left join tcv_mrp_gangsaw_supplies s on g.id = s.task_id
        left join product_template p2 on s.product_id = p2.id
        left join (
            select gangsaw_id,
               round(sum(length*heigth*width),4) as total_vol
            from tcv_mrp_gangsaw_blocks
            left join stock_production_lot spl on prod_lot_id = spl.id
            where gangsaw_id=tcv_mrp_gangsaw_blocks.gangsaw_id
            group by gangsaw_id) tb on tb.gangsaw_id = b.gangsaw_id
        where g.date_end between '%s 00:00:00' and '%s 23:59:59'
        ) as q1
    ) as q2 where supplie='%s'
group by supplie, name
order by supplie, name
        ''' % (date_from, date_to, grp)
        self.cr.execute(sql)
        return self.cr.dictfetchall()

    def _get_groups_total(self, obj, grp):
        date_from = obj.date_from
        date_to = obj.date_to
        sql = '''
select supplie, '' as name, count(supplie) as item_count,
       round(avg(yield), 3) as avg_yield,
       round(avg(yield) - stddev_samp(yield), 3) as min_yield,
       round(avg(yield) + stddev_samp(yield), 3) as max_yield,
        min(yield) as minimun, max(yield) as maximun
from (
    select product_id, name, supplie, area, vol, total_vol,
           round(vol/total_vol, 3) as sup_pct, quantity,
           round(quantity*round(vol/total_vol, 3),4) as used_qty,
           round((quantity*round(vol/total_vol, 3))/area,3) as yield
    from (
        select b.product_id, p.name,
               round((b.net_length*b.net_heigth*b.slab_qty),4) as area,
               round((length*heigth*width),4) as vol,
               tb.total_vol,
               p2.name as supplie,
               s.quantity
        from tcv_mrp_gangsaw g
        left join tcv_mrp_gangsaw_blocks b on b.gangsaw_id = g.id
        left join tcv_mrp_subprocess sp on g.parent_id = sp.id
        left join tcv_mrp_template t on sp.template_id = t.id
        left join stock_production_lot l on b.prod_lot_id = l.id
        left join product_template p on b.product_id = p.id
        left join tcv_mrp_gangsaw_supplies s on g.id = s.task_id
        left join product_template p2 on s.product_id = p2.id
        left join (
            select gangsaw_id,
               round(sum(length*heigth*width),4) as total_vol
            from tcv_mrp_gangsaw_blocks
            left join stock_production_lot spl on prod_lot_id = spl.id
            where gangsaw_id=tcv_mrp_gangsaw_blocks.gangsaw_id
            group by gangsaw_id) tb on tb.gangsaw_id = b.gangsaw_id
        where g.date_end between '%s 00:00:00' and '%s 23:59:59'
        ) as q1
    ) as q2 where supplie='%s'
group by supplie
order by supplie
        ''' % (date_from, date_to, grp)
        self.cr.execute(sql)
        return self.cr.dictfetchall()

report_sxw.report_sxw('report.tcv.mrp.supplies.by.product.report',
                      'tcv.mrp.supplies.by.product.wizard',
                      'addons/tcv_mrp/report/tcv_mrp_supplies_by_product.rml',
                      parser=parser_tcv_mrp_supplies_by_product,
                      header=False
                      )
