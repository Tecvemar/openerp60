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

    ##------------------------------------------------------- _internal methods

    def default_get(self, cr, uid, fields, context=None):
        data = super(tcv_mrp_finished_slab_output_wizard, self).\
            default_get(cr, uid, fields, context)
        if not context.get('default_task_id'):
            return data
        obj_task = self.pool.get('tcv.mrp.finished.slab')
        obj_prd = self.pool.get('product.product')
        task = obj_task.browse(cr, uid, context['default_task_id'],
                               context=context)
        lines = []
        first_num = 1
        product_id = False
        for item in task.input_ids:
            if not product_id:
                if item.product_id.similarity_ids:
                    code = item.product_id.similarity_ids[0].default_code
                    prod_id = [item.product_id.similarity_ids[0].id]
                else:
                    code = '%sLS201' % item.product_id.default_code[:6]
                    prod_id = obj_prd.search(cr, uid, [('default_code', '=',
                                                        code)])
                if prod_id:
                    product_id = prod_id[0]
                else:
                    product_id = item.product_id.id
            line = {'input_id': item.id,
                    'prod_lot_ref': item.prod_lot_ref,
                    'product_id': product_id,
                    'length': item.length,
                    'heigth': item.heigth,
                    'pieces': item.pieces,
                    'thickness': item.thickness,
                    'first_num': first_num,
                    }
            first_num += item.pieces
            lines.append(line)
        data.update({'line_ids': lines})
        return data

    ##--------------------------------------------------------- function fields

    _columns = {
        'task_id': fields.many2one(
            'tcv.mrp.finished.slab', 'Task', required=True,
            ondelete='cascade'),
        'line_ids': fields.one2many(
            'tcv.mrp.finished.slab.output.wizard.line', 'line_id', 'Outcomes'),
        }

    _defaults = {
        }

    _sql_constraints = [
        ]

    ##-----------------------------------------------------

    ##----------------------------------------------------- public methods

    def gen_slabs(self, cr, uid, ids, context=None):
        """
        generate all lots
        """
        context = context or {}
        obj_slb = self.pool.get('tcv.mrp.finished.slab')
        obj_uom = self.pool.get('product.uom')
        for item in self.browse(cr, uid, ids, context={}):
            for wz in item.line_ids:
                lines = []
                for i in range(wz.pieces):
                    label_num = '%s%02d' % (wz.input_id.prod_lot_ref,
                                            i + wz.first_num)
                    total_area = obj_uom._calc_area(1, wz.input_id.length,
                                                    wz.input_id.heigth)
                    unit_cost = round(wz.input_id.real_unit_cost, 2)
                    slab = {'task_id': item.task_id.id,
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
                if lines:
                    upd_out = {'output_ids': lines}
                    obj_slb.write(cr, uid, item.task_id.id, upd_out,
                                  context=context)

    ##----------------------------------------------------- buttons (object)

    def button_done(self, cr, uid, ids, context):
        self.gen_slabs(cr, uid, ids, context=context)
        return {'type': 'ir.actions.act_window_close'}

    def button_renum_first_num(self, cr, uid, ids, context):
        first_num = 0
        obj_lin = self.pool.get('tcv.mrp.finished.slab.output.wizard.line')
        for item in self.browse(cr, uid, ids, context={}):
            for line in item.line_ids:
                if first_num:
                    data = {'first_num': first_num}
                    obj_lin.write(cr, uid, [line.id], data, context=context)
                else:
                    first_num = line.first_num
                first_num += line.pieces
        return False

    ##----------------------------------------------------- on_change...

    ##----------------------------------------------------- create write unlink

    ##----------------------------------------------------- Workflow

tcv_mrp_finished_slab_output_wizard()

##------------------------------------ tcv_mrp_finished_slab_output_wizard_line


class tcv_mrp_finished_slab_output_wizard_line(osv.osv_memory):

    _name = 'tcv.mrp.finished.slab.output.wizard.line'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def _fill_data(self, cr, uid, ids, context):
        return True

    ##--------------------------------------------------------- function fields

    _columns = {
        'line_id': fields.many2one(
            'tcv.mrp.finished.slab.output.wizard', 'Parent', required=True,
            ondelete='cascade'),
        'input_id': fields.many2one(
            'tcv.mrp.finished.slab.inputs', 'Origin', required=True,
            readonly=False, ondelete='cascade'),
        'prod_lot_ref': fields.char(
            'Lot reference', size=24, readonly=False),
        'location_id': fields.many2one(
            'stock.location', 'Location', required=True, select=True,
            ondelete='restrict', help=""),
        'pieces': fields.integer(
            'Pieces', readonly=False),
        'length': fields.float(
            string='Length (m)',
            digits_compute=dp.get_precision('Extra UOM data'), readonly=False),
        'heigth': fields.float(
            string='heigth (m)',
            digits_compute=dp.get_precision('Extra UOM data'), readonly=False),
        'thickness': fields.integer(
            'Thickness', readonly=False),
        'product_id': fields.many2one(
            'product.product', 'Product', ondelete='restrict', required=True,
            help="The finised output product",
            domain=[('sale_ok', '=', True), ('stock_driver', '=', 'slab')]),
        'first_num': fields.integer(
            'First slab #', required=True,
            help="The first number for sequence this set of slabs (to " +
            "complete the label number)"),
        }

    _defaults = {
        }

    _sql_constraints = [
        ('first_num_gt_zero', 'CHECK (first_num>0)',
         'The first_num must be > 0!'),
        ]

    ##-----------------------------------------------------

    ##----------------------------------------------------- public methods

    ##----------------------------------------------------- buttons (object)

    ##----------------------------------------------------- on_change...

    ##----------------------------------------------------- create write unlink

    def write(self, cr, uid, ids, vals, context=None):
        readonly_fields = ('input_id', 'prod_lot_ref', 'pieces',
                           'length', 'heigth', 'thickness')
        for f in readonly_fields:
            if f in vals:
                vals.pop(f)
        res = super(tcv_mrp_finished_slab_output_wizard_line, self).\
            write(cr, uid, ids, vals, context)
        return res

    ##----------------------------------------------------- Workflow

tcv_mrp_finished_slab_output_wizard_line()
