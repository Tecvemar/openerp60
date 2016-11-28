# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date: 03/10/2012
#    Version: 0.0.0.0
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
#~ import time
#~ import netsvc

##--------------------------------------------------------------- tcv_mrp_resin


class tcv_mrp_resin(osv.osv):

    _name = 'tcv.mrp.resin'

    _inherit = 'tcv.mrp.basic.task'

    _description = ''

    def _template_params(self):
        res = super(tcv_mrp_resin, self)._template_params()
        res.extend([
            {'sequence': 30, 'name': 'resin_qty_m2', 'type': 'float',
             'help': 'Cantidad de resina usada por m2 (ver UOM)'},
            {'sequence': 40, 'name': 'resin_qty_uom', 'type': 'char',
             'help': 'Unidad de medida de la cantidad por m2',
             'char_val': 'g'},
            {'sequence': 50, 'name': 'default_resin_product',
             'type': 'char', 'help': 'Resina a aplicar (Código del producto)',
             'char_val': '03055015'},
            {'sequence': 60, 'name': 'default_catalyst_product',
             'type': 'char', 'help': 'Catalizador (Código del producto)',
             'char_val': 'CATALIZ350'},
            {'sequence': 70, 'name': 'catalyst_percent', 'type': 'float',
             'help': 'Cantidad de catalizador por cada 100g de resina',
             'float_val': '35'},
            ])
        return res

    ##-------------------------------------------------------------------------

    def _get_task_info(self, cr, uid, obj_task, context=None):
        res = ''
        for imp in obj_task.input_ids:
            info = '[%s] %s (%s %sx%s)' % (imp.product_id.default_code,
                                           imp.prod_lot_ref, imp.pieces,
                                           imp.length, imp.heigth)
            res = '%s, %s' % (res, info) if res else info
        return res[:128]

    ##--------------------------------------------------------- function fields

    _columns = {
        'input_ids': fields.one2many(
            'tcv.mrp.resin.inputs', 'task_id', 'String', readonly=True,
            states={'draft': [('readonly', False)]}),
        'supplies_ids': fields.one2many(
            'tcv.mrp.resin.supplies', 'task_id', 'Supplies', readonly=True,
            states={'draft': [('readonly', False)]}),
        'output_ids': fields.one2many(
            'tcv.mrp.resin.output', 'task_id', 'Output data', readonly=True,
            states={'draft': [('readonly', False)]}),
        'costs_ids': fields.one2many(
            'tcv.mrp.resin.costs', 'task_id', 'Output data', readonly=True),
        'resin_qty_m2': fields.float(
            'Resin/m2', digits_compute=dp.get_precision('Account'),
            readonly=True, help="Estimated resin+catalyst quantity per m2, " +
            "from template (resin_qty_m2)"),
        'catalyst_percent': fields.float(
            'Catalyst %', digits_compute=dp.get_precision('Account'),
            readonly=True, help="Quantity of catalyst (grams) " +
            "per 100 grams of resin, from template (catalyst_percent)"),
        }

    _defaults = {
    }

    _sql_constraints = [
    ]

    def compute_resin_qty(self, cr, uid, ids, context=None):
        so_brw = self.browse(cr, uid, ids, context)
        obj_sup = self.pool.get('tcv.mrp.resin.supplies')
        for resin in so_brw:
            m2 = 0
            for i in resin.input_ids:
                m2 += i.total_area
            context.update({'resin_qty_m2': resin.resin_qty_m2,
                            'catalyst_percent': resin.catalyst_percent})
            resin_data = obj_sup.calc_resin_catalyst_supplies(
                cr, uid, resin.parent_id.template_id.id, m2, context)
            #~ id = 0
            if resin_data:
                update_data = []
                for s in resin.supplies_ids:
                    if s.type == 'resin':
                        update_data.append((1, s.id,
                                            {'quantity': resin_data[0]
                                             ['quantity']}))
                    elif s.type == 'catalyst':
                        update_data.append((1, s.id,
                                            {'quantity': resin_data[1]
                                             ['quantity']}))
                if update_data:
                    self.write(cr, uid, resin.id,
                               {'supplies_ids': update_data}, context)
        return True

    def _calc_supplies_operator_factory_cost(self, cr, uid, ids, output,
                                             supplies_ids, output_area,
                                             round_to, context=None):
        so_brw = self.browse(cr, uid, ids, context={})[0]
        supplies_cost = round((
            so_brw.supplies_cost * output.total_area) / output_area, round_to)
        if so_brw.date_end >= self._change_method_date:
            values = self._compute_cost_by_m2(
                cr, uid, so_brw, output_area, round_to)
            operator_cost = round(
                (values.get('operator_cost_m2', 0) *
                 output.total_area) / output_area, round_to)
            factory_overhead = round(
                (values.get('factory_overhead_m2', 0) *
                 output.total_area) / output_area, round_to)
        else:
            operator_cost = round((
                self._compute_operator_cost(so_brw, round_to) *
                output.total_area) / output_area, round_to)
            factory_overhead = round((
                self._compute_factory_overhead(so_brw, round_to) *
                output.total_area) / output_area, round_to)
        return supplies_cost, operator_cost, factory_overhead

    def cost_distribution(self, cr, uid, ids, context=None):
        #~ res = {}
        so_brw = self.browse(cr, uid, ids, context={})
        #~ obj_tmp = self.pool.get('tcv.mrp.template')
        round_to = 2
        for item in so_brw:
            self._clear_previous_cost_distribution(cr, uid, item, context)
            output_area = 0
            for output in item.output_ids:
                output_area += output.total_area
            lines = []
            for output in item.output_ids:
                supplies_cost, operator_cost, factory_overhead = \
                    self._calc_supplies_operator_factory_cost(
                        cr, uid, ids, output, item.supplies_ids, output_area,
                        round_to, context)
                # Take the total cost of input and distributed based on the
                # number of slabss output
                # Toma el costo total de la entrada y lo distribuye en funcion
                # de la cantidad de laminas de salida
                cumulative_cost = (
                    output.input_id.total_cost * output.pieces) / output.input_id.pieces
                line = {'output_id': output.id,
                        'cumulative_cost': cumulative_cost,
                        'supplies_cost': supplies_cost,
                        'operator_cost': operator_cost,
                        'factory_overhead': factory_overhead,
                        'total_area': output.total_area,
                        }
                line.update({'total_cost': cumulative_cost + supplies_cost +
                             operator_cost + factory_overhead})
                line.update({'real_unit_cost': line[
                             'total_cost'] / line['total_area']})
                lines.append((0, 0, line))
            if lines:
                self.write(
                    cr, uid, item.id, {'costs_ids': lines, 'valid_cost': True},
                    context)
                self.save_output_products(cr, uid, ids, context)
        return True

    def load_default_values(self, cr, uid, parent_id, context=None):
        '''
        If required, here you can create here a new task with any default data
        this method must be overriden in inherited models
        '''
        res = super(
            tcv_mrp_resin, self).load_default_values(
                cr, uid, parent_id, context)

        obj_spr = self.pool.get('tcv.mrp.subprocess')
        obj_sup = self.pool.get('tcv.mrp.resin.supplies')
        obj_tmp = self.pool.get('tcv.mrp.template')

        subp = obj_spr.browse(cr, uid, parent_id, context=context)
        m2 = 0  # to store area to be resined

        input_list = []
        if subp.prior_id:
            model = subp.prior_id.template_id.output_model.name
            obj_pri = self.pool.get(model)
            output_ids = obj_pri.search(cr, uid, [(
                'subprocess_ref', '=', subp.prior_id.id),
                ('type', '=', 'output')])
            outputs = obj_pri.browse(cr, uid, output_ids, context=context)
            for output in outputs:
                if int(output.available_pcs):
                    input_list.append({'pieces': output.available_pcs,
                                       'output_id': output.id,
                                       'product_id': output.product_id.id,
                                       'prod_lot_ref': output.prod_lot_ref,
                                       'length': output.length,
                                       'heigth': output.heigth,
                                       'thickness': output.thickness,
                                       'total_area': output.total_area,
                                       'real_unit_cost': output.real_unit_cost,
                                       'total_cost': output.total_cost
                                       })
                    m2 += output.total_area

        if not input_list:
            raise osv.except_osv(_('Error!'), _('No outputs to be processed'))

        resin_qty_m2 = obj_tmp.get_var_value(
            cr, uid, subp.template_id.id, 'resin_qty_m2') or 0
        catalyst_percent = obj_tmp.get_var_value(
            cr, uid, subp.template_id.id, 'catalyst_percent') or 0

        supplies_list = obj_sup.calc_resin_catalyst_supplies(
            cr, uid, subp.template_id.id, m2, context)

        if supplies_list or input_list:
            res.update({'default_supplies_ids': supplies_list,
                        'default_input_ids': input_list,
                        'default_resin_qty_m2': resin_qty_m2,
                        'default_catalyst_percent': catalyst_percent,
                        })

        return res

    def get_output_data_line(self, item, line):
        product_id = line.output_id.product_id.id
        lot_name = line.output_id.input_id.prod_lot_ref
        return {'task_ref': item.id,
                'subprocess_ref': item.parent_id.id,
                'cost_line': line.id,
                'type': 'output',
                'product_id': product_id,
                'prod_lot_ref': lot_name,
                'thickness': line.output_id.thickness,
                'pieces': line.output_id.pieces,
                'length': line.output_id.length,
                'heigth': line.output_id.heigth,
                'total_area': line.total_area,
                'real_unit_cost': line.real_unit_cost,
                'total_cost': line.total_cost,
                }

    def create_account_move_lines(self, cr, uid, task, lines, context=None):
        '''
        Must be overridden in models inherited
        Here you create and return a acount.move.lines (list of dict)
        '''
        res = super(tcv_mrp_resin, self).create_account_move_lines(
            cr, uid, task, lines, context)
        return res

    def create_stock_picking(self, cr, uid, ids, vals, context=None):
        #~ This task should not create a stock picking
        return False

    def get_task_input_sumary(self, cr, uid, ids_str, context=None):
        sql = """
        select sum(i.pieces) pieces, sum(i.pieces*heigth*length) as qty
        from tcv_mrp_resin_inputs i
        left join tcv_mrp_io_slab s on i.output_id = s.id
        where task_id in %s
        """ % ids_str
        cr.execute(sql)
        return cr.dictfetchone()

    def get_task_output_sumary(self, cr, uid, ids_str, context=None):
        sql = """
        select sum(pieces) pieces, sum(pieces*heigth*length) as qty
        from tcv_mrp_resin_output
        where task_id in %s
        """ % ids_str
        cr.execute(sql)
        return cr.dictfetchone()

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_mrp_resin()

