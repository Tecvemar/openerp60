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

##------------------------------------------------------------- tcv_mrp_gangsaw


class tcv_mrp_gangsaw(osv.osv):

    _name = 'tcv.mrp.gangsaw'

    _inherit = 'tcv.mrp.basic.task'

    _description = ''

    def _template_params(self):
        res = super(tcv_mrp_gangsaw, self)._template_params()
        res.extend([
            {'sequence': 30, 'name': 'default_blade_product', 'type': 'char',
                'help': 'Código del producto "cuchilla"',
                'char_val': 'CUACFC60S'},
            {'sequence': 40, 'name': 'default_steel_grit_product',
                'type': 'char', 'help': 'Código del producto "granalla"',
                'char_val': 'GRISSC25'},
            {'sequence': 50, 'name': 'default_lime_product', 'type': 'char',
                'help': 'Código del producto "cal"'},
            {'sequence': 60, 'name': 'thickness_factor_correction',
                'type': 'float', 'help': 'Para ajustar el volumen consumido ' +
                ' por la cuchilla en el proceso de corte, en mm ',
                'float_val': 8},
            {'sequence': 70, 'name': 'blade_unit_weight', 'type': 'float',
                'help': 'Peso NETO de una cuchilla (en Kg)'},
            {'sequence': 80, 'name': 'blade_useful_height', 'type': 'float',
                'help': 'Alto "útil" de las cuchillas', 'float_val': 7.5},
            {'sequence': 130, 'name': 'account_blade_cost', 'type': 'account',
                'help': _('Account for the cost of the blade applied')},
            {'sequence': 140, 'name': 'new_blade_heigth', 'type': 'float',
                'help': _('Heigth for new blade'), 'float_val': 10},
            {'sequence': 150, 'name': 'ref_name', 'type': 'char',
                'help': _('Default name for process')},
            {'sequence': 160, 'name': 'valid_thickness', 'type': 'char',
                'help': _('List of valid thickness. Ex.: 15,20,30 ' +
                          '(comma separated)'), 'char_val': '15, 20, 30'},
            {'sequence': 170, 'name': 'block_flanks', 'type': 'float',
                'help': _('Recomended size for process lateral flanks (cm)'),
                'float_val': 5},
            ])
        return res

    def _account_move_settings(self):
        res = super(tcv_mrp_gangsaw, self)._account_move_settings()
        res.update({'blade_cost': {'name': _('Blade used'),
                                   'isproduct': True}})
        return res

    ##-------------------------------------------------------------------------

    def _get_task_info(self, cr, uid, obj_task, context=None):
        res = ''
        for bl in obj_task.gangsaw_ids:
            block_ref = ' (%s)' % bl.block_ref if bl.block_ref else ''
            block = '[%s] %s%s' % (bl.product_id.default_code,
                                   bl.prod_lot_id.name, block_ref)
            res = '%s, %s' % (res, block) if res else block
        return res[:128]

    def name_get(self, cr, uid, ids, context):
        if not len(ids):
            return []
        res = []
        so_brw = self.browse(cr, uid, ids, context)
        for item in so_brw:
            res.append((item.id, '%s' % (item.parent_id.template_id.name)))
        return res

    ##--------------------------------------------------------- function fields

    _columns = {
        'supplies_ids': fields.one2many(
            'tcv.mrp.gangsaw.supplies', 'task_id', 'Supplies', readonly=True,
            states={'draft': [('readonly', False)]}),
        'gangsaw_ids': fields.one2many(
            'tcv.mrp.gangsaw.blocks', 'gangsaw_id', 'Blocks data',
            readonly=True, states={'draft': [('readonly', False)]}),
        'output_ids': fields.one2many(
            'tcv.mrp.gangsaw.output', 'gangsaw_id', 'Output data',
            readonly=True, states={'draft': [('readonly', False)]}),
        'costs_ids': fields.one2many(
            'tcv.mrp.gangsaw.costs', 'task_id', 'Output data', readonly=True),
        'stops_ids': fields.one2many(
            'tcv.mrp.gangsaw.stops', 'task_id', 'Stop issues', readonly=False,
            context={'stop_type_domain': [('type', '=', 'gangsaw')]}),
        }

    _defaults = {
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    def _get_block_cost(self, cr, uid, prod_lot_id, product_id, round_to,
                        context=None):
        context = context or {}
        obj_cst = self.pool.get('tcv.cost.management')
        context.update({'property_cost_price_only': True})
        price = obj_cst.get_tcv_cost(cr, uid, prod_lot_id, None, context)
        if not price:
            raise osv.except_osv(_('Error!'), _('Can\'t find block cost! (%s)')
                                 % context.get('block_name', ''))
        return price

    def _calc_block_cost(self, cr, uid, ids, block_id, product_id, totals,
                         round_to, context=None):
        '''
        This method determines the cost of the block applicable to manufactured
        product, for it builds on the net cost of the block (batch) and the
        net volume of material produced and total cost is applied to the
        volume Proportioning

        Este metodo determina el costo del bloque aplicable al producto
        manufacturado, para ello toma como base el costo neto del bloque (lote)
        y el volumen neto y total del material producido aplicando el costo
        de forma proporcinal al volumen
        '''
        block_unit_cost = self._get_block_cost(
            cr, uid, totals[block_id]['prod_lot_id'],
            totals[block_id]['product_id'], round_to, context)
        block_volume = totals[block_id]['block_volume']
        context.update({'block_volume': block_volume})
        block_cost = round((block_volume * block_unit_cost), round_to)
        return block_cost

    def _calc_blade_cost(self, cr, uid, ids, block_id, product_id, totals,
                         round_to, context=None):
        '''
        Use the parameter blade_unit_weight to calculate the relative
        weight of blade used

            blade_unit_weight(kg) ----> blade_useful_height(cm)
                    X(kg)         ----> 1 cm

        This method determines the cost of the manufactured product applicable
        to blades, it takes as a basis for the cost per cm of blade and the
        total consumed cm blade, to distribute in proportion to the volume of
        consumed block

        Este metodo determina el costo de las cuchillas aplicable al producto
        manufacturado, para ello toma como base el costo por cm de cuchilla,
        los cm consumidos y el total de cuchillas, para distribuirlo de forma
        proporcional al volumen del bloque consumido
        '''
        obj_tmp = self.pool.get('tcv.mrp.template')
        obj_cst = self.pool.get('tcv.cost.management')
        so_brw = self.browse(cr, uid, ids, context={})[0]
        blade_unit_weight = obj_tmp.get_var_value(
            cr, uid, so_brw.parent_id.template_id.id, 'blade_unit_weight') or 0
        blade_useful_height = obj_tmp.get_var_value(
            cr, uid, so_brw.parent_id.template_id.id,
            'blade_useful_height') or 0
        unit_weight = (blade_unit_weight * totals[block_id]['blade_cm']) / \
            blade_useful_height if blade_useful_height else 0
        total_weight = unit_weight * totals[block_id]['blade_qty']
        # tomar el costo por kg del lote de cuchillas
        #~ blade_lot_unit_cost = 5758.56 / 1000 # segun expediente LGR-3831

        blade_lot_unit_cost = obj_cst.get_tcv_cost(
            cr, uid, None, totals[block_id]['blade_id'], context)
        total_blade_cost = total_weight * blade_lot_unit_cost
        # determinar el costo por lamina
        slab_count = totals[block_id]['slab_count']
        blade_unit_cost = total_blade_cost / slab_count
        pieces = totals[block_id]['slabs'][product_id]['pieces']
        blade_cost = round(blade_unit_cost * pieces, round_to)
        return round(blade_cost, round_to)

    def _calc_supplies_operator_factory_cost(
            self, cr, uid, ids, block_id, product_id, supplies_ids,
            totals, round_to, context=None):
        slabs_area = totals[block_id]['slabs'][product_id]['slabs_area']
        total_area = totals['total_area']
        so_brw = self.browse(cr, uid, ids, context={})[0]
        supplies_cost = round((
            so_brw.supplies_cost * slabs_area) / total_area, round_to)
        if so_brw.date_end >= self._change_method_date:
            values = self._compute_cost_by_m2(
                cr, uid, so_brw, slabs_area, round_to)
            operator_cost = values.get('operator_cost_m2', 0)
            factory_overhead = values.get('factory_overhead_m2', 0)
        else:
            operator_cost = round((self._compute_operator_cost(
                so_brw, round_to) * slabs_area) / total_area, round_to)
            factory_overhead = round((
                self._compute_factory_overhead(so_brw, round_to) *
                slabs_area) / total_area, round_to)
        return supplies_cost, operator_cost, factory_overhead

    def cost_distribution(self, cr, uid, ids, context=None):
        context = context or {}
        so_brw = self.browse(cr, uid, ids, context={})
        obj_tmp = self.pool.get('tcv.mrp.template')
        round_to = 2
        for item in so_brw:
            self._clear_previous_cost_distribution(cr, uid, item, context)
            totals = {}
            thickness_factor_correction = obj_tmp.get_var_value(
                cr, uid, item.parent_id.template_id.id,
                'thickness_factor_correction') or 0
            for block in item.gangsaw_ids:
                totals.update({block.id:
                              {'prod_lot_id': block.prod_lot_id.id,
                               'product_id': block.product_id.id,
                               'blade_id': block.blade_id.id,
                               'blade_qty': block.blade_qty,
                               'blade_cm': block.blade_start - block.blade_end,
                               'slabs': {},
                               'slab_count': 0,
                               'total_vol': 0.0,
                               'block_volume': block.prod_lot_id.lot_factor},
                               'total_area': 0.0})
            for product in item.output_ids:
                block_id = product.block_id.id
                real_thickness = product.thickness + \
                    thickness_factor_correction
                volume = product.total_area * real_thickness
                totals[block_id]['slabs'].update({product.id: {
                    'output_id': product.id,
                    'length': product.length,
                    'heigth': product.heigth,
                    'pieces': product.pieces,
                    'thickness': product.thickness,
                    'slabs_area': product.total_area,
                    'volume': volume, }})
                totals[block_id]['total_vol'] += volume
                totals['total_area'] += product.total_area
                totals[block_id]['slab_count'] += product.pieces
            lines = []
            for product in item.output_ids:
                product_id = product.id
                block_id = product.block_id.id
                supplies_cost, operator_cost, factory_overhead = \
                    self._calc_supplies_operator_factory_cost(
                        cr, uid, ids, block_id, product_id, item.supplies_ids,
                        totals, round_to, context)
                context.update({
                    'block_volume': product.block_id.lot_factor,
                    'block_name': product.block_id.prod_lot_id.name})
                line = {'output_id': product_id,
                        'block_cost': self._calc_block_cost(
                            cr, uid, ids, block_id, product_id, totals,
                            round_to, context),
                        'blade_cost': self._calc_blade_cost(
                            cr, uid, ids, block_id, product_id, totals,
                            round_to, context),
                        'supplies_cost': supplies_cost,
                        'operator_cost': operator_cost,
                        'factory_overhead': factory_overhead,
                        'total_area': totals[block_id]['slabs'][product_id]
                        ['slabs_area'],
                        }
                total_cost = round(line['block_cost'] + line['blade_cost'] +
                                   line['supplies_cost'] +
                                   line['operator_cost'] +
                                   line['factory_overhead'], round_to)
                line.update({'total_cost': total_cost})
                line.update({'real_unit_cost': line['total_cost'] /
                             line['total_area']})
                lines.append((0, 0, line))

            if lines:
                self.write(cr, uid, item.id, {'costs_ids': lines,
                                              'valid_cost': True}, context)
                self.save_output_products(cr, uid, ids, context)
        return True

    def process_all_input(self, cr, uid, ids, context=None):
        '''
        Send all input data to output valid for input = io.slab
        '''
        output_ids = []
        obj_prd = self.pool.get('product.product')
        for item in self.browse(cr, uid, ids, context):
            for line in item.gangsaw_ids:
                code = '%sPROC' % line.product_id.default_code[:6]
                prod_id = obj_prd.search(cr, uid, [(
                    'default_code', '=', code)])
                if prod_id:
                    p_id = prod_id[0]
                else:
                    p_id = line.product_id.id
                output_ids.append((0, 0, {'block_id': line.id,
                                          'product_id': p_id,
                                          'pieces': line.slab_qty,
                                          'length': line.net_length,
                                          'heigth': line.net_heigth,
                                          'thickness': line.thickness,
                                          }))
            if output_ids:
                self.write(cr, uid, item.id, {'output_ids': output_ids},
                           context)
        return True

    def load_default_values(self, cr, uid, parent_id, context=None):
        '''
        If required, here you can create here a new task with any default data
        this method must be overriden in inherited models
        '''
        res = super(tcv_mrp_gangsaw, self).load_default_values(
            cr, uid, parent_id, context)

        obj_spr = self.pool.get('tcv.mrp.subprocess')
        obj_tmp = self.pool.get('tcv.mrp.template')
        subp = obj_spr.browse(cr, uid, parent_id, context=context)
        product_list = []

        # default_steel_grit_product (granalla)
        product = obj_tmp.get_var_value(
            cr, uid, subp.template_id.id, 'default_steel_grit_product')
        if product:
            product_id = self.pool.get('product.product').search(
                cr, uid, [('default_code', '=', product)])
            product_list.append({'product_id': product_id[0]})

        # default_lime_product (cal)
        product = obj_tmp.get_var_value(
            cr, uid, subp.template_id.id, 'default_lime_product')
        if product:
            product_id = self.pool.get('product.product').search(
                cr, uid, [('default_code', '=', product)])
            product_list.append({'product_id': product_id[0]})

        if product_list:
            res.update({'default_supplies_ids': product_list})
        return res

    def get_output_data_line(self, item, line):
        product_id = line.output_id.product_id.id
        lot_prefix = line.output_id.block_id.product_id.lot_prefix
        if not lot_prefix:
            raise osv.except_osv(
                _('Error!'),
                _('Must indicate a lot prefix for %s product') %
                line.output_id.block_id.product_id.name)
        lot_name = line.output_id.block_id.prod_lot_id.name.split('-')
        if len(lot_name) == 1:
            lot_name = lot_name[0]
        else:
            lot_name = lot_name[1]
        lot_name = ('000000%s' % lot_name. strip())[- 6:]
        return {'task_ref': item.id,
                'subprocess_ref': item.parent_id.id,
                'cost_line': line.id,
                'type': 'output',
                'product_id': product_id,
                'prod_lot_ref': '%s%s' % (lot_prefix, lot_name),
                'thickness': line.output_id.thickness,
                'pieces': line.output_id.pieces,
                'length': line.output_id.length,
                'heigth': line.output_id.heigth,
                'total_area': line.total_area,
                'real_unit_cost': line.real_unit_cost,
                'total_cost': line.total_cost,
                }

    def _get_settings_acc_cost_id(self, cr, uid, cost_name, cost_line, task):
        if cost_name == 'blade_cost':
            obj_tmp = self.pool.get('tcv.mrp.template')
            default_blade_product = obj_tmp.get_var_value(
                cr, uid, task.parent_id.template_id.id,
                'default_blade_product') or 0
            if default_blade_product:
                obj_prd = self.pool.get('product.product')
                blade_prd_id = obj_prd.search(
                    cr, uid, [('default_code', '=', default_blade_product)])
                if blade_prd_id:
                    blade = obj_prd.browse(
                        cr, uid, blade_prd_id[0], context={})
                    return blade.property_account_expense.id or \
                        blade.categ_id.property_account_expense_categ.id
        return super(tcv_mrp_gangsaw, self).\
            _get_settings_acc_cost_id(cr, uid, cost_name, cost_line, task)

    def _create_model_account_move_lines(self, cr, uid, task, lines, context):
        '''
        Must be overridden in models inherited
        Here you create and return a acount.move.lines (list of dict)
        task is a task.browse object
        return a sum of created lines amounts
        '''
        total_amount = 0.0
        round_to = 2
        name = context.get('move_name', '')
        company_id = context.get('move_company_id', 'Error')
        for block in task.gangsaw_ids:
            account_id = block.product_id.property_stock_account_output.id or \
                block.product_id.categ_id.property_stock_account_output_categ.id
            acc_cost_id = block.product_id.property_account_expense.id or \
                block.product_id.categ_id.property_account_expense_categ.id
            if not account_id:
                raise osv.except_osv(_('Error!'), _(
                    'No block account found, please check product and ' +
                    ' category account settings (%s)') % block.product_id.name)
            context.update({'block_volume': block.lot_factor,
                            'block_name': block.prod_lot_id.name})
            block_unit_cost = self._get_block_cost(
                cr, uid, block.prod_lot_id.id, block.product_id.id,
                round_to, context)
            block_cost = round((
                block.prod_lot_id.lot_factor * block_unit_cost), round_to)
            total_amount += block_cost
            # Block stock vs block cost
            lines.append(self._gen_account_move_line(
                company_id, account_id, _('%s %s %s') %
                (block.product_id.name, block.prod_lot_id.name, name),
                0.0, block_cost))
            lines.append(self._gen_account_move_line(
                company_id, acc_cost_id, _('%s %s %s') %
                (block.product_id.name, block.prod_lot_id.name, name),
                block_cost, 0.0))

        return total_amount

    def _create_model_stock_move_lines(self, cr, uid, task, lines,
                                       context=None):
        obj_lot = self.pool.get('stock.production.lot')
        obj_tmp = self.pool.get('tcv.mrp.template')
        obj_prd = self.pool.get('product.product')
        new_blade_heigth = obj_tmp.get_var_value(
            cr, uid, task.parent_id.template_id.id, 'new_blade_heigth') or 0
        blade_unit_weight = obj_tmp.get_var_value(
            cr, uid, task.parent_id.template_id.id, 'blade_unit_weight') or 0
        default_blade_product = obj_tmp.get_var_value(
            cr, uid, task.parent_id.template_id.id,
            'default_blade_product') or 0
        blade_prd_id = obj_prd.search(
            cr, uid, [('default_code', '=', default_blade_product)])
        if blade_prd_id:
            blade_prd = obj_prd.browse(
                cr, uid, blade_prd_id[0], context=context)
        for block in task.gangsaw_ids:
            if block.prod_lot_id:
                location_id = obj_lot.get_actual_lot_location(
                    cr, uid, block.prod_lot_id.id, context)
            if not location_id:
                raise osv.except_osv(
                    _('Error!'),
                    _('Missign location for block (%s)') %
                    block.prod_lot_id.name)
            if location_id[0] != 3510:
                location = obj_lot.browse(
                    cr, uid, location_id[0], context=context)
                raise osv.except_osv(
                    _('Error!'),
                    _('Location for block (%s, %s) <> "Patio bloques"') %
                    (block.prod_lot_id.name, location.name))
            blck = {'product_id': block.product_id.id,
                    'name': context.get('task_name', ''),
                    'date': context.get('task_date'),
                    'location_id': location_id[0],
                    'location_dest_id': context.get(
                        'task_config').location_id.id,
                    'pieces_qty': 1,
                    'product_qty': block.lot_factor,
                    'product_uos_qty': block.lot_factor,
                    'product_uom': block.product_id.uom_id.id,
                    'prodlot_id': block.prod_lot_id.id,
                    'state': 'draft'}
            lines.append((0, 0, blck))
            if new_blade_heigth and blade_unit_weight and blade_prd and \
                    block.blade_start == new_blade_heigth:
                blade_qty = block.blade_qty * blade_unit_weight
                blade = {'product_id': blade_prd.id,
                         'name': context.get('task_name', ''),
                         'date': context.get('task_date'),
                         'location_id': location_id[0],
                         'location_dest_id': context.get(
                             'task_config').location_id.id,
                         'product_qty': blade_qty,
                         'product_uos_qty': blade_qty,
                         'product_uom': blade_prd.uom_id.id,
                         'state': 'draft'}
                lines.append((0, 0, blade))
        return lines

    def get_task_input_sumary(self, cr, uid, ids_str, context=None):
        sql = """
        select count(l.id) pieces, sum(l.heigth*l.length*l.width) as qty
        from tcv_mrp_gangsaw_blocks b
        left join tcv_mrp_gangsaw g on b.gangsaw_id = g.id
        left join stock_production_lot l on b.prod_lot_id = l.id
        where b.gangsaw_id in %s;
        """ % ids_str
        cr.execute(sql)
        return cr.dictfetchone()

    def get_task_output_sumary(self, cr, uid, ids_str, context=None):
        sql = """
        select sum(pieces) pieces, sum(pieces*heigth*length) as qty
        from tcv_mrp_gangsaw_output
        where gangsaw_id in %s
        """ % ids_str
        cr.execute(sql)
        return cr.dictfetchone()

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

    def test_done(self, cr, uid, ids, *args):
        res = super(tcv_mrp_gangsaw, self).test_done(cr, uid, ids, *args)
        if res:
            ids = isinstance(ids, (int, long)) and [ids] or ids
            obj_tmp = self.pool.get('tcv.mrp.template')
            for task in self.browse(cr, uid, ids, context={}):
                valid_thickness = obj_tmp.get_var_value(
                    cr, uid, task.parent_id.template_id.id,
                    'valid_thickness')
                if not valid_thickness:
                    raise osv.except_osv(
                        _('Error!'),
                        _('You must set a list of valid thickness ' +
                          'in template!'))
                vt = [int(x) for x in valid_thickness.split(',')]
                for block in task.gangsaw_ids:
                    if block.thickness not in vt:
                        raise osv.except_osv(
                            _('Error!'),
                            _('You must indicate a valid thickness ' +
                              'value for block (%s)!') % valid_thickness)
                for out in task.output_ids:
                    if out.thickness not in vt:
                        raise osv.except_osv(
                            _('Error!'),
                            _('You must indicate a valid thickness ' +
                              'value in outputs (%s)!') % valid_thickness)
                for sup in task.supplies_ids:
                    if sup.product_id.track_production and \
                            not sup.prod_lot_id:
                        raise osv.except_osv(
                            _('Error!'),
                            _('Must indicate a lot for %s') %
                            sup.product_id.name)
                    elif sup.prod_lot_id and \
                            sup.product_id.id != sup.prod_lot_id.product_id.id:
                        raise osv.except_osv(
                            _('Error!'),
                            _('Supplies product and lot\'s product must be ' +
                              'the same: %s <> %s') % (
                                sup.product_id.name,
                                sup.prod_lot_id.product_id.name))

        return True

tcv_mrp_gangsaw()

##------------------------------------------------------ tcv_mrp_gangsaw_blocks


class tcv_mrp_gangsaw_blocks(osv.osv):

    _name = 'tcv.mrp.gangsaw.blocks'

    _description = 'Handle gangsaw operation data'

    _rec_name = 'prod_lot_id'

    ##-------------------------------------------------------------------------

    def name_get(self, cr, uid, ids, context):
        if not len(ids):
            return []
        res = []
        blocks = self.browse(cr, uid, ids, context)
        for b in blocks:
            res.append((b.id, '%s - %s (%s)' %
                        (b.product_id.name, b.block_ref or '',
                         b.prod_lot_id.name)))
        return res

    ##--------------------------------------------------------- function fields

    def _calc_throwput(self, cr, uid, ids, name, arg, context=None):
        if context is None:
            context = {}
        if not len(ids):
            return []
        res = {}
        obj_uom = self.pool.get('product.uom')
        obj_tmp = self.pool.get('tcv.mrp.template')
        blade_unit_weight = 0
        for item in self.browse(cr, uid, ids, context={}):
            if not blade_unit_weight:
                blade_unit_weight = obj_tmp.get_var_value(
                    cr, uid, item.parent_id.template_id.id,
                    'blade_unit_weight') or 0
            res[item.id] = {}
            res[item.id]['estimated_area'] = obj_uom._compute_area_tile(
                cr, uid, item.slab_qty, item.net_length,
                item.net_heigth, context)
            res[item.id]['throwput'] = round(
                res[item.id]['estimated_area'] / item.lot_factor, 4)
            res[item.id]['blade_unit_weight'] = blade_unit_weight
            res[item.id]['blade_weight'] = item.blade_qty * blade_unit_weight
            res[item.id]['cut_down_feed'] = (
                item.net_heigth / item.gangsaw_id.run_time) * 1000

        return res

    _columns = {
        'gangsaw_id': fields.many2one(
            'tcv.mrp.gangsaw', 'Blocks', required=True, ondelete='cascade'),
        'parent_id': fields.related(
            'gangsaw_id', 'parent_id', type='many2one',
            relation='tcv.mrp.subprocess', string='Subprocess', store=False,
            readonly=True),
        'template_id': fields.related(
            'parent_id', 'template_id', type='many2one',
            relation='tcv.mrp.template', string='Task template', store=True,
            readonly=True),
        'date_start': fields.related(
            'gangsaw_id', 'date_start', type='datetime',
            string='Date started', store=False, readonly=True),
        'date_end': fields.related(
            'gangsaw_id', 'date_end', type='datetime', string='Date finished',
            store=False, readonly=True),
        'prod_lot_id': fields.many2one(
            'stock.production.lot', 'Block (lot Nº)', required=True),
        'block_ref': fields.char(
            'Block ref', size=8, required=True, readonly=False,
            help="Characters for internal block reference"),
        'product_id': fields.related(
            'prod_lot_id', 'product_id', type='many2one',
            relation='product.product', string='Block / Product',
            store=True, readonly=True),
        'lot_factor': fields.related(
            'prod_lot_id', 'lot_factor', type='float', string='Vol (m3)',
            store=False, digits_compute=dp.get_precision('Product UoM'),
            readonly=True),
        'length': fields.related(
            'prod_lot_id', 'length', type='float',
            string='Length', store=False,
            digits_compute=dp.get_precision('Extra UOM data'), readonly=True),
        'width': fields.related(
            'prod_lot_id', 'width', type='float', string='Width', store=False,
            digits_compute=dp.get_precision('Extra UOM data'), readonly=True),
        'heigth': fields.related(
            'prod_lot_id', 'heigth', type='float', string='Heigth',
            store=False, digits_compute=dp.get_precision('Extra UOM data'),
            readonly=True),
        'net_length': fields.float(
            'Net length (m)', digits_compute=dp.get_precision('Product UoM')),
        'net_heigth': fields.float(
            'Net heigth (m)', digits_compute=dp.get_precision('Product UoM')),
        'blade_id': fields.many2one(
            'product.product', 'Blade / Product', ondelete='restrict',
            required=True, help="The product (blade) used, using the factor " +
            "of the template: default_blade_product"),
        'blade_qty': fields.integer(
            'Blade qty', required=True),
        'blade_unit_weight': fields.function(
            _calc_throwput, method=True, type='float',
            string='Unit wheight', digits_compute=dp.get_precision
            ('Product UoM'), help="Blade's wheight ", multi='all'),
        'blade_weight': fields.function(
            _calc_throwput, method=True, type='float', string='Wheight',
            digits_compute=dp.get_precision('Product UoM'),
            help="Blade's total wheight ", multi='all'),
        'slab_qty': fields.integer('Slab qty', required=True),
        'blade_start': fields.float(
            'Blade init', help="Initial heigth of blade before process (cm)"),
        'blade_end': fields.float(
            'Blade end', help="Final heigth of blade after process (cm)"),
        'thickness': fields.integer('Thickness (mm)', required=True),
        'estimated_area': fields.function(
            _calc_throwput, method=True, type='float', string='Area (E)',
            digits_compute=dp.get_precision('Product UoM'),
            help="Estimated output area", multi='all'),
        'throwput': fields.function(
            _calc_throwput, method=True, type='float', string='Throwput (E)',
            digits_compute=dp.get_precision('Product UoM'),
            help="Estimated throwput", multi='all'),
        'cut_down_feed': fields.function(
            _calc_throwput, method=True, type='float',
            string='Cutting down feed', digits=(14, 1),
            help="Cutting down feed (mm/h)", multi='all'),
        }

    _defaults = {
        'blade_start': lambda *a: 10,
        'blade_end': lambda *a: 0,
        'thickness': lambda *a: 20,
        }

    _sql_constraints = [
        ('blade_qty_gt_1', 'CHECK (blade_qty>=2)',
         'The cuchillas quantity must be >= 2!'),
        ('slab_qty_gt_zero', 'CHECK (slab_qty>=0)',
         'The slab quantity must be >= 0!'),
        ('blade_qty_gt_slab_qty', 'CHECK (blade_qty>=slab_qty+1)',
         'The blabe quantity mus be greater than slab quantity'),
        ('blade_start_range', 'CHECK(blade_start between 1 and 10)',
         'The blade heigth start must be in 1-10 range!'),
        ('blade_end_gt_zero', 'CHECK (blade_end between 1 and 10)',
         'The blade heigth end must be in 1-10 range!'),
        ('blade_diff', 'CHECK (blade_start>blade_end)',
         'The blade heigth start must be > blade heigth end!'),
        ('net_length_gt_zero', 'CHECK (net_length between 0.5 and 4)',
         'The slab net length must be 0.5-4!'),
        ('net_heigth_gt_zero', 'CHECK (net_heigth between 0.5 and 4)',
         'The slab net heigth must be 0.5-4!'),
        ('thickness_gt_zero', 'CHECK (thickness>0)',
         'The slab thickness must be > 0!'),
        ('block_ref_unique', 'UNIQUE(block_ref)',
         'The Block ref must be unique!'),
        ('prod_lot_id_unique', 'UNIQUE(prod_lot_id)',
         'The block must be unique!'),
        ]

    ##-------------------------------------------------------------------------

    def default_get(self, cr, uid, fields, context=None):
        data = super(tcv_mrp_gangsaw_blocks, self).default_get(
            cr, uid, fields, context)
        task_data = context.get('task_data')
        if task_data:
            obj_spr = self.pool.get('tcv.mrp.subprocess')
            obj_tmp = self.pool.get('tcv.mrp.template')
            subp = obj_spr.browse(
                cr, uid, task_data['parent_id'], context=context)
            blade_prd = obj_tmp.get_var_value(
                cr, uid, subp.template_id.id, 'default_blade_product')
            if blade_prd:
                blade_id = self.pool.get('product.product').search(
                    cr, uid, [('default_code', '=', blade_prd)])
                if blade_id:
                    data.update({'blade_id': blade_id[0]})
        return data

    ##------------------------------------------------------------ on_change...

    def on_change_prod_lot(self, cr, uid, ids, prod_lot_id):
        res = {}
        if prod_lot_id:
            lot = self.pool.get('stock.production.lot').browse(
                cr, uid, prod_lot_id, context=None)
            res = {'value': {}}
            res['value'].update({'product_id': lot.product_id.id,
                                 'length': lot.length,
                                 'width': lot.width,
                                 'heigth': lot.heigth,
                                 'lot_factor': lot.lot_factor,
                                 'net_length': lot.length,
                                 'net_heigth': lot.heigth})
        return res

    def on_change_blade_qty(self, cr, uid, ids, blade_qty, slab_qty):
        res = {}
        if blade_qty and not slab_qty:
            res = {'value': {'slab_qty': blade_qty - 1}}
        if not blade_qty and slab_qty:
            res = {'value': {'blade_qty': slab_qty + 1}}
        return res

    def on_change_block_ref(self, cr, uid, ids, block_ref):
        res = {}
        if block_ref:
            res = {'value': {'block_ref': block_ref.upper()}}
        return res

    def on_change_size(self, cr, uid, ids, length, heigth):
        obj_uom = self.pool.get('product.uom')
        length, heigth = obj_uom.adjust_sizes(length, heigth)
        res = {'value': {'net_length': length,
                         'net_heigth': heigth,
                         }}
        return res

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_mrp_gangsaw_blocks()

##---------------------------------------------------- tcv_mrp_gangsaw_supplies


class tcv_mrp_gangsaw_supplies(osv.osv):

    _name = 'tcv.mrp.gangsaw.supplies'

    _inherit = 'tcv.mrp.basic.task.supplies'

    _columns = {
        'task_id': fields.many2one(
            'tcv.mrp.gangsaw', 'Supplies', required=True, ondelete='cascade'),
        }

tcv_mrp_gangsaw_supplies()

##------------------------------------------------------ tcv_mrp_gangsaw_output


class tcv_mrp_gangsaw_output(osv.osv):

    _name = 'tcv.mrp.gangsaw.output'

    _description = ''

    ##-------------------------------------------------------------------------

    def name_get(self, cr, uid, ids, context):
        if not len(ids):
            return []
        res = []
        output = self.browse(cr, uid, ids, context)
        for o in output:
            res.append((o.id, '%s (%s) [%s - (%sx%s) (%smm)]' %
                       (o.product_id.name, o.block_id.prod_lot_id.name,
                        o.pieces, o.length, o.heigth, o.thickness)))
        return res

    ##--------------------------------------------------------- function fields

    def _compute_area(self, cr, uid, ids, name, args, context=None):
        res = {}
        obj_uom = self.pool.get('product.uom')
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = obj_uom._calc_area(line.pieces, line.length,
                                              line.heigth)
        return res

    ##-------------------------------------------------------------------------

    _columns = {
        'gangsaw_id': fields.many2one(
            'tcv.mrp.gangsaw', 'Blocks', required=True, ondelete='cascade'),
        'block_id': fields.many2one(
            'tcv.mrp.gangsaw.blocks', 'Origin', required=True,
            ondelete='cascade'),
        'product_id': fields.many2one(
            'product.product', 'Product', ondelete='restrict',
            required=True, help="The output product"),
        'length': fields.float(
            'Length (m)', digits_compute=dp.get_precision('Extra UOM data')),
        'heigth': fields.float(
            'Heigth (m)', digits_compute=dp.get_precision('Extra UOM data')),
        'pieces': fields.integer('Slabs'),
        'thickness': fields.integer(
            'Thickness (mm)', help="The product thickness, correction value " +
            "for volume calculation assigned in template: " +
            "thickness_factor_correction"),
        'total_area': fields.function(
            _compute_area, method=True, type='float', string='Area (m2)',
            digits_compute=dp.get_precision('Product UoM')),
        'out_res_id': fields.many2one(
            'tcv.mrp.output.result', 'Result', readonly=False, required=False,
            ondelete='restrict'),
        }

    _defaults = {
        'thickness': lambda *a: 20,
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

    def on_change_block_id(self, cr, uid, ids, block_id):
        res = {}
        if block_id:
            obj_out = self.pool.get('tcv.mrp.gangsaw.output')
            obj_uom = self.pool.get('product.uom')
            out_ids = obj_out.search(cr, uid, [('block_id', '=', block_id)])
            if block_id in out_ids:
                out_ids.remove(block_id)
            slabs = 0
            if out_ids:
                out_brw = self.browse(cr, uid, out_ids, context={})
                for o in out_brw:
                    slabs += o.pieces

            block = self.pool.get('tcv.mrp.gangsaw.blocks').browse(
                cr, uid, block_id, context=None)
            res = {'value': {}}
            res['value'].update({'length': block.prod_lot_id.length,
                                 'heigth': block.prod_lot_id.heigth,
                                 'net_length': block.prod_lot_id.length,
                                 'net_heigth': block.prod_lot_id.heigth,
                                 'pieces': block.slab_qty - slabs,
                                 'total_area': obj_uom._calc_area(
                                     block.slab_qty - slabs,
                                     block.prod_lot_id.length,
                                     block.prod_lot_id.heigth)
                                 })
        return res

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_mrp_gangsaw_output()

##------------------------------------------------------- tcv_mrp_gangsaw_costs


class tcv_mrp_gangsaw_costs(osv.osv):

    _name = 'tcv.mrp.gangsaw.costs'

    _inherit = 'tcv.mrp.basic.task.costs'

    _description = 'Calc gangsaw costs'

    ##-------------------------------------------------------------------------

    ##--------------------------------------------------------- function fields

    _columns = {
        'task_id': fields.many2one(
            'tcv.mrp.gangsaw', 'costs', required=True, ondelete='cascade'),
        'output_id': fields.many2one(
            'tcv.mrp.gangsaw.output', 'Output product',
            readonly=True, ondelete='cascade'),
        'block_cost': fields.float(
            'Block cost', digits_compute=dp.get_precision('Account'),
            readonly=True, help="Direct cost of processing block, " +
            "distributed according to the relative volume"),
        'blade_cost': fields.float(
            'Blade cost', digits_compute=dp.get_precision('Account'),
            readonly=True, help="Blade cost consumed (by conversion of cm " +
            "to kg), using the parameters of the template: " +
            "blade_unit_weight & blade_useful_height"),
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

tcv_mrp_gangsaw_costs()

##------------------------------------------------------- tcv_mrp_gangsaw_stops


class tcv_mrp_gangsaw_stops(osv.osv):

    _name = 'tcv.mrp.gangsaw.stops'

    _inherit = 'tcv.mrp.basic.task.stops'

    _columns = {
        'task_id': fields.many2one(
            'tcv.mrp.gangsaw', 'Gangsaw', required=True,
            ondelete='cascade'),
        }

tcv_mrp_gangsaw_stops()

##--------------------------------------------- tcv_mrp_gangsaw_supplies_detail


class tcv_mrp_gangsaw_supplies_detail(osv.osv):

    _name = 'tcv.mrp.gangsaw.supplies.detail'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'task_id': fields.many2one(
            'tcv.mrp.gangsaw', 'Gangsaw', required=True,
            ondelete='cascade'),
        'product_id': fields.many2one(
            'product.product', 'Product', ondelete='restrict'),
        'block_id': fields.many2one(
            'tcv.mrp.gangsaw.blocks', 'Block', ondelete='cascade'),
        'throwput': fields.float(
            'Throwput (E)', digits_compute=dp.get_precision('Product UoM')),
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

tcv_mrp_gangsaw_supplies_detail()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
