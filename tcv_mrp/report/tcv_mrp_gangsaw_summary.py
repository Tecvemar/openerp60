# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description: Report parser for: tcv_mrp_gangsaw_summary
#
#
##############################################################################
#~ import time
#~ import pooler
from report import report_sxw
from tools.translate import _


def _join_data(report, data, sql):
    report.cr.execute(sql)
    res = report.cr.dictfetchall()
    if data:
        for i in res:
            for k in data:
                if i['id'] == k['id']:
                    k.update(i)
    elif res:
        data.extend(res)
    return data


def _compute_totals(data, keys):
    res = {'name': _('Totals')}
    for key in keys:
        res.update({key: 0})
    for item in data:
        for key in keys:
            if item.get(key):
                res.update({key: res[key] + item[key]})
    return res


def load_gangsaw_sumary1(report, obj):
    date_from = obj.date_from
    date_to = obj.date_to
    res = []
    sql1 = '''
    select t.id, t.name,
           count(b.id) as blocks,
           sum(l.length*l.heigth*l.width) as volume,
           sum(b.slab_qty) as slabs,
           sum(b.net_length*b.net_heigth*b.slab_qty) as area
    from tcv_mrp_gangsaw g
    left join tcv_mrp_gangsaw_blocks b on b.gangsaw_id = g.id
    left join tcv_mrp_subprocess sp on g.parent_id = sp.id
    left join tcv_mrp_template t on sp.template_id = t.id
    left join stock_production_lot l on b.prod_lot_id = l.id
    where g.date_end between '%s 00:00:00' and '%s 23:59:59'
    group by t.id, t.name
    order by t.name
    ''' % (date_from, date_to)
    sql2 = '''
    select t.id, t.name, pc.name as prd,
           sum(s.quantity) as granalla_kg
    from tcv_mrp_gangsaw g
    left join tcv_mrp_gangsaw_supplies s on s.task_id = g.id
    left join tcv_mrp_subprocess sp on g.parent_id = sp.id
    left join tcv_mrp_template t on sp.template_id = t.id
    left join product_template p on s.product_id = p.id
    left join product_category pc on p.categ_id = pc.id
    where g.date_end between '%s 00:00:00' and '%s 23:59:59' and
          p.categ_id in (44)
    group by t.id, t.name, pc.name
    order by t.name
    ''' % (date_from, date_to)
    sql3 = '''
    select t.id, p.float_val,
           sum(b.blade_qty) as blade_qty,
           sum(b.blade_qty*p.float_val) as blade_kg
    from tcv_mrp_gangsaw g
    left join tcv_mrp_gangsaw_blocks b on b.gangsaw_id = g.id
    left join tcv_mrp_subprocess sp on g.parent_id = sp.id
    left join tcv_mrp_template t on sp.template_id = t.id
    left join tcv_mrp_template_param p on p.param_id = t.id and
                                          p.name = 'blade_unit_weight'
    where g.date_end between '%s 00:00:00' and '%s 23:59:59' and
          b.blade_start = 10
    group by t.id, p.float_val
    order by t.id
    ''' % (date_from, date_to)
    res = _join_data(report, res, sql1)
    res = _join_data(report, res, sql2)
    res = _join_data(report, res, sql3)
    total = _compute_totals(
        res, ['blocks', 'volume', 'area', 'slabs', 'granalla_kg',
              'blade_qty', 'blade_kg'])
    res.append(total)
    return res


def load_templates_sumary(report, obj):
    obj_tmp = report.pool.get('tcv.mrp.template')
    tmp_ids = obj_tmp.search(report.cr, report.uid, [])
    res = []
    for temp in obj_tmp.browse(report.cr, report.uid,
                               tmp_ids, context=None):
        obj_task = report.pool.get(temp.res_model.model)
        task_ids, task_count = obj_task.get_task_ids_by_date_range(
            report.cr, report.uid, temp.id, obj.date_from, obj.date_to)
        if task_ids:
            inputs = obj_task.get_task_input_sumary(
                report.cr, report.uid, task_ids)
            outputs = obj_task.get_task_output_sumary(
                report.cr, report.uid, task_ids)
            runtime = obj_task.get_task_runtime_sumary(
                report.cr, report.uid, task_ids)
        else:
            inputs = {}
            outputs = {}
            runtime = {}
        avg_run_time = ((runtime.get('run_time', 0) -
                         runtime.get('down_time', 0)) /
                        task_count) if task_count else 0
        data = {'name': temp.name,
                'res_model': temp.res_model.model,
                'run_time': runtime.get('run_time', 0) -
                runtime.get('down_time', 0),
                'down_time': runtime.get('down_time', 0),
                'count': task_count,
                'avg_run_time': avg_run_time,
                'in_pieces': inputs.get('pieces', 0),
                'in_qty': inputs.get('qty', 0),
                'out_pieces': outputs.get('pieces', 0),
                'out_qty': outputs.get('qty', 0),
                }
        res.append(data)
    return res