##-------------------------------------------------------- tcv_mrp_resin_inputs


class tcv_mrp_resin_inputs(osv.osv):

    _name = 'tcv.mrp.resin.inputs'

    _description = 'Calc resin inputs'

    ##-------------------------------------------------------------------------

    def load_input_data(self, cr, uid, output_obj, pieces, context):
        '''
        output_obj must be a valid self.pool.get('tcv.mrp.io.slab').browse()
        '''
        if context is None:
            context = {}
        obj_uom = self.pool.get('product.uom')
        total_area = obj_uom._calc_area(
            pieces, output_obj.length, output_obj.heigth)
        total_cost = total_area * output_obj.real_unit_cost
        return {
            'product_id': output_obj.product_id.id,
            'prod_lot_ref': output_obj.prod_lot_ref,
            'available_pcs': output_obj.available_pcs,
            'length': output_obj.length,
            'heigth': output_obj.heigth,
            'thickness': output_obj.thickness,
            'total_area': total_area,
            'real_unit_cost': output_obj.real_unit_cost,
            'total_cost': total_cost,
            }

    def name_get(self, cr, uid, ids, context):
        if not len(ids):
            return []
        res = []
        inputs = self.browse(cr, uid, ids, context)
        for i in inputs:
            res.append((i.id, '%s (%s)' % (i.product_id.name, i.prod_lot_ref)))
        return res

    ##--------------------------------------------------------- function fields

    def _compute_all(self, cr, uid, ids, name, arg, context=None):
        if context is None:
            context = {}
        if not len(ids):
            return []
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = self.load_input_data(
                cr, uid, line.output_id, line.pieces, context)
            res[line.id].pop('product_id')
        return res

    ##-------------------------------------------------------------------------

    _columns = {
        'task_id': fields.many2one(
            'tcv.mrp.resin', 'inputs', required=True, ondelete='cascade'),
        'output_id': fields.many2one(
            'tcv.mrp.io.slab', 'inputs', required=True, ondelete='restrict',
            readonly=False),
        'product_id': fields.related(
            'output_id', 'product_id', type='many2one',
            relation='product.product', string='Product',
            store=False, readonly=True),
        'prod_lot_ref': fields.function(
            _compute_all, method=True, type='char',
            string='Lot reference', multi='all'),
        'pieces': fields.integer(
            'slabs'),
        'available_pcs': fields.function(
            _compute_all, method=True, type='integer',
            string='Availables pcs', multi='all'),
        'length': fields.function(
            _compute_all, method=True, type='float', string='Length (m)',
            digits_compute=dp.get_precision('Extra UOM data'), multi='all'),
        'heigth': fields.function(
            _compute_all, method=True, type='float', string='Heigth (m)',
            digits_compute=dp.get_precision('Extra UOM data'), multi='all'),
        'thickness': fields.function(
            _compute_all, method=True, type='integer',
            string='Thickness', multi='all'),
        'total_area': fields.function(
            _compute_all, method=True, type='float', string='Area (m2)',
            digits_compute=dp.get_precision('Product UoM'), multi='all'),
        'real_unit_cost': fields.function(
            _compute_all, method=True, type='float', string='Unit cost',
            digits_compute=dp.get_precision('MRP unit cost'), multi='all'),
        'total_cost': fields.function(
            _compute_all, method=True, type='float', string='Total cost',
            digits_compute=dp.get_precision('Account'), multi='all'),
        }

    _defaults = {
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------------ on_change...

    def on_change_pieces(self, cr, uid, ids, output_id, pieces):
        if output_id:
            context = {}
            obj_io = self.pool.get('tcv.mrp.io.slab')
            so_brw = obj_io.browse(cr, uid, output_id, context)
            if pieces == 0:
                pieces += int(so_brw.available_pcs)
            res = self.load_input_data(cr, uid, so_brw, pieces, context)
            res.update({'pieces': pieces})
            return {'value': res}

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_mrp_resin_inputs()

##------------------------------------------------------ tcv_mrp_resin_supplies


class tcv_mrp_resin_supplies(osv.osv):

    _name = 'tcv.mrp.resin.supplies'

    _inherit = 'tcv.mrp.basic.task.supplies'

    _description = ''

    ##-------------------------------------------------------------------------

    ##--------------------------------------------------------- function fields

    _columns = {
        'task_id': fields.many2one(
            'tcv.mrp.resin', 'Supplies', required=True, ondelete='cascade'),
        'type': fields.selection(
            [('resin', 'Resin'), ('catalyst', 'Catalyst'), ('other', 'Other')],
            string='Type', required=True),
        }

    _defaults = {
        'type': lambda *a: 'other',
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    def calc_resin_catalyst_supplies(self, cr, uid, template_id, m2, context):
        '''
        return a list of dict with resin & catalyst supplies required
        distributed by m2

        Example:

            35% resin means: 100g Resin + 35g Catalyst = 135g
            37% resin means: 100g Resin + 37g Catalyst = 137g
        '''

        res = []

        #~ obj_spr = self.pool.get('tcv.mrp.subprocess')
        obj_tmp = self.pool.get('tcv.mrp.template')
        obj_uom = self.pool.get('product.uom')
        obj_prd = self.pool.get('product.product')
        obj_cst = self.pool.get('tcv.cost.management')
        #~ obj_sup = self.pool.get('tcv.mrp.resin.supplies')

        #get basic data from template
        template_params = obj_tmp.get_all_values(cr, uid, template_id)
        resin_qty_m2 = context.get(
            'resin_qty_m2') or template_params['resin_qty_m2']
        resin_qty_uom = template_params['resin_qty_uom']
        mix_qty_grs = (m2 * resin_qty_m2)
        # resin_qty_m2 in grams / la cantidad de resina viene en gramos

        catalyst_mix_pct = context.get(
            'catalyst_percent') or template_params['catalyst_percent']

        percent_100 = catalyst_mix_pct + 100
        catalyst_percent = catalyst_mix_pct / percent_100
        resin_percent = 1 - catalyst_percent

        from_uom_id = obj_uom.search(cr, uid, [(
            'name', '=', resin_qty_uom)])[0]

        # default_resin_product (resin)
        product = template_params['default_resin_product']
        if product:  #
            product_id = obj_prd.search(cr, uid, [(
                'default_code', '=', product)])[0]
            product = obj_prd.browse(cr, uid, product_id, context=context)
            real_qty = obj_uom._compute_qty(
                cr, uid, from_uom_id, mix_qty_grs * resin_percent,
                product.uom_id.id)
            unit_price = obj_cst.get_tcv_cost(
                cr, uid, None, product_id, context)
            res.append({
                'type': 'resin', 'product_id': product_id,
                'quantity': real_qty, 'unit_price': unit_price,
                'amount': real_qty * unit_price})

        # default_catalyst_product (catalyst)
        product = template_params['default_catalyst_product']
        if product:
            product_id = obj_prd.search(
                cr, uid, [('default_code', '=', product)])[0]
            product = obj_prd.browse(cr, uid, product_id, context=context)
            real_qty = obj_uom._compute_qty(
                cr, uid, from_uom_id, mix_qty_grs * catalyst_percent,
                product.uom_id.id)
            unit_price = obj_cst.get_tcv_cost(
                cr, uid, None, product_id, context)
            res.append({
                'type': 'catalyst', 'product_id': product_id,
                'quantity': real_qty, 'unit_price': unit_price,
                'amount': real_qty * unit_price})

        return res

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_mrp_resin_supplies()

##-------------------------------------------------------- tcv_mrp_resin_output


class tcv_mrp_resin_output(osv.osv):

    _name = 'tcv.mrp.resin.output'

    _description = ''

    ##-------------------------------------------------------------------------

    def name_get(self, cr, uid, ids, context):
        if not len(ids):
            return []
        res = []
        output = self.browse(cr, uid, ids, context)
        for o in output:
            res.append((o.id, '%s (%s) [%s - (%sx%s) (%smm)]' % (
                o.product_id.name, o.input_id.prod_lot_ref, o.pieces,
                o.length, o.heigth, o.thickness)))
        return res

    ##--------------------------------------------------------- function fields

    def _compute_area(self, cr, uid, ids, name, args, context=None):
        res = {}
        obj_uom = self.pool.get('product.uom')
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = obj_uom._calc_area(
                line.pieces, line.length, line.heigth)
        return res

    ##-------------------------------------------------------------------------

    _columns = {
        'task_id': fields.many2one(
            'tcv.mrp.resin', 'Blocks', required=True, ondelete='cascade'),
        'input_id': fields.many2one(
            'tcv.mrp.resin.inputs', 'Origin', required=True,
            ondelete='cascade'),
        'product_id': fields.many2one(
            'product.product', 'Product', ondelete='restrict',
            required=True, help="The output product"),
        'length': fields.float(
            'Length (m)', digits_compute=dp.get_precision('Extra UOM data')),
        'heigth': fields.float(
            'Heigth (m)', digits_compute=dp.get_precision('Extra UOM data')),
        'pieces': fields.integer(
            'Slabs'),
        'thickness': fields.integer(
            'Thickness (mm)', help="The product thickness, correction value " +
            "for volume calculation assigned in template: " +
            "thickness_factor_correction"),
        'total_area': fields.function(
            _compute_area, method=True, type='float', string='Area (m2)',
            digits_compute=dp.get_precision('Product UoM')),
        }

    _defaults = {
        }

    _sql_constraints = [
        ('length_gt_zero', 'CHECK (length>0)', 'The length must be > 0!'),
        ('heigth_gt_zero', 'CHECK (heigth>0)', 'The heigth must be > 0!'),
        ('thickness_gt_zero', 'CHECK (thickness>0)',
         'The thickness must be > 0!'),
        ('pieces_gt_zero', 'CHECK (pieces>0)', 'The pieces must be > 0!'),
        ]

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------------ on_change...

    def on_change_input_id(self, cr, uid, ids, input_id):
        res = {}
        if input_id:
            obj_out = self.pool.get('tcv.mrp.resin.output')
            obj_uom = self.pool.get('product.uom')
            out_ids = obj_out.search(cr, uid, [('input_id', '=', input_id)])
            if input_id in out_ids:
                out_ids.remove(input_id)
            slabs = 0
            if out_ids:
                out_brw = self.browse(cr, uid, out_ids, context={})
                for o in out_brw:
                    slabs += o.pieces

            input = self.pool.get('tcv.mrp.resin.inputs').browse(
                cr, uid, input_id, context=None)
            res = {'value': {}}
            res['value'].update({'product_id': input.product_id.id,
                                 'length': input.length,
                                 'heigth': input.heigth,
                                 'pieces': input.pieces - slabs,
                                 'thickness': input.thickness,
                                 'total_area': obj_uom._calc_area(
                                     input.pieces - slabs,
                                     input.length,
                                     input.heigth)
                                 })
        return res

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_mrp_resin_output()

##--------------------------------------------------------- tcv_mrp_resin_costs


class tcv_mrp_resin_costs(osv.osv):

    _name = 'tcv.mrp.resin.costs'

    _inherit = 'tcv.mrp.basic.task.costs'

    _description = 'Calc resin costs'

    ##-------------------------------------------------------------------------

    ##--------------------------------------------------------- function fields

    _columns = {
        'task_id': fields.many2one(
            'tcv.mrp.resin', 'costs', required=True, ondelete='cascade'),
        'output_id': fields.many2one(
            'tcv.mrp.resin.output', 'Output product',
            readonly=True, ondelete='cascade'),
        'total_area': fields.float(
            'Area (m2)', digits_compute=dp.get_precision('Product UoM'),
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

tcv_mrp_resin_costs()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
