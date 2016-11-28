# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description: Report parser for: tcv_mrp_anual_report
#
#
##############################################################################
#~ import time
#~ import pooler
from report import report_sxw
from tools.translate import _
from osv import fields, osv


__TCV_MRP_ANUAL_REPORT_TYPES__ = [
    (10, _('Area proceced by Subprocess (m2)')),
    (20, _('Gangsaw by product (m2)')),
    (25, _('Gangsaw by hardness (m2)')),
    (30, _('Finished slabs by product (m2)')),
    (35, _('Finished slabs by hardness (m2)')),
    (40, _('Stop issues by month (hrs)')),
    (50, _('Production supplies')),
    (60, _('Production vs waste')),
    (70, _('Waste by origin process')),
    ]


##-------------------------------------------------------- tcv_mrp_anual_report


class tcv_mrp_anual_report(osv.osv_memory):

    _inherit = 'tcv.monthly.report'

    _name = 'tcv.mrp.anual.report'

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def default_get(self, cr, uid, fields, context=None):
        data = super(tcv_mrp_anual_report, self).default_get(
            cr, uid, fields, context)
        data.update({
            'name': _('Annual Summary of processes'),
            })
        return data

    def _get_pct_type(self, type):
        res = super(tcv_mrp_anual_report, self)._get_pct_type(type)
        return res

    def _area_proceced_by_subprocess_m2(self, cr, uid, ids, params, context):
        lines_ord = []
        sql = "select sequence, name from tcv_mrp_template order by sequence"
        cr.execute(sql)
        for row in cr.fetchall():
            lines_ord.append(row[1])
        sql = """
        select extract(year from g.date_end) AS year,
               extract(month from g.date_end) AS month,
               t.sequence, t.name,
               sum(pieces*heigth*length) as area
        from tcv_mrp_gangsaw g
        left join tcv_mrp_gangsaw_output b on b.gangsaw_id = g.id
        left join tcv_mrp_subprocess sp on g.parent_id = sp.id
        left join tcv_mrp_template t on sp.template_id = t.id
        where g.date_end between '%(date_start)s 00:00:00' and
            '%(date_end)s 23:59:59'
        group by year, month, t.sequence, t.name
        union
        select extract(year from p.date_end) as year,
               extract(month from p.date_end) AS month,
               t.sequence, t.name, sum(pieces*heigth*length) as area
        from tcv_mrp_polish_output o
        left join tcv_mrp_polish p on o.task_id = p.id
        left join tcv_mrp_subprocess sp on p.parent_id = sp.id
        left join tcv_mrp_template t on sp.template_id = t.id
        where p.date_end between '%(date_start)s 00:00:00' and
            '%(date_end)s 23:59:59'
        group by year, month, t.sequence, t.name
        union
        select extract(year from p.date_end) as year,
               extract(month from p.date_end) AS month,
               t.sequence, t.name, sum(pieces*heigth*length) as area
        from tcv_mrp_resin_output o
        left join tcv_mrp_resin p on o.task_id = p.id
        left join tcv_mrp_subprocess sp on p.parent_id = sp.id
        left join tcv_mrp_template t on sp.template_id = t.id
        where p.date_end between '%(date_start)s 00:00:00' and
            '%(date_end)s 23:59:59'
        group by year, month, t.sequence, t.name
        union
        select extract(year from p.date_end) as year,
               extract(month from p.date_end) AS month,
               t.sequence, t.name, sum(pieces*heigth*length) as area
        from tcv_mrp_finished_slab_output o
        left join tcv_mrp_finished_slab p on o.task_id = p.id
        left join tcv_mrp_subprocess sp on p.parent_id = sp.id
        left join tcv_mrp_template t on sp.template_id = t.id
        where p.date_end between '%(date_start)s 00:00:00' and
            '%(date_end)s 23:59:59'
        group by year, month, t.sequence, t.name
        union
        select extract(year from p.date_end) as year,
               extract(month from p.date_end) AS month,
               t.sequence, t.name, sum(o.pieces*heigth*length) as area
        from tcv_mrp_waste_slab_inputs o
        left join tcv_mrp_io_slab s on o.output_id = s.id
        left join tcv_mrp_waste_slab p on o.task_id = p.id
        left join tcv_mrp_subprocess sp on p.parent_id = sp.id
        left join tcv_mrp_template t on sp.template_id = t.id
        where p.date_end between '%(date_start)s 00:00:00' and
            '%(date_end)s 23:59:59'
        group by year, month, t.sequence, t.name
        order by 1,2,3
        """ % params
        cr.execute(sql)
        data = cr.fetchall()
        return lines_ord, data

    def _get_gangsaw_by_product_m2(self, cr, uid, ids, params, context):
        lines_ord = []
        sql = """
        select distinct p.default_code, pt.name
        from tcv_mrp_gangsaw g
        left join tcv_mrp_gangsaw_blocks b on b.gangsaw_id = g.id
        left join product_product p on b.product_id = p.id
        left join product_template pt on b.product_id = pt.id
        where g.date_end between '%(date_start)s 00:00:00' and
            '%(date_end)s 23:59:59'
        order by 1,2
        """ % params
        cr.execute(sql)
        for row in cr.fetchall():
            lines_ord.append(row[1])
        sql = """
        select extract(year from g.date_end) AS year,
               extract(month from g.date_end) AS month,
               p.default_code, pt.name,
               sum(b.net_length*b.net_heigth*b.slab_qty) as area
        from tcv_mrp_gangsaw g
        left join tcv_mrp_gangsaw_blocks b on b.gangsaw_id = g.id
        left join product_product p on b.product_id = p.id
        left join product_template pt on b.product_id = pt.id
        left join tcv_mrp_subprocess sp on g.parent_id = sp.id
        left join tcv_mrp_template t on sp.template_id = t.id
        where g.date_end between '%(date_start)s 00:00:00' and
            '%(date_end)s 23:59:59'
        group by year, month, p.default_code, pt.name
        order by 1,2,3
        """ % params
        cr.execute(sql)
        data = cr.fetchall()
        return lines_ord, data

    def _get_gangsaw_by_hardness_m2(self, cr, uid, ids, params, context):
        lines_ord = ['Soft', 'Soft-Medium', 'Medium', 'Medium-Hard', 'Hard']
        sql = """
        select extract(year from g.date_end) AS year,
               extract(month from g.date_end) AS month,
               p.hardness as default_code,
               case p.hardness
                   when 1 then 'Soft'
                   when 2 then 'Soft-Medium'
                   when 3 then 'Medium'
                   when 4 then 'Medium-Hard'
                   when 5 then 'Hard'
                   else '-' end as name,
               sum(b.net_length*b.net_heigth*b.slab_qty) as area
        from tcv_mrp_gangsaw g
        left join tcv_mrp_gangsaw_blocks b on b.gangsaw_id = g.id
        left join product_product p on b.product_id = p.id
        left join product_template pt on b.product_id = pt.id
        left join tcv_mrp_subprocess sp on g.parent_id = sp.id
        left join tcv_mrp_template t on sp.template_id = t.id
        where g.date_end between '%(date_start)s 00:00:00' and
            '%(date_end)s 23:59:59'
        group by year, month, p.hardness
        order by 1,2,3
        """ % params
        cr.execute(sql)
        data = cr.fetchall()
        return lines_ord, data

    def _get_finished_slabs_by_product_m2(self, cr, uid, ids, params, context):
        lines_ord = []
        sql = """
        select distinct p.default_code, pt.name
        from tcv_mrp_finished_slab s
        left join tcv_mrp_finished_slab_output o on o.task_id = s.id
        left join product_product p on o.product_id = p.id
        left join product_template pt on o.product_id = pt.id
        where s.date_end between '%(date_start)s 00:00:00' and
            '%(date_end)s 23:59:59'
        order by 1,2
        """ % params
        cr.execute(sql)
        for row in cr.fetchall():
            lines_ord.append(row[1])
        sql = """
        select extract(year from s.date_end) as year,
               extract(month from s.date_end) AS month,
               p.default_code, pt.name, sum(pieces*heigth*length) as area
        from tcv_mrp_finished_slab_output o
        left join tcv_mrp_finished_slab s on o.task_id = s.id
        left join tcv_mrp_subprocess sp on s.parent_id = sp.id
        left join tcv_mrp_template t on sp.template_id = t.id
        left join product_product p on o.product_id = p.id
        left join product_template pt on o.product_id = pt.id
        where s.date_end between '%(date_start)s 00:00:00' and
            '%(date_end)s 23:59:59'
        group by year, month, p.default_code, pt.name
        order by 1, 2
        """ % params
        cr.execute(sql)
        data = cr.fetchall()
        return lines_ord, data

    def _get_finished_slabs_by_hardness_m2(self, cr, uid, ids, params,
                                           context):
        lines_ord = ['Soft', 'Soft-Medium', 'Medium', 'Medium-Hard', 'Hard']
        sql = """
        select extract(year from s.date_end) as year,
               extract(month from s.date_end) AS month,
               p.hardness as default_code,
               case p.hardness
                   when 1 then 'Soft'
                   when 2 then 'Soft-Medium'
                   when 3 then 'Medium'
                   when 4 then 'Medium-Hard'
                   when 5 then 'Hard'
                   else '-' end as name,
               sum(pieces*heigth*length) as area
        from tcv_mrp_finished_slab_output o
        left join tcv_mrp_finished_slab s on o.task_id = s.id
        left join tcv_mrp_subprocess sp on s.parent_id = sp.id
        left join tcv_mrp_template t on sp.template_id = t.id
        left join product_product p on o.product_id = p.id
        left join product_template pt on o.product_id = pt.id
        where s.date_end between '%(date_start)s 00:00:00' and
            '%(date_end)s 23:59:59'
        group by year, month, p.hardness
        order by 1, 2
        """ % params
        cr.execute(sql)
        data = cr.fetchall()
        return lines_ord, data

    def _get_stop_issues_by_month_hrs(self, cr, uid, ids, params, context):
        lines_ord = []
        sql = """
        select code, name from tcv_mrp_stops_issues
        order by code
        """ % params
        cr.execute(sql)
        for row in cr.fetchall():
            lines_ord.append(row[1])
        sql = """
        select extract(year from s.stop_end) as year,
               extract(month from s.stop_end) AS month,
               i.code, i.name,
               EXTRACT(epoch FROM sum(stop_end-stop_start))/3600 as stop_time
        from tcv_mrp_gangsaw_stops s
        left join tcv_mrp_stops_issues i on s.stop_issue_id = i.id
        where s.stop_end between '%(date_start)s 00:00:00' and
            '%(date_end)s 23:59:59'
        group by year, month, i.code, i.name
        order by 1, 2
        """ % params
        cr.execute(sql)
        data = cr.fetchall()
        return lines_ord, data

    def _get_production_supplies(self, cr, uid, ids, params, context):
        lines_ord = []
        sql = """
        select distinct p.default_code || ' ' || tp2.char_val as code,
               pt.name || ' - ' || tp2.char_val as name
        from tcv_mrp_gangsaw g
        left join tcv_mrp_gangsaw_supplies b on b.task_id = g.id
        left join product_product p on b.product_id = p.id
        left join product_template pt on b.product_id = pt.id
        left join tcv_mrp_subprocess sp on g.parent_id = sp.id
        left join tcv_mrp_template_param tp2 on sp.template_id = tp2.param_id
             and tp2.name = 'ref_name'
        where g.date_end between '%(date_start)s 00:00:00' and
            '%(date_end)s 23:59:59'
        union
        select tp.char_val, pt.name
        from tcv_mrp_template_param tp
        left join product_product p on tp.char_val = p.default_code
        left join product_template pt on p.id = pt.id
        where tp.name = 'default_blade_product'
        order by 1,2
        """ % params
        cr.execute(sql)
        for row in cr.fetchall():
            lines_ord.append(row[1])
        sql = """
        select extract(year from g.date_end) AS year,
               extract(month from g.date_end) AS month,
               p.default_code || ' ' || tp2.char_val as code,
               pt.name || ' - ' || tp2.char_val as name,
               sum(s.quantity) as quantity
        from tcv_mrp_gangsaw g
        left join tcv_mrp_gangsaw_supplies s on s.task_id = g.id
        left join product_product p on s.product_id = p.id
        left join product_template pt on s.product_id = pt.id
        left join tcv_mrp_subprocess sp on g.parent_id = sp.id
        left join tcv_mrp_template t on sp.template_id = t.id
        left join tcv_mrp_template_param tp2 on sp.template_id = tp2.param_id
             and tp2.name = 'ref_name'
        where g.date_end between '%(date_start)s 00:00:00' and
            '%(date_end)s 23:59:59'
        group by year, month, p.default_code, pt.name, tp2.char_val
        union
        select extract(year from g.date_end) AS year,
               extract(month from g.date_end) AS month,
               p.default_code, pt.name,
               sum(b.blade_qty*tp.float_val) as area
        from tcv_mrp_gangsaw g
        left join tcv_mrp_gangsaw_blocks b on b.gangsaw_id = g.id
        left join product_product p on b.blade_id = p.id
        left join product_template pt on b.blade_id = pt.id
        left join tcv_mrp_subprocess sp on g.parent_id = sp.id
        left join tcv_mrp_template t on sp.template_id = t.id
        left join tcv_mrp_template_param tp on t.id = tp.param_id and
                                               tp.name = 'blade_unit_weight'
        where g.date_end between '%(date_start)s 00:00:00' and
            '%(date_end)s 23:59:59' and b.blade_start = 10
        group by year, month, p.default_code, pt.name
        order by 1,2,3
        """ % params
        cr.execute(sql)
        data = cr.fetchall()
        return lines_ord, data

    def _get_production_vs_waste(self, cr, uid, ids, params, context):
        lines_ord = ['Total aserrado (m2)', 'Total merma (m2)',
                     'Merma / Aserrado (%)']
        sql = """
        select distinct 4 as sequence, 'Merma (m2) ' || pt.name as name
        from tcv_mrp_waste_slab_inputs w
        left join tcv_mrp_io_slab io on w.output_id = io.id
        left join product_template pt on io.product_id = pt.id
        left join tcv_mrp_waste_slab ws on w.task_id = ws.id
        where ws.date_end between '%(date_start)s 00:00:00' and
                                  '%(date_end)s 23:59:59'
        group by pt.name
        order by 2
        """ % params
        cr.execute(sql)
        for row in cr.fetchall():
            lines_ord.append(row[1])

        sql = """
        select extract(year from g.date_end) AS year,
               extract(month from g.date_end) AS month,
                1 as sequence, 'Total aserrado (m2)' as name,
               sum(b.net_length*b.net_heigth*b.slab_qty) as area
        from tcv_mrp_gangsaw g
        left join tcv_mrp_gangsaw_blocks b on b.gangsaw_id = g.id
        left join tcv_mrp_subprocess sp on g.parent_id = sp.id
        left join tcv_mrp_template t on sp.template_id = t.id
        where g.date_end between '%(date_start)s 00:00:00' and
                                 '%(date_end)s 23:59:59'
        group by year, month
        union
        select extract(year from p.date_end) as year,
               extract(month from p.date_end) AS month,
               2 as sequence, 'Total merma (m2)' as name,
               sum(o.pieces*heigth*length) as area
        from tcv_mrp_waste_slab_inputs o
        left join tcv_mrp_io_slab s on o.output_id = s.id
        left join tcv_mrp_waste_slab p on o.task_id = p.id
        left join tcv_mrp_subprocess sp on p.parent_id = sp.id
        left join tcv_mrp_template t on sp.template_id = t.id
        where p.date_end between '%(date_start)s 00:00:00' and
                                 '%(date_end)s 23:59:59'
        group by year, month
        union
        select extract(year from ws.date_end) as year,
               extract(month from ws.date_end) AS month,
               4 as sequence,
               'Merma (m2) ' || pt.name as name,
               sum(io.length*io.heigth*w.pieces) as area
        from tcv_mrp_waste_slab_inputs w
        left join tcv_mrp_io_slab io on w.output_id = io.id
        left join product_template pt on io.product_id = pt.id
        left join tcv_mrp_waste_slab ws on w.task_id = ws.id
        where ws.date_end between '%(date_start)s 00:00:00' and
                                  '%(date_end)s 23:59:59'
        group by year, month, pt.name
        order by 1,2,3
        """ % params
        cr.execute(sql)
        data = cr.fetchall()
        #~ Now compute and add (waste / gangsaw)
        gangsaw = {}
        waste = {}
        periods = []
        for item in data:
            period = int(item[0] * 100 + item[1])
            periods.append(period)
            if item[3] == lines_ord[0]:
                gangsaw[period] = item[4]
            elif item[3] == lines_ord[1]:
                waste[period] = item[4]
        for period in periods:
            values = (
                period // 100, period % 100, 3, lines_ord[2],
                round((waste[period] / gangsaw[period]) * 100, 2) if
                gangsaw.get(period) else 0
                )
            data.append(values)
        return lines_ord, data

    def _get_waste_by_origin_process(self, cr, uid, ids, params, context):
        lines_ord = []
        sql = """
        select sequence, name from tcv_mrp_template order by sequence
        """ % params
        cr.execute(sql)
        for row in cr.fetchall():
            lines_ord.append(row[1])
        sql = """
        select extract(year from ws.date_end) as year,
           extract(month from ws.date_end) AS month,
           t.sequence as sequence,
           t.name as name,
           sum(io.length*io.heigth*w.pieces) as area
        from tcv_mrp_waste_slab_inputs w
        left join tcv_mrp_io_slab io on w.output_id = io.id
        left join tcv_mrp_waste_slab ws on w.task_id = ws.id
        left join tcv_mrp_subprocess s on ws.parent_id = s.id
        left join tcv_mrp_subprocess ps on s.prior_id = ps.id
        left join tcv_mrp_template t on ps.template_id = t.id
        where ws.date_end between '%(date_start)s 00:00:00' and
                                  '%(date_end)s 23:59:59'
        group by year, month, t.name, t.sequence
        order by 1,2,3
        """ % params
        cr.execute(sql)
        data = cr.fetchall()
        return lines_ord, data

    ##--------------------------------------------------------- function fields

    _columns = {
        'type': fields.selection(
            __TCV_MRP_ANUAL_REPORT_TYPES__, string='Type', required=True,
            readonly=False),
        #~ Must be added to corret % calculation
        'line_ids': fields.one2many(
            'tcv.mrp.anual.report.lines', 'line_id', 'Lines',
            readonly=True),
        'line_p_ids': fields.one2many(
            'tcv.mrp.anual.report.lines', 'line_id', 'Lines',
            readonly=True),
        'line_q_ids': fields.one2many(
            'tcv.mrp.anual.report.lines', 'line_id', 'Lines',
            readonly=True),
        'line_pq_ids': fields.one2many(
            'tcv.mrp.anual.report.lines', 'line_id', 'Lines',
            readonly=True),
        }

    _defaults = {
        'type': lambda *a: 10,
        }

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    def button_load_monthly_lines(self, cr, uid, ids, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        brw = self.browse(cr, uid, ids[0], context={})
        params = self.get_report_default_params(cr, uid, ids, brw)
        if params['type'] == 10:
            lines_ord, data = self._area_proceced_by_subprocess_m2(
                cr, uid, ids, params, context)
        elif params['type'] == 20:
            lines_ord, data = self._get_gangsaw_by_product_m2(
                cr, uid, ids, params, context)
            params.update({'add_summary': True})
        elif params['type'] == 25:
            lines_ord, data = self._get_gangsaw_by_hardness_m2(
                cr, uid, ids, params, context)
            params.update({'add_summary': True})
        elif params['type'] == 30:
            lines_ord, data = self._get_finished_slabs_by_product_m2(
                cr, uid, ids, params, context)
            params.update({'add_summary': True})
        elif params['type'] == 35:
            lines_ord, data = self._get_finished_slabs_by_hardness_m2(
                cr, uid, ids, params, context)
            params.update({'add_summary': True})
        elif params['type'] == 40:
            lines_ord, data = self._get_stop_issues_by_month_hrs(
                cr, uid, ids, params, context)
            params.update({'add_summary': True})
        elif params['type'] == 50:
            lines_ord, data = self._get_production_supplies(
                cr, uid, ids, params, context)
        elif params['type'] == 60:
            lines_ord, data = self._get_production_vs_waste(
                cr, uid, ids, params, context)
        elif params['type'] == 70:
            lines_ord, data = self._get_waste_by_origin_process(
                cr, uid, ids, params, context)
            params.update({'add_summary': True})
        else:
            lines_ord = []
            data = []
        self.load_report_data(cr, uid, ids, lines_ord, data, params, context)
        return True

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_mrp_anual_report()


##-------------------------------------------------- tcv_mrp_anual_report_lines


#~ Must be added to corret % calculation
class tcv_mrp_anual_report_lines(osv.osv_memory):

    _inherit = 'tcv.monthly.report.lines'

    _name = 'tcv.mrp.anual.report.lines'

    _columns = {
        'line_id': fields.many2one(
            'tcv.mrp.anual.report', 'Line', required=True,
            ondelete='cascade'),
        }

tcv_mrp_anual_report_lines()


##---------------------------------------------------------------------- Parser


class parser_tcv_mrp_anual_report(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        context = context or {}
        super(parser_tcv_mrp_anual_report, self).__init__(
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
        for item in __TCV_MRP_ANUAL_REPORT_TYPES__:
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
    'report.tcv.mrp.anual.report.report',
    'tcv.mrp.anual.report',
    'addons/tcv_monthly_report/report/tcv_monthly_report.rml',
    parser=parser_tcv_mrp_anual_report,
    header=False
    )
