# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2014-11-11
#    Version: 0.0.0.1
#
#    Description:
#
#
##############################################################################

#~ from datetime import datetime
from osv import fields, osv
from tools.translate import _
#~ import pooler
import decimal_precision as dp
import time
#~ import netsvc

##---------------------------------------------------------- tcv_mrp_in_process


class tcv_mrp_in_process(osv.osv_memory):

    _name = 'tcv.mrp.in.process'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def _clear_lines(self, cr, uid, ids, context):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        unlink_ids = []
        for item in self.browse(cr, uid, ids, context={}):
            for l in item.line_ids:
                unlink_ids.append((2, l.id))
            self.write(cr, uid, ids, {'line_ids': unlink_ids}, context=context)
        return True

    def default_get(self, cr, uid, fields, context=None):
        data = super(tcv_mrp_in_process, self).default_get(
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
        'template_id': fields.many2one(
            'tcv.mrp.template', 'Task template', required=False,
            readonly=False, ondelete='restrict',
            domain=[('output_model', '!=', None)]),
        'loaded': fields.boolean(
            'Loaded'),
        'line_ids': fields.one2many(
            'tcv.mrp.in.process.lines', 'line_id', 'Lines', readonly=True),
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
select t.sequence, pc.id as process_id, pc.ref as process_ref,
       pc.name, sp.id as subprocess_id, sp.ref as subprocess_ref,
       o.prod_lot_ref, t.id as template_id, pr.id as product_id,
       pr.name as product, d.date_end, o.pieces,
       coalesce(i.used_pcs, 0) as used_pcs, o.length, o.heigth,
       o.real_unit_cost as unit_cost
from tcv_mrp_io_slab o
left join (
  select output_id, sum(pieces) as used_pcs from (
    select output_id, pieces from tcv_mrp_polish_inputs i
    left join tcv_mrp_polish t on i.task_id = t.id
    where t.date_end between '%(date_from)s 00:00'
                         and '%(date_to)s 23:59' union
    select output_id, pieces from tcv_mrp_resin_inputs i
    left join tcv_mrp_resin t on i.task_id = t.id
    where t.date_end between '%(date_from)s 00:00'
                         and '%(date_to)s 23:59' union
    select output_id, pieces from tcv_mrp_waste_slab_inputs i
    left join tcv_mrp_waste_slab t on i.task_id = t.id
    where t.date_end between '%(date_from)s 00:00'
                         and '%(date_to)s 23:59' union
    select output_id, pieces from tcv_mrp_finished_slab_inputs i
    left join tcv_mrp_finished_slab t on i.task_id = t.id
    where t.date_end between '%(date_from)s 00:00'
                         and '%(date_to)s 23:59'
    ) as q group by output_id
  ) as i on i.output_id = o.id
left join (
  select o.id, t.date_end from tcv_mrp_gangsaw t
  left join tcv_mrp_io_slab o on t.parent_id = o.subprocess_ref
  and t.id = o.task_ref union
  select o.id, t.date_end from tcv_mrp_polish t
  left join tcv_mrp_io_slab o on t.parent_id = o.subprocess_ref
  and t.id = o.task_ref union
  select o.id, t.date_end from tcv_mrp_resin t
  left join tcv_mrp_io_slab o on t.parent_id = o.subprocess_ref
  and t.id = o.task_ref
) as d on o.id = d.id
left join tcv_mrp_subprocess sp on o.subprocess_ref = sp.id
left join tcv_mrp_template t on sp.template_id = t.id
left join product_template pr on o.product_id = pr.id
left join tcv_mrp_process pc on sp.process_id = pc.id
where (o.pieces > i.used_pcs or i.used_pcs is null)
and t.sequence is not null
and d.date_end between '%(date_from)s 00:00'
               and '%(date_to)s 23:59'
order by t.sequence, d.date_end
        ''' % {'date_from': brw.date_from, 'date_to': brw.date_to}
        cr.execute(sql)
        line_ids = []
        for item in cr.fetchall():
            process_id = item[1]
            name = item[2]
            prod_lot_ref = item[6]
            template_id = item[7]
            product_id = item[8]
            date_end = item[10]
            pieces = item[11]
            used_pcs = item[12]
            length = item[13]
            heigth = item[14]
            unit_cost = item[15]
            if not brw.template_id or brw.template_id.id == template_id:
                line_ids.append(
                    (0, 0, {'template_id': template_id,
                            'name': name,
                            'process_id': process_id,
                            'progress': round((used_pcs * 100.0) / pieces, 2),
                            'product_id': product_id,
                            'prod_lot_ref': prod_lot_ref,
                            'date_end': date_end,
                            'pieces': pieces - used_pcs,
                            'length': length,
                            'heigth': heigth,
                            'unit_cost': unit_cost,
                            }))
        if line_ids:
            self._clear_lines(cr, uid, ids, context)
            self.write(cr, uid, ids, {
                'line_ids': line_ids, 'loaded': bool(line_ids)},
                context=context)
        return True

    ##------------------------------------------------------------ on_change...

    def on_change_date(self, cr, uid, ids, date_start, date_en):
        res = {}
        self._clear_lines(cr, uid, ids, context=None)
        res.update({'loaded': False, 'line_ids': []})
        return {'value': res}

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_mrp_in_process()


##---------------------------------------------------- tcv_mrp_in_process_lines


class tcv_mrp_in_process_lines(osv.osv_memory):

    _name = 'tcv.mrp.in.process.lines'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def _compute_all(self, cr, uid, ids, field_name, arg, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        res = {}
        obj_uom = self.pool.get('product.uom')
        for item in self.browse(cr, uid, ids, context=context):
            area = obj_uom._calc_area(item.pieces, item.length, item.heigth)
            res[item.id] = {'area': area,
                            'total_cost': area * item.unit_cost,
                            }
        return res

    ##--------------------------------------------------------- function fields

    _columns = {
        'line_id': fields.many2one(
            'tcv.mrp.in.process', 'Line', required=True, ondelete='cascade'),
        'name': fields.char(
            'Name', size=64, required=False, readonly=False),
        'template_id': fields.many2one(
            'tcv.mrp.template', 'Task template', required=True,
            readonly=False, ondelete='restrict'),
        'process_id': fields.many2one(
            'tcv.mrp.process', 'Process', required=True, ondelete='cascade'),
        'date_end': fields.datetime(
            'Date end', required=False, select=True),
        'product_id': fields.many2one(
            'product.product', 'Product', ondelete='restrict'),
        'prod_lot_ref': fields.char(
            'lot ref', size=64, required=False, readonly=False),
        'progress': fields.float(
            'Progress', digits=(8, 2)),
        'pieces': fields.integer(
            'Slabs'),
        'length': fields.float(
            'Length (m)', digits_compute=dp.get_precision('Extra UOM data')),
        'heigth': fields.float(
            'Heigth (m)', digits_compute=dp.get_precision('Extra UOM data')),
        'area': fields.function(
            _compute_all, method=True, type='float', string='Area (m2)',
            digits_compute=dp.get_precision('Product UoM'), multi='all'),
        'unit_cost': fields.float(
            'Unit cost', digits_compute=dp.get_precision('Account')),
        'total_cost': fields.function(
            _compute_all, method=True, type='float', string='Total cost',
            digits_compute=dp.get_precision('Account'), multi='all'),
        }

    _defaults = {
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    def button_show_process(self, cr, uid, ids, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        brw = self.browse(cr, uid, ids[0], context={})
        return {'name': _('Production process'),
                'type': 'ir.actions.act_window',
                'res_model': 'tcv.mrp.process',
                'view_type': 'form',
                'view_id': False,
                'view_mode': 'form',
                'nodestroy': True,
                'res_id': brw.process_id.id,
                'target': 'current',
                'domain': "",
                'context': {}}

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_mrp_in_process_lines()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
