# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description: Report parser for: tcv_mrp_gangsaw_by_hardness
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


class parser_tcv_mrp_gangsaw_by_hardness(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        context = context or {}
        super(parser_tcv_mrp_gangsaw_by_hardness, self).__init__(
            cr, uid, name, context=context)
        self.localcontext.update({
            'get_summary': self._get_summary,
            })
        self.context = context

    def _get_summary(self, obj):
        fields = (
            'blocks', 'block_qty', 'slab_qty', 'slab_area',
            )
        groups = []
        totals = {}
        if obj.order_by == 'sp.name,pp.hardness':  # By Gangsaw
            fld_grp = 'name'
        else:
            fld_grp = 'hardness'
        for line in obj.line_ids:
            if not line[fld_grp] in groups:
                groups.append(line[fld_grp])
        for group in groups:
            totals[group] = {}
            for key in fields:
                totals[group][key] = 0
        #~ Compute Totals
        for line in obj.line_ids:
            for key in fields:
                totals[line[fld_grp]][key] += line[key]
                totals[line[fld_grp]].update({'name': line[fld_grp]})
        res = []
        for group in groups:
            res.append(totals[group])
        return res

report_sxw.report_sxw(
    'report.tcv.mrp.gangsaw.by.hardness.report',
    'tcv.mrp.gangsaw.by.hardness',
    'addons/tcv_mrp/report/tcv_mrp_gangsaw_by_hardness.rml',
    parser=parser_tcv_mrp_gangsaw_by_hardness,
    header=False
    )


##------------------------------------------------- tcv_mrp_gangsaw_by_hardness


class tcv_mrp_gangsaw_by_hardness(osv.osv_memory):

    _name = 'tcv.mrp.gangsaw.by.hardness'

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
        data = super(tcv_mrp_gangsaw_by_hardness, self).default_get(
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
            'tcv.mrp.gangsaw.by.hardness.lines', 'line_id', 'Lines',
            readonly=True),
        'order_by': fields.selection(
            [('sp.name,pp.hardness', 'Gangsaw and hardness'),
             ('pp.hardness,sp.name', 'Hardness and gangsaw')],
            string='Order by', required=True),
        }

    _defaults = {
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company').
        _company_default_get(cr, uid, self._name, context=c),
        'order_by': lambda *a: 'sp.name,pp.hardness',
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
select sp.name, case pp.hardness
                   when 1 then 'Soft'
                   when 2 then 'Soft-Medium'
                   when 3 then 'Medium'
                   when 4 then 'Medium-Hard'
                   when 5 then 'Hard'
                   else '-' end as hardness,
       count(b.id) as blocks,
       sum(l.length*l.width*l.heigth) as block_qty,
       sum(b.slab_qty) as slab_qty,
       sum(b.slab_qty*b.net_length*b.net_heigth) as slab_area
from tcv_mrp_gangsaw_blocks b
left join product_product pp on b.product_id = pp.id
left join product_template pt on b.product_id = pt.id
left join tcv_mrp_gangsaw g on b.gangsaw_id = g.id
left join tcv_mrp_subprocess sp on g.parent_id = sp.id
left join stock_production_lot l on b.prod_lot_id = l.id
where g.date_end between '%(date_from)s 00:00:00' and
                         '%(date_to)s 23:59:59'
group by sp.name, pp.hardness
order by %(order_by)s
        ''' % {'date_from': brw.date_from,
               'date_to': brw.date_to,
               'order_by': brw.order_by}
        cr.execute(sql)
        line_ids = []
        for item in cr.dictfetchall():
            line_ids.append(
                (0, 0, {'name': item.get('name'),
                        'hardness': item.get('hardness'),
                        'blocks': item.get('blocks'),
                        'block_qty': item.get('block_qty'),
                        'slab_qty': item.get('slab_qty'),
                        'slab_area': item.get('slab_area'),
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

tcv_mrp_gangsaw_by_hardness()


class tcv_mrp_gangsaw_by_hardness_lines(osv.osv_memory):

    _name = 'tcv.mrp.gangsaw.by.hardness.lines'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'line_id': fields.many2one(
            'tcv.mrp.gangsaw.by.hardness', 'Lines', required=True,
            ondelete='cascade'),
        'name': fields.char(
            'Name', size=64, required=False, readonly=True),
        'slab_qty': fields.integer(
            'Slab qty', size=64, required=False, readonly=True),
        'slab_area': fields.float(
            'Slab area (m2)',
            digits_compute=dp.get_precision('Extra UOM data'),
            readonly=True),
        'blocks': fields.integer(
            'Block qty', size=64, required=False, readonly=True),
        'block_qty': fields.float(
            'Block area (m3)',
            digits_compute=dp.get_precision('Extra UOM data'),
            readonly=True),
        'hardness': fields.char(
            'Hardness', size=64, required=False, readonly=True),
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

tcv_mrp_gangsaw_by_hardness_lines()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
