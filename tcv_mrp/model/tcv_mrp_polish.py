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

##-------------------------------------------------------------- tcv_mrp_polish


class tcv_mrp_polish(osv.osv):

    _name = 'tcv.mrp.polish'

    _inherit = 'tcv.mrp.basic.task'

    _description = 'Handle polisher operation data'

    def _template_params(self):
        res = super(tcv_mrp_polish, self)._template_params()
        res.extend([{'sequence': 30,
                     'name': 'abrasive_durability_table',
                     'type': 'char',
                     'help': _('The code for the duration table of ' +
                               'abrasives used for the calculation')},
                    {'sequence': 130,
                     'name': 'account_abrasive_cost',
                     'type': 'account',
                     'help': _(
                         'Account for the cost of the abrasive applied')},
                    ])
        return res

    def _account_move_settings(self):
        res = super(tcv_mrp_polish, self)._account_move_settings()
        res.update({'abrasive_cost': {'name': _('Abrasive used'),
                    'isproduct': True}})
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
            'tcv.mrp.polish.inputs', 'task_id', 'String', readonly=True,
            states={'draft': [('readonly', False)]}),
        'output_ids': fields.one2many(
            'tcv.mrp.polish.output', 'task_id', 'Output data', readonly=True,
            states={'draft': [('readonly', False)]}),
        'costs_ids': fields.one2many(
            'tcv.mrp.polish.costs', 'task_id', 'Output data', readonly=True),
        'stops_ids': fields.one2many(
            'tcv.mrp.polish.stops', 'task_id', 'Stop issues', readonly=False,
            context={'stop_type_domain': [('type', '=', 'polish')]}),
        'ad_table': fields.many2one(
            'tcv.mrp.abrasive.durability', 'Durability table',
            ondelete='restrict', readonly=True,
            help="Abrasive durability table used"),
        'price_m2': fields.float(
            'm2 cost', digits_compute=dp.get_precision('Account'),
            readonly=True, help="Estimated cost per m2, " +
            "taken from the table set in the template " +
            "(abrasive_durability_table)"),
        }

    _defaults = {}

    _sql_constraints = []

    ##-------------------------------------------------------------------------

    def _calc_supplies_operator_factory_cost(
            self, cr, uid, ids, output, supplies_ids, output_area,
            round_to, context=None):
        so_brw = self.browse(cr, uid, ids, context={})[0]
        #~ supplies_cost = round((so_brw.supplies_cost * output.total_area) /
        #~ output_area,round_to)
        supplies_cost = 0
        if so_brw.date_end >= self._change_method_date:
            values = self._compute_cost_by_m2(cr, uid, so_brw,
                                              output_area, round_to)
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
        so_brw = self.browse(cr, uid, ids, context={})
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
                abrasive_cost = round(item.price_m2 * output.total_area,
                                      round_to)
                line = {'output_id': output.id,
                        'cumulative_cost': cumulative_cost,
                        'abrasive_cost': abrasive_cost,
                        #~ 'supplies_cost':supplies_cost,
                        'operator_cost': operator_cost,
                        'factory_overhead': factory_overhead,
                        'total_area': output.total_area,
                        }
                #~ line.update({'total_cost':cumulative_cost+abrasive_cost +
                #~ supplies_cost+operator_cost + factory_overhead})
                line.update({'total_cost': cumulative_cost + abrasive_cost +
                             operator_cost + factory_overhead})
                line.update({'real_unit_cost': line['total_cost'] /
                             line['total_area']})
                lines.append((0, 0, line))
            if lines:
                self.write(cr, uid, item.id, {
                    'costs_ids': lines, 'valid_cost': True}, context)
                self.save_output_products(cr, uid, ids, context)
        return True

    def load_default_values(self, cr, uid, parent_id, context=None):
        '''
        If required, here you can create here a new task with any default data
        this method must be overriden in inherited models
        '''
        res = super(tcv_mrp_polish, self).load_default_values(
            cr, uid, parent_id, context)

        obj_spr = self.pool.get('tcv.mrp.subprocess')
        obj_abr = self.pool.get('tcv.mrp.abrasive.durability')
        obj_tmp = self.pool.get('tcv.mrp.template')

        subp = obj_spr.browse(cr, uid, parent_id, context=context)

        input_list = []
        if subp.prior_id:
            model = subp.prior_id.template_id.output_model.name
            obj_pri = self.pool.get(model)
            output_ids = obj_pri.search(
                cr, uid, [('subprocess_ref', '=', subp.prior_id.id),
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
        if not input_list:
            raise osv.except_osv(_('Error!'), _('No outputs to be processed'))

        price_m2 = 0
        abrasive_ref = obj_tmp.get_var_value(
            cr, uid, subp.template_id.id, 'abrasive_durability_table')
        if abrasive_ref:
            abr_id = obj_abr.search(cr, uid, [('ref', '=', abrasive_ref)])
            if abr_id:
                ad_table = abr_id[0]
                price_m2 = obj_abr._get_total_cost_m2(
                    cr, uid, ad_table, context)

        if input_list:
            res.update({'default_ad_table': ad_table,
                        'default_price_m2': price_m2,
                        'default_input_ids': input_list})

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

    def _get_settings_acc_cost_id(self, cr, uid, cost_name, cost_line, task):
        if cost_name == 'abrasive_cost':
            if task.ad_table:
                return task.ad_table.categ_id.property_account_expense_categ.id
        return super(tcv_mrp_polish, self).\
            _get_settings_acc_cost_id(cr, uid, cost_name, cost_line, task)

    def get_task_input_sumary(self, cr, uid, ids_str, context=None):
        sql = """
        select sum(i.pieces) pieces, sum(i.pieces*heigth*length) as qty
        from tcv_mrp_polish_inputs i
        left join tcv_mrp_io_slab s on i.output_id = s.id
        where task_id in %s
        """ % ids_str
        cr.execute(sql)
        return cr.dictfetchone()

    def get_task_output_sumary(self, cr, uid, ids_str, context=None):
        sql = """
        select sum(pieces) pieces, sum(pieces*heigth*length) as qty
        from tcv_mrp_polish_output
        where task_id in %s
        """ % ids_str
        cr.execute(sql)
        return cr.dictfetchone()

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_mrp_polish()

##------------------------------------------------------- tcv_mrp_polish_inputs


class tcv_mrp_polish_inputs(osv.osv):

    _name = 'tcv.mrp.polish.inputs'

    _description = 'Calc polish inputs'

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
            'tcv.mrp.polish', 'inputs', required=True, ondelete='cascade'),
        'output_id': fields.many2one(
            'tcv.mrp.io.slab', 'inputs', required=True,
            ondelete='restrict', readonly=False),
        'product_id': fields.related(
            'output_id', 'product_id', type='many2one',
            relation='product.product', string='Product',
            store=False, readonly=True),
        'prod_lot_ref': fields.function(
            _compute_all, method=True,
            type='char', string='Lot reference', multi='all'),
        'pieces': fields.integer(
            'slabs'),
        'available_pcs': fields.function(
            _compute_all, method=True, type='integer',
            string='Availables pcs', multi='all'),
        'length': fields.function(
            _compute_all, method=True, type='float', string='Length (m)',
            digits_compute=dp.get_precision('Extra UOM data'), multi='all'),
        'heigth': fields.function(
            _compute_all, method=True, type='float',
            string='Heigth (m)', digits_compute=dp.get_precision
            ('Extra UOM data'), multi='all'),
        'thickness': fields.function(
            _compute_all, method=True, type='integer', string='Thickness',
            multi='all'),
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

tcv_mrp_polish_inputs()

##------------------------------------------------------- tcv_mrp_polish_output


class tcv_mrp_polish_output(osv.osv):

    _name = 'tcv.mrp.polish.output'

    _description = ''

    ##-------------------------------------------------------------------------

    def name_get(self, cr, uid, ids, context):
        if not len(ids):
            return []
        res = []
        output = self.browse(cr, uid, ids, context)
        for o in output:
            res.append((o.id, '%s (%s) [%s - (%sx%s) (%smm)]' %
                       (o.product_id.name, o.input_id.prod_lot_ref,
                        o.pieces, o.length, o.heigth, o.thickness)))
        return res

    def default_get(self, cr, uid, fields, context=None):
        context = context or {}
        data = super(tcv_mrp_polish_output, self).default_get(cr, uid, fields,
                                                              context)
        input_ids = context.get('input_ids')
        output_ids = context.get('output_ids')
        if input_ids:
            inp = input_ids[0]
            ext = inp[2]
            ext.update({'input_id': inp[1]})
            ext.pop('output_id')
            if output_ids:
                used_pcs = 0
                for item in output_ids:
                    used_pcs += item[2].get('pieces', 0)
                pcs = ext['pieces'] - used_pcs
                if pcs < 0:
                    pcs = 0
                ext.update({'pieces': pcs,
                            'length': output_ids[-1][2].get('length'),
                            'heigth': output_ids[-1][2].get('heigth'),
                            })
            data.update(ext)
        return data

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
            'tcv.mrp.polish', 'Blocks', required=True, ondelete='cascade'),
        'input_id': fields.many2one(
            'tcv.mrp.polish.inputs', 'Origin', required=True,
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
            'Thickness (mm)', help="The product thickness, " +
            "correction value for volume calculation assigned in template: " +
            " thickness_factor_correction"),
        'total_area': fields.function(
            _compute_area, method=True, type='float', string='Area (m2)',
            digits_compute=dp.get_precision('Product UoM')),
        }

    _defaults = {
        }

    _sql_constraints = [
        ('length_gt_zero', 'CHECK (length between 0.5 and 4)',
         'The length must be 0.5-4!'),
        ('heigth_gt_zero', 'CHECK (heigth between 0.5 and 4)',
         'The heigth must be 0.5-4!'),
        ('thickness_gt_zero', 'CHECK (thickness>0)',
         'The thickness must be > 0!'),
        ('pieces_gt_zero', 'CHECK (pieces>0)',
         'The pieces must be > 0!'),
        ]

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------------ on_change...

    def on_change_input_id(self, cr, uid, ids, input_id):
        res = {}
        if input_id:
            obj_out = self.pool.get('tcv.mrp.polish.output')
            obj_uom = self.pool.get('product.uom')
            out_ids = obj_out.search(cr, uid, [('input_id', '=', input_id)])
            if input_id in out_ids:
                out_ids.remove(input_id)
            slabs = 0
            for o in self.browse(cr, uid, out_ids, context={}):
                slabs += o.pieces

            input = self.pool.get('tcv.mrp.polish.inputs').browse(
                cr, uid, input_id, context=None)
            res = {'value': {}}
            res['value'].update({'product_id': input.product_id.id,
                                 'length': input.length,
                                 'heigth': input.heigth,
                                 'pieces': input.pieces - slabs,
                                 'thickness': input.thickness,
                                 'total_area': obj_uom.
                                _calc_area(input.pieces - slabs,
                                           input.length, input.heigth)
                                 })
        return res

    def on_change_size(self, cr, uid, ids, pieces, length, heigth):
        obj_uom = self.pool.get('product.uom')
        length, heigth = obj_uom.adjust_sizes(length, heigth)
        return {'value': {'length': length,
                          'heigth': heigth,
                          'total_area': obj_uom._calc_area(pieces,
                                                           length, heigth)}}

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_mrp_polish_output()