def load_process_efec(report, obj):
    obj_tmp = report.pool.get('tcv.mrp.template')
    tmp_ids = obj_tmp.search(report.cr, report.uid, [])
    res = []
    total_m2_finished = 0
    total_m2_process = 0
    count_process = 4
    for temp in obj_tmp.browse(report.cr, report.uid,
                               tmp_ids, context=None):
        obj_task = report.pool.get(temp.res_model.model)
        task_ids, task_count = obj_task.get_task_ids_by_date_range(
            report.cr, report.uid, temp.id, obj.date_from, obj.date_to)
        if task_ids:
            outputs = obj_task.get_task_output_sumary(
                report.cr, report.uid, task_ids)
            if temp.res_model.model != u'tcv.mrp.waste.slab':
                if temp.res_model.model == u'tcv.mrp.finished.slab':
                    total_m2_finished += outputs.get('qty', 0)
                elif temp.res_model.model in (u'tcv.mrp.gangsaw',
                                              u'tcv.mrp.resin',
                                              u'tcv.mrp.polish'):
                    total_m2_process += outputs.get('qty', 0)
    data = {
        'name': _('Total m2 finished / ') +
        _('(Total m2 gangsawed + m2 polished + m2 resined)') +
        _('\n(Good >= 80; Regular < 80 and >= 50; Poor < 50)'),
        'total_m2_finished': total_m2_finished,
        'total_m2_process': total_m2_process,
        'effectiveness': total_m2_process and round(
            ((count_process * total_m2_finished) /
             total_m2_process) * 100, 2) or 0,
        }
    res.append(data)
    return res


def get_gangsaw_efec(report, obj):
    res = []
    waste = report._get_waste_rates(obj)
    process = report._load_process_efec(obj)
    total_m2_finished = process[0].get('total_m2_finished')
    total_m2_gangsawed = waste[0].get('gangsaw_qty')
    data = {
        'name': _('Total m2 finished / m2 gangsawed (Goal >= 80)'),
        'total_m2_finished': total_m2_finished,
        'total_m2_gangsawed': total_m2_gangsawed,
        'effectiveness': round(
            total_m2_finished * 100 /
            total_m2_gangsawed, 2) if total_m2_gangsawed else 0
    }
    res.append(data)
    return res


def get_debris_efec(report, obj):
    res = []
    obj_cfg = report.pool.get('tcv.mrp.config')
    obj_bal = report.pool.get('tcv.liquidity.report.wizard')
    cfg_ids = obj_cfg.search(
        report.cr, report.uid, [('company_id', '=', obj.company_id.id)])
    cfg = obj_cfg.browse(
        report.cr, report.uid, cfg_ids, context=None)[0]
    balance = obj_bal._get_account_balance(
        report.cr, report.uid,
        cfg.debris_account_id.id, '<=', obj.date_to, True, context=None)
    process = report._load_process_efec(obj)
    total_m2_finished = process[0].get('total_m2_finished')
    data = {
        'name': _('Total amount for debris / total m2 finished'),
        'balance': balance,
        'total_m2_finished': total_m2_finished,
        'effectiveness': round(
            balance / total_m2_finished, 2) if total_m2_finished else 0
    }
    res.append(data)
    return res


