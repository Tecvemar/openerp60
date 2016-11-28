# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description:
#       Wizard to import multime account moves
#
##############################################################################

#~ from datetime import datetime
from osv import fields, osv
#~ from tools.translate import _
#~ import pooler
import decimal_precision as dp
#~ import time


##----------------------------------------- tcv_mrp_finished_slab_output_wizard


class tcv_mrp_finished_slab_output_wizard(osv.osv_memory):

    _name = 'tcv.mrp.finished.slab.output.wizard'

    _description = ''

    ##-------------------------------------------------------------------------

    ##--------------------------------------------------------- function fields

    _columns = {
        'input_id': fields.many2one(
            'tcv.mrp.finished.slab.inputs', 'Origin', required=True,
            ondelete='cascade'),
        'prod_lot_ref': fields.char(
            'Lot reference', size=24, readonly=True),
        'location_id': fields.many2one(
            'stock.location', 'Location', required=True, select=True,
            ondelete='restrict', help=""),
        'pieces': fields.integer('Pieces', readonly=False),
        'length': fields.float(
            string='Length (m)',
            digits_compute=dp.get_precision('Extra UOM data'),
            readonly=True),
        'heigth': fields.float(
            string='heigth (m)',
            digits_compute=dp.get_precision('Extra UOM data'),
            readonly=True),
        'thickness': fields.integer(
            'Thickness', readonly=True),
        'product_id': fields.many2one(
            'product.product', 'Product', ondelete='restrict',
            required=True, help="The finised output product",
            domain=[('sale_ok', '=', True), ('stock_driver', '=', 'slab')]),
        'first_num': fields.integer(
            'First slab #', required=True, help="The first number for " +
            "sequence this set of slabs (to complete the label number)"),
        }

    _defaults = {
        'first_num': lambda *a: 1,
        }

    _sql_constraints = [
        ('first_num_gt_zero', 'CHECK (first_num>0)',
         'The first_num must be > 0!'),
        ]

    ##-------------------------------------------------------------------------

    def gen_slabs(self, cr, uid, ids, context=None):
        """
        generate all lots
        """
        if context is None:
            context = {}
        obj_slb = self.pool.get('tcv.mrp.finished.slab')
        obj_uom = self.pool.get('product.uom')
        wz = self.browse(cr, uid, ids[0], context=context)
        lines = []
        if context.get('task_id'):
            task_id = context['task_id']
            for i in range(wz.pieces):
                label_num = '%s%02d' % (
                    wz.input_id.prod_lot_ref, i + wz.first_num)
                total_area = obj_uom._calc_area(
                    1, wz.input_id.length, wz.input_id.heigth)
                unit_cost = round(wz.input_id.real_unit_cost, 2)
                slab = {'task_id': task_id,
                        'input_id': wz.input_id.id,
                        'product_id': wz.product_id.id,
                        'prod_lot_ref': label_num,
                        'location_id': wz.location_id.id,
                        'length': wz.input_id.length,
                        'heigth': wz.input_id.heigth,
                        'pieces': 1,
                        'thickness': wz.input_id.thickness,
                        'real_unit_cost': unit_cost,
                        'total_cost': round(total_area * unit_cost, 2),
                        }
                lines.append((0, 0, slab))
            upd_out = {'output_ids': lines}
            obj_slb.write(cr, uid, task_id, upd_out, context=context)

    def button_save_close(self, cr, uid, ids, context):
        self.gen_slabs(cr, uid, ids, context=context)
        return {'type': 'ir.actions.act_window_close'}

    def button_save_new(self, cr, uid, ids, context):
        self.gen_slabs(cr, uid, ids, context=context)
        data = self.browse(cr, uid, ids[0], context=context)
        next_num = int(data.input_id.pieces) + int(data.first_num)
        self.write(cr, uid, ids, {'input_id': 0,
                                  'first_num': next_num}, context)
        return True

    ##------------------------------------------------------------ on_change...

    def on_change_input_id(self, cr, uid, ids, input_id):
        if input_id:
            obj_io = self.pool.get('tcv.mrp.finished.slab.inputs')
            so_brw = obj_io.browse(cr, uid, input_id, None)
            res = ({'prod_lot_ref': so_brw.prod_lot_ref,
                    'pieces': so_brw.pieces,
                    'length': so_brw.length,
                    'heigth': so_brw.heigth,
                    'thickness': so_brw.thickness
                    })
            return {'value': res}

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_mrp_finished_slab_output_wizard()
