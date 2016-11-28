# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description:
#
#
##############################################################################
#~ from datetime import datetime
from osv import fields, osv
#~ from tools.translate import _
#~ import pooler
import decimal_precision as dp
#~ import time
#~ import netsvc

##------------------------------------------------------------- tcv_mrp_io_slab


class tcv_mrp_io_slab(osv.osv):

    _name = 'tcv.mrp.io.slab'

    _description = ''

    _order = 'task_ref, cost_line'

    _rec_name = 'prod_lot_ref'

    ##-------------------------------------------------------------------------

    def _calc_available_pcs(self, cr, uid, ids, io_obj, context):
        obj_spr = self.pool.get('tcv.mrp.subprocess')
        subp = obj_spr.browse(cr, uid, io_obj.subprocess_ref, context=context)
        # Find all models with input_model = io_obj.output_model
        input_model = subp.template_id.output_model.id
        used_slabs = 0
        if input_model:
            cr.execute('''
            select distinct m.model from tcv_mrp_template t
            left join ir_model m on t.res_model = m.id
            where t.input_model = %s
            ''' % (input_model))
            for model in cr.fetchall():
                table_name = model[0].replace('.', '_')
                cr.execute('''
                select sum(pieces) pieces from %s_inputs where output_id = %d
                ''' % (table_name, io_obj.id))
                used_slabs += cr.fetchone()[0] or 0
        return int(io_obj.pieces - used_slabs)

    def _calc_output_progress(self, cr, uid, subprocess_id, context):
        '''
        this method must be declared in all io models
        '''
        progress = max = position = 0.0
        ids = self.search(cr, uid, [('subprocess_ref', '=', subprocess_id)])
        if ids:
            for l in self.browse(cr, uid, ids, context=context):
                max += int(l.pieces)
                position += int(l.pieces) - int(l.available_pcs)
            progress = (position * 100.0) / max
        return progress

    ##--------------------------------------------------------- function fields

    def _compute_all(self, cr, uid, ids, name, arg, context=None):
        if context is None:
            context = {}
        if not len(ids):
            return []
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            #~ total_area = obj_uom._calc_area(line.pieces, line.length,
            #~ line.heigth)
            available_pcs = self._calc_available_pcs(
                cr, uid, ids, line, context)
            res[line.id] = {'available_pcs': available_pcs}
        return res

    ##-------------------------------------------------------------------------

    _columns = {
        'task_ref': fields.integer(
            'Task'),
        'subprocess_ref': fields.integer(
            'Subprocess'),
        'cost_line': fields.integer(
            'Cost line'),
        'type': fields.selection([(
            'input', 'Input'), ('output', 'Output')], string='Type',
            required=True, readonly=True),
        'product_id': fields.many2one(
            'product.product', 'Product', ondelete='restrict'),
        'prod_lot_ref': fields.char(
            'Lot reference', size=16, required=False, readonly=False),
        'thickness': fields.integer(
            'Thickness (mm)', help="The product thickness, " +
            "correction value for volume calculation assigned in template: " +
            " thickness_factor_correction"),
        'pieces': fields.integer(
            'Slabs'),
        'available_pcs': fields.function(
            _compute_all, method=True, type='integer', string='Availables pcs',
            multi='all'),
        'length': fields.float(
            'Length (m)', digits_compute=dp.get_precision('Extra UOM data')),
        'heigth': fields.float(
            'Heigth (m)', digits_compute=dp.get_precision('Extra UOM data')),
        'total_area': fields.float(
            'Area (m2)', digits_compute=dp.get_precision('Product UoM')),
        'real_unit_cost': fields.float(
            'Unit cost', digits_compute=dp.get_precision('MRP unit cost'),
            readonly=True),
        'total_cost': fields.float(
            'Total cost', digits_compute=dp.get_precision('Account'),
            readonly=True),
        }

    _defaults = {
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_mrp_io_slab()