def load_material_sumary(report, obj):
    date_from = obj.date_from
    date_to = obj.date_to

    res = []
    sql1 = '''
    select b.product_id, p.name,
           count(b.id) as blocks,
           sum(l.length*l.heigth*l.width) as volume,
           sum(b.slab_qty) as slabs,
           sum(b.net_length*b.net_heigth*b.slab_qty) as area
    from tcv_mrp_gangsaw g
    left join tcv_mrp_gangsaw_blocks b on b.gangsaw_id = g.id
    left join tcv_mrp_subprocess sp on g.parent_id = sp.id
    left join tcv_mrp_template t on sp.template_id = t.id
    left join stock_production_lot l on b.prod_lot_id = l.id
    left join product_template p on b.product_id = p.id
    where g.date_end between '%s 00:00:00' and '%s 23:59:59'
    group by b.product_id, p.name
    order by p.name
    ''' % (date_from, date_to)
    res = _join_data(report, res, sql1)
    total = _compute_totals(res, ['blocks', 'volume', 'area', 'slabs'])
    res.append(total)
    return res


class parser_tcv_mrp_gangsaw_summary(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        if context is None:
            context = {}
        super(parser_tcv_mrp_gangsaw_summary, self).\
            __init__(cr, uid, name, context=context)
        self.localcontext.update({
            'get_gangsaw_sumary1': self._get_gangsaw_sumary1,
            'get_waste_rates': self._get_waste_rates,
            'get_templates_sumary': self._get_templates_sumary,
            'get_material_sumary': self._get_material_sumary,
            'load_process_efec': self._load_process_efec,
            'get_gangsaw_efec': self._get_gangsaw_efec,
            'get_debris_efec': self._get_debris_efec,
            })
        self.context = context

    def _get_gangsaw_sumary1(self, obj):
        return load_gangsaw_sumary1(self, obj)

    def _get_templates_sumary(self, obj):
        return load_templates_sumary(self, obj)

    def _get_material_sumary(self, obj):
        return load_material_sumary(self, obj)

    def _get_waste_rates(self, obj):
        params = {
            'date_from': obj.date_from,
            'date_to': obj.date_to}
        res = []
        sql = '''
        select q.code, pt.name, sum(area) as gangsaw_qty,
               sum(waste) as waste_qty from (
            select substring(pp.default_code, 1,6) || 'PROC' as code,
                   sum(b.net_length*b.net_heigth*b.slab_qty) as area,
                   0 as waste
            from tcv_mrp_gangsaw g
            left join tcv_mrp_gangsaw_blocks b on b.gangsaw_id = g.id
            left join stock_production_lot l on b.prod_lot_id = l.id
            left join product_product pp on l.product_id = pp.id
            where g.date_end between '%(date_from)s 00:00:00' and
                                     '%(date_to)s 23:59:59'
            group by pp.default_code
            union
            select substring(pp.default_code, 1,6) || 'PROC' as code,
                   0 as area, sum(io.length*io.heigth*w.pieces) as waste
            from tcv_mrp_waste_slab_inputs w
            left join tcv_mrp_io_slab io on w.output_id = io.id
            left join product_product pp on io.product_id = pp.id
            left join tcv_mrp_waste_slab ws on w.task_id = ws.id
            where ws.date_end between '%(date_from)s 00:00:00' and
                                      '%(date_to)s 23:59:59'
            group by pp.default_code) as q
        left join product_product pp on q.code = pp.default_code
        left join product_template pt on pp.id = pt.id
        group by q.code, pt.name
        order by q.code, pt.name
        ''' % (params)
        res = []
        total = {
            'name': _('Total m2 waste / total m2 gangsawed'),
            'gangsaw_qty': 0,
            'waste_qty': 0,
            }
        self.cr.execute(sql)
        for row in self.cr.dictfetchall():
            total['gangsaw_qty'] += row['gangsaw_qty']
            total['waste_qty'] += row['waste_qty']
        res.append(total)
        return res

    def _load_process_efec(self, obj):
        return load_process_efec(self, obj)

    def _get_gangsaw_efec(self, obj):
        return get_gangsaw_efec(self, obj)

    def _get_debris_efec(self, obj):
        return get_debris_efec(self, obj)


report_sxw.report_sxw('report.tcv.mrp.gangsaw.summary.report',
                      'tcv.mrp.gangsaw.summary.wizard',
                      'addons/tcv_mrp/report/tcv_mrp_gangsaw_summary.rml',
                      parser=parser_tcv_mrp_gangsaw_summary,
                      header=False
                      )