##-------------------------------------------------------- tcv_mrp_polish_costs

##--------------------------------------------------------- tcv_mrp_resin_costs


class tcv_mrp_polish_costs(osv.osv):

    _name = 'tcv.mrp.polish.costs'

    _inherit = 'tcv.mrp.basic.task.costs'

    _description = 'Calc polish costs'

    ##-------------------------------------------------------------------------

    ##--------------------------------------------------------- function fields

    _columns = {
        'task_id': fields.many2one(
            'tcv.mrp.polish', 'costs', required=True, ondelete='cascade'),
        'output_id': fields.many2one(
            'tcv.mrp.polish.output', 'Output product',
            readonly=True, ondelete='cascade'),
        'abrasive_cost': fields.float(
            'Abrasive cost', digits_compute=dp.get_precision('Account'),
            readonly=True, help="Direct cost of Abrasive"),
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

tcv_mrp_polish_costs()

##------------------------------------------------------- tcv_mrp_gangsaw_stops


class tcv_mrp_polish_stops(osv.osv):

    _name = 'tcv.mrp.polish.stops'

    _inherit = 'tcv.mrp.basic.task.stops'

    _columns = {
        'task_id': fields.many2one(
            'tcv.mrp.polish', 'Stop issues', required=True,
            ondelete='cascade'),
        }

tcv_mrp_polish_stops()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
