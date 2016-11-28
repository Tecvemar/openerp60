# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description: Report parser for: tcv_production_rates
#
#
##############################################################################
#~ import time
#~ import pooler
from report import report_sxw
from tools.translate import _
from osv import fields, osv
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
#~ import tcv_mrp_gangsaw_summary
import numpy as np


##------------------------------------------------- tcv_production_rates_wizard


class tcv_production_rates_wizard(osv.osv_memory):

    _name = 'tcv.production.rates.wizard'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def default_get(self, cr, uid, fields, context=None):
        data = super(tcv_production_rates_wizard, self).\
            default_get(cr, uid, fields, context)
        bas_date = datetime.strptime(
            time.strftime('%Y-%m-01'), '%Y-%m-%d')
        str_date = bas_date + relativedelta(years=-1)
        end_date = bas_date + relativedelta(days=-1)
        data.update({'date_from': str_date.strftime('%Y-%m-%d'),
                     'date_to': end_date.strftime('%Y-%m-%d')})
        return data

    ##--------------------------------------------------------- function fields

    _columns = {
        'name': fields.char('Name', size=64, required=False, readonly=False),
        'date_from': fields.date('Date from', required=True),
        'date_to': fields.date('Date to', required=True),
        'company_id': fields.many2one('res.company', 'Company', required=True,
                                      readonly=True, ondelete='restrict'),
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

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_production_rates_wizard()


class parser_tcv_production_rates(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        context = context or {}
        super(parser_tcv_production_rates, self).\
            __init__(cr, uid, name, context=context)
        self.localcontext.update({
            'get_gangsaw_rates': self._get_gangsaw_rates,
            'get_material_rates': self._get_material_rates,
            'get_waste_rates': self._get_waste_rates,
            })
        self.context = context

    #~ def _get_gangsaw_rates(self, obj):
        #~ res = tcv_mrp_gangsaw_summary.load_gangsaw_sumary1(self, obj)[-1:]
        #~ res[0].update({'name': _('Gangsaw rates')})
        #~ return res

    def _get_gangsaw_rates(self, obj):
        date_from = obj.date_from
        date_to = obj.date_to
        params = {'date_from': date_from, 'date_to': date_to}
        res = []
        sql = '''
        select avg(area) as avg_area from (
            select g.id,
                   sum(b.net_length*b.net_heigth*b.slab_qty) as area
            from tcv_mrp_gangsaw g
            left join tcv_mrp_gangsaw_blocks b on b.gangsaw_id = g.id
            left join tcv_mrp_subprocess sp on g.parent_id = sp.id
            left join tcv_mrp_template t on sp.template_id = t.id
            left join stock_production_lot l on b.prod_lot_id = l.id
            left join product_template p on b.product_id = p.id
            where g.date_end between '%(date_from)s 00:00:00' and
                                     '%(date_to)s 23:59:59'
            group by g.id) as a
        ''' % (params)
        self.cr.execute(sql)
        data = {}
        for row in self.cr.dictfetchall():
            avg_area = row['avg_area']
        sql = '''
        select pc.name as name, s.quantity as quantity
        from tcv_mrp_gangsaw g
        left join tcv_mrp_gangsaw_supplies s on s.task_id = g.id
        left join tcv_mrp_subprocess sp on g.parent_id = sp.id
        left join tcv_mrp_template t on sp.template_id = t.id
        left join product_template p on s.product_id = p.id
        left join product_category pc on p.categ_id = pc.id
        where g.date_end between '%(date_from)s 00:00:00' and
                                 '%(date_to)s 23:59:59'                         and s.quantity > 500
        union
        select 'GANGSAW BLADES' as name,
               b.blade_qty * p.float_val as quantity
        from tcv_mrp_gangsaw g
        left join tcv_mrp_gangsaw_blocks b on b.gangsaw_id = g.id
        left join tcv_mrp_subprocess sp on g.parent_id = sp.id
        left join tcv_mrp_template t on sp.template_id = t.id
        left join tcv_mrp_template_param p on p.param_id = t.id and
                                              p.name = 'blade_unit_weight'
        where g.date_end between '%(date_from)s 00:00:00' and
                                 '%(date_to)s 23:59:59' and
              b.blade_start = 10
        order by 1
        ''' % (params)
        self.cr.execute(sql)
        act_name = False
        data = {}
        for row in self.cr.dictfetchall():
            if act_name != row['name']:
                if act_name:
                    res.append(data)
                act_name = row['name']
                data = {'name': act_name, 'values': []}
            data['values'].append(row['quantity'])
        res.append(data)
        for item in res:
            avg_key = np.mean(item['values'])  # Average
            std_key = np.std(item['values'])  # standart deviation
            item.update({
                'min_value': avg_key - std_key,
                'max_value': avg_key + std_key,
                'min_yield': (avg_key - std_key) / avg_area,
                'max_yield': (avg_key + std_key) / avg_area,
                })
        return res

    #~ def _get_material_rates(self, obj):
        #~ '''Deprecated'''
        #~ res = tcv_mrp_gangsaw_summary.load_material_sumary(self, obj)
        #~ return res

    def _get_material_rates(self, obj):
        date_from = obj.date_from
        date_to = obj.date_to

        res = []
        sql = '''
        select b.product_id, p.name,
               l.length*l.heigth*l.width as volume,
               b.net_length*b.net_heigth*b.slab_qty as area
        from tcv_mrp_gangsaw g
        left join tcv_mrp_gangsaw_blocks b on b.gangsaw_id = g.id
        left join tcv_mrp_subprocess sp on g.parent_id = sp.id
        left join tcv_mrp_template t on sp.template_id = t.id
        left join stock_production_lot l on b.prod_lot_id = l.id
        left join product_template p on b.product_id = p.id
        where g.date_end between '%s 00:00:00' and '%s 23:59:59'
        order by p.name
        ''' % (date_from, date_to)
        self.cr.execute(sql)
        act_name = False
        avg_data = {}
        data = {}
        for row in self.cr.dictfetchall():
            if act_name != row['name']:
                if act_name:
                    res.append(data)
                act_name = row['name']
                data = {'name': act_name, 'volumes': [], 'yields': []}
            bl_yield = row['area'] / row['volume']
            data['volumes'].append(row['volume'])
            data['yields'].append(bl_yield)
        if act_name:
            res.append(data)
        avg_data = {'name': _('Average'), 'volumes': [], 'yields': []}
        for lin in res:
            avg_data['volumes'].extend(lin['volumes'])
            avg_data['yields'].extend(lin['yields'])
        res.append(avg_data)
        for item in res:
            vol_avg = np.mean(item['volumes'])  # Average
            vol_std = np.std(item['volumes'])  # standart deviation
            yield_avg = np.mean(item['yields'])  # Average
            yield_std = np.std(item['yields'])  # standart deviation
            item.update({
                'min_vol': vol_avg - vol_std,
                'max_vol': vol_avg + vol_std,
                'min_yield': yield_avg - yield_std,
                'max_yield': yield_avg + yield_std,
                })
        return res

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
            'name': _('Total waste in process'),
            'gangsaw_qty': 0,
            'waste_qty': 0,
            }
        self.cr.execute(sql)
        for row in self.cr.dictfetchall():
            #~ res.append({
                #~ 'name': ' '.join((row.get('name') or
                                 #~ (row['code'] + ' a b')).split()[:-2]),
                #~ 'gangsaw_qty': row['gangsaw_qty'],
                #~ 'waste_qty': row['waste_qty']})
            total['gangsaw_qty'] += row['gangsaw_qty']
            total['waste_qty'] += row['waste_qty']
        res.append(total)
        return res

report_sxw.report_sxw('report.tcv.production.rates.report',
                      'tcv.production.rates.wizard',
                      'addons/tcv_mrp/report/tcv_production_rates.rml',
                      parser=parser_tcv_production_rates,
                      header=False
                      )
