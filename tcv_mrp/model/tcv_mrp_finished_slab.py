# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date: 31/10/2012
#    Version: 0.0.0.0
#
#    Description:
#
#
##############################################################################
from datetime import datetime
from dateutil.relativedelta import relativedelta
from osv import fields, osv
from tools.translate import _
#~ import pooler
import decimal_precision as dp
import time
#~ import netsvc
#~ import csv
import unicodedata


##------------------------------------------------------- tcv_mrp_finished_slab


class tcv_mrp_finished_slab(osv.osv):

    _name = 'tcv.mrp.finished.slab'

    _inherit = 'tcv.mrp.finished.base'

    ##-------------------------------------------------------------------------

    def _get_task_info(self, cr, uid, obj_task, context=None):
        res = ''
        dict = {}
        for out in obj_task.output_ids:
            key = out.product_id.default_code
            if dict.get(key):
                dict[key].append(out.prod_lot_ref)
            else:
                dict[key] = [out.prod_lot_ref]
        for k in dict:
            dict[k].sort()
            next_lot = 0
            list = []
            sep = ''
            for ref in dict[k]:
                int_ref = int(ref)
                if next_lot != int_ref:
                    list.append(ref)
                    sep = '...'
                else:
                    if sep:
                        list.extend([sep, ref, ', '])
                        sep = ''
                    else:
                        list[-2] = ref[-2:]
                next_lot = int_ref + 1
            if list:
                if len(list) > 1:
                    list.pop(-1)
                r = '[%s] %s' % (k, ''.join(list))
                res = '%s | %s' % (res, r) if res else r
        return res[:128]

    def _compute_average_cost(self, cr, uid, ids, context=None):
        '''
        This method compute the average cost for outputs
        and set same unit cost for all lots (in this task)
        before create lots
        '''
        ids = isinstance(ids, (int, long)) and [ids] or ids
        total_cost = total_area = 0
        roundto = 2
        obj_out = self.pool.get('tcv.mrp.finished.slab.output')
        for item in self.browse(cr, uid, ids, context={}):
            for line in item.input_ids:
                total_cost += line.total_cost
            for line in item.output_ids:
                total_area += line.total_area
            average_cost = round(total_cost / total_area, roundto)
            for line in item.output_ids:
                total_cost = round(line.total_area * average_cost, roundto)
                avg_data = {'real_unit_cost': average_cost,
                            'total_cost': total_cost,
                            }
                obj_out.write(cr, uid, line.id, avg_data, context=context)
        return True

    ##--------------------------------------------------------- function fields

    _columns = {
        'input_ids': fields.one2many(
            'tcv.mrp.finished.slab.inputs', 'task_id', 'String',
            readonly=True, states={'draft': [('readonly', False)]}),
        'output_ids': fields.one2many(
            'tcv.mrp.finished.slab.output', 'task_id', 'Output data',
            readonly=True, states={'draft': [('readonly', False)]}),
        }

    _defaults = {
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    def load_default_values(self, cr, uid, parent_id, context=None):
        '''
        If required, here you can create here a new task with any default data
        this method must be overriden in inherited models
        '''
        res = super(tcv_mrp_finished_slab, self).load_default_values(
            cr, uid, parent_id, context)

        obj_spr = self.pool.get('tcv.mrp.subprocess')

        subp = obj_spr.browse(cr, uid, parent_id, context=context)

        input_list = []
        if subp.prior_id:
            model = subp.prior_id.template_id.output_model.name
            obj_pri = self.pool.get(model)
            output_ids = obj_pri.search(cr, uid, [('subprocess_ref', '=',
                                                  subp.prior_id.id),
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

        if input_list:
            date_start = (
                datetime.now() +
                relativedelta(minutes=-1)).strftime("%Y-%m-%d %H:%M:%S")
            date_end = time.strftime('%Y-%m-%d %H:%M:%S')
            res.update({'default_date_start': date_start,
                        'default_date_end': date_end,
                        'default_input_ids': input_list}
                       )
        return res

    def clear_output(self, cr, uid, ids, context):
        unlink_ids = []
        so_brw = self.browse(cr, uid, ids, context={})[0]
        for line in so_brw.output_ids:
            unlink_ids.append((2, line.id))
        if unlink_ids:
            self.write(cr, uid, so_brw.id, {'output_ids': unlink_ids}, context)
        return True

    def create_txt_profit(self, cr, uid, ids, context):
        if not ids:
            return []
        res = {}
        obj_txt = self.pool.get('tcv.mrp.finished.product.txt.export')
        so_brw = self.browse(cr, uid, ids[0], context={})
        txt_file = obj_txt.create_txt_profit(cr, uid, ids, so_brw, context)
        file_name = u'%s_%s.txt' % (so_brw.parent_id.template_id.name,
                                    so_brw.parent_id.ref)
        file_name = file_name.replace('/', '_').replace(' ', '_')
        # limpiar tildes y demás (ñÜ...)
        # desde http://guimi.net/blogs/hiparco/funcion-para-eliminar-
        # acentos-en-python/
        file_name = ''.join((c for c in unicodedata.normalize(
            'NFD', unicode(file_name)) if unicodedata.category(c) != 'Mn'))
        res.update({
            'name': _('Create TXT file'),
            'type': 'ir.actions.act_window',
            'res_model': 'tcv.mrp.finished.product.txt.export',
            'view_type': 'form',
            'view_id': False,
            'view_mode': 'form',
            'nodestroy': True,
            'target': 'new',
            'domain': "",
            'context': {'default_txt_file': txt_file,
                        'default_advice': _('The TXT file was generated ' +
                                            'suscefully, please save yor ' +
                                            'file.'),
                        'default_name': file_name.decode()}
            })
        return res

    def relocate_products(self, cr, uid, ids, context):
        if not ids:
            return []
        res = {}
        res.update({
            'name': _('Change product\'s location'),
            'type': 'ir.actions.act_window',
            'res_model': 'tcv.mrp.finished.slab.output.change.location',
            'view_type': 'form',
            'view_id': False,
            'view_mode': 'form',
            'nodestroy': True,
            'target': 'new',
            'domain': "[('task_id', '=', %s)]" % ids[0],
            'context': {'task_ids': ids}
            })
        return res

    def load_finished_products(self, cr, uid, ids, context):
        if not ids:
            return []
        ids = isinstance(ids, (int, long)) and [ids] or ids
        res = {}
        context.update({'default_task_id': ids[0], })
        res.update({
            'name': _('Load finished product'),
            'type': 'ir.actions.act_window',
            'res_model': 'tcv.mrp.finished.slab.output.wizard',
            'view_type': 'form',
            'view_id': False,
            'view_mode': 'form',
            'nodestroy': True,
            'target': 'new',
            'domain': "",
            'context': context
            })
        return res

    def _create_model_account_move_lines(self, cr, uid, task, lines, context):
        '''
        Must be overridden in models inherited
        Here you create and return a acount.move.lines (list of dict)
        task is a task.browse object
        return a sum of created lines amounts
        '''
        total_amount = 0.0
        name = context.get('move_name', '')
        company_id = context.get('move_company_id', 'Error')
        input_products = {}
        for input in task.input_ids:
            #~ if not input_products.has_key(input.product_id.id):
            if input.product_id.id not in input_products:
                input_products[input.product_id.id] = {
                    'account_id':
                    input.product_id.property_stock_account_output.id or
                    input.product_id.categ_id.property_stock_account_output_categ.id,
                    'name': input.product_id.name}
            if 'amount' in input_products[input.product_id.id]:
                input_products[
                    input.product_id.id]['amount'] += input.total_cost
            else:
                input_products[
                    input.product_id.id]['amount'] = input.total_cost
        for key in input_products:
            product = input_products[key]
            total_amount += product['amount']
            lines.append(
                self._gen_account_move_line(
                    company_id, product['account_id'],
                    _('%s %s') % (product['name'], name),
                    0.0, product['amount']))

        # Outputs = debits
        output_products = {}
        for output in task.output_ids:
            if not output_products.get(output.product_id.id):
                output_products[output.product_id.id] = {
                    'account_id':
                    output.product_id.property_stock_account_input.id or
                    output.product_id.categ_id.property_stock_account_input_categ.id,
                    'name': output.product_id.name}
            if output_products[output.product_id.id].get('amount'):
                output_products[
                    output.product_id.id]['amount'] += output.total_cost
            else:
                output_products[
                    output.product_id.id]['amount'] = output.total_cost
        for key in output_products:
            product = output_products[key]
            total_amount -= product['amount']
            lines.append(self._gen_account_move_line(company_id,
                         product['account_id'], _('%s %s') %
                         (product['name'], name),
                         product['amount'], 0.0))

        if total_amount:
            #~ account_id = obj_tmp.get_var_value(
            #~cr, uid, task.parent_id.template_id.id,
            #~'account_rounding_difference')
            account_id = context.get('task_config').rounding_account_id.id
            debit, credit = (0.0, abs(total_amount)) if total_amount < 0 else \
                (total_amount, 0.0)
            lines.append(self._gen_account_move_line(
                company_id, account_id,
                _('Unit cost rounding diff %s') % (name), debit, credit))
            total_amount = 0.0

        return total_amount

    def _create_model_stock_move_lines(self, cr, uid, task, lines,
                                       context=None):
        obj_lot = self.pool.get('stock.production.lot')
        obj_out = self.pool.get('tcv.mrp.finished.slab.output')
        for output in task.output_ids:
            if output.heigth > output.length:
                length, heigth = output.heigth, output.length
            else:
                length, heigth = output.length, output.heigth
            lot = {'product_id': output.product_id.id,
                   'name': output.prod_lot_ref,
                   'date': task.date_end,
                   'length': length,
                   'heigth': heigth,
                   'company_id': context.get('task_company_id'),
                   'property_cost_price': output.real_unit_cost}
            if output.prod_lot_id:
                prod_lot_id = output.prod_lot_id.id
                obj_lot.write(cr, uid, prod_lot_id, lot, context=context)
            else:
                prod_lot_id = obj_lot.create(cr, uid, lot, context)
                obj_out.write(cr, uid, output.id,
                              {'prod_lot_id': prod_lot_id}, context)

            slab = {
                'product_id': output.product_id.id,
                'name': context.get('task_name', ''),
                'date': context.get('task_date'),
                'location_id': context.get('task_config').location_id.id,
                'pieces_qty': output.pieces,
                'location_dest_id': output.location_id.id,
                'product_qty': output.total_area,
                'product_uos_qty': output.total_area,
                'product_uom': output.product_id.uom_id.id,
                'prodlot_id': prod_lot_id,
                'state': 'draft'}
            lines.append((0, 0, slab))
        return lines

    def get_task_input_sumary(self, cr, uid, ids_str, context=None):
        sql = """
        select sum(i.pieces) pieces, sum(i.pieces*heigth*length) as qty
        from tcv_mrp_finished_slab_inputs i
        left join tcv_mrp_io_slab s on i.output_id = s.id
        where task_id in %s
        """ % ids_str
        cr.execute(sql)
        return cr.dictfetchone()

    def get_task_output_sumary(self, cr, uid, ids_str, context=None):
        sql = """
        select sum(pieces) pieces, sum(pieces*heigth*length) as qty
        from tcv_mrp_finished_slab_output
        where task_id in %s
        """ % ids_str
        cr.execute(sql)
        return cr.dictfetchone()

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

    def test_done(self, cr, uid, ids, *args):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        for item in self.browse(cr, uid, ids, context={}):
            if not item.output_ids:
                raise osv.except_osv(
                    _('Error!'),
                    _('You must load finished products first!'))
            else:
                for lot in item.output_ids:
                    if not lot.product_id.sale_ok:
                        raise osv.except_osv(
                            _('Error!'),
                            _('The product: %s, can\'t be sold!') %
                            lot.product_id.name)
        return True

    def do_before_done(self, cr, uid, ids, context=None):
        self._compute_average_cost(cr, uid, ids, context)
        return super(tcv_mrp_finished_slab, self).\
            do_before_done(cr, uid, ids, context)

    def button_done(self, cr, uid, ids, context=None):
        res = super(tcv_mrp_finished_slab, self).\
            button_done(cr, uid, ids, context=context)
        return res

tcv_mrp_finished_slab()

##------------------------------------------------ tcv_mrp_finished_slab_inputs


class tcv_mrp_finished_slab_inputs(osv.osv):

    _name = 'tcv.mrp.finished.slab.inputs'

    _description = ''

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
            res.append((i.id, '%s (%s x %s) ' % (
                i.product_id.name, i.prod_lot_ref, i.pieces)))
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
            'tcv.mrp.finished.slab', 'inputs',
            required=True, ondelete='cascade'),
        'output_id': fields.many2one(
            'tcv.mrp.io.slab', 'inputs', required=True,
            ondelete='restrict', readonly=False),
        'product_id': fields.related(
            'output_id', 'product_id', type='many2one',
            relation='product.product', string='Product', store=False,
            readonly=True),
        'prod_lot_ref': fields.function(
            _compute_all, method=True, type='char', string='Lot reference',
            multi='all'),
        'pieces': fields.integer(
            'slabs'),
        'available_pcs': fields.function(
            _compute_all, method=True, type='integer', string='Availables pcs',
            multi='all'),
        'length': fields.function(
            _compute_all, method=True, type='float', string='Length (m)',
            digits_compute=dp.get_precision('Extra UOM data'), multi='all'),
        'heigth': fields.function(
            _compute_all, method=True, type='float', string='Heigth (m)',
            digits_compute=dp.get_precision('Extra UOM data'), multi='all'),
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

tcv_mrp_finished_slab_inputs()

##------------------------------------------------ tcv_mrp_finished_slab_output


class tcv_mrp_finished_slab_output(osv.osv):

    _name = 'tcv.mrp.finished.slab.output'

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
        'task_id': fields.many2one(
            'tcv.mrp.finished.slab', 'Task',
            required=True, ondelete='cascade'),
        'input_id': fields.many2one(
            'tcv.mrp.finished.slab.inputs', 'Origin', required=True,
            ondelete='cascade'),
        'product_id': fields.many2one(
            'product.product', 'Product', ondelete='restrict',
            required=True, help="The output product"),
        'prod_lot_ref': fields.char(
            'Lot reference', size=24, readonly=True),
        'location_id': fields.many2one(
            'stock.location', 'Location', required=True, select=True,
            ondelete='restrict', help=""),
        'length': fields.float(
            'Length (m)', digits_compute=dp.get_precision('Extra UOM data')),
        'heigth': fields.float(
            'Heigth (m)', digits_compute=dp.get_precision('Extra UOM data')),
        'pieces': fields.integer('Slabs'),
        'thickness': fields.integer(
            'Thickness (mm)', help="The product thickness, " +
            "correction value for volume calculation assigned in template: " +
            "thickness_factor_correction"),
        'total_area': fields.function(
            _compute_area, method=True, type='float',
            string='Area (m2)',
            digits_compute=dp.get_precision('Product UoM')),
        'real_unit_cost': fields.float(
            'Unit cost', digits_compute=dp.get_precision('MRP unit cost'),
            readonly=True),
        'total_cost': fields.float(
            'Total cost', digits_compute=dp.get_precision
            ('Account'), readonly=True),
        'prod_lot_id': fields.many2one(
            'stock.production.lot', 'Production lot', required=False,
            ondelete='cascade'),
        # this ondelete='cascade' is set to force to delete the
        # stock.production.lot object if its origin is deleted!
        }

    _defaults = {
        }

    _sql_constraints = [
        ('length_gt_zero', 'CHECK (length  between 0.5 and 4)',
         'The length must be 0.5-4!'),
        ('heigth_gt_zero', 'CHECK (heigth  between 0.5 and 4)',
         'The heigth must be 0.5-4!'),
        ('thickness_gt_zero', 'CHECK (thickness>0)',
         'The thickness must be > 0!'),
        ('pieces_gt_zero', 'CHECK (pieces>0)', 'The pieces must be > 0!'),
        ]

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------------ on_change...

    def on_change_input_id(self, cr, uid, ids, input_id):
        res = {}
        if input_id:
            obj_out = self.pool.get('tcv.mrp.finished_slab.output')
            obj_uom = self.pool.get('product.uom')
            out_ids = obj_out.search(cr, uid, [('input_id', '=', input_id)])
            if input_id in out_ids:
                out_ids.remove(input_id)
            slabs = 0
            if out_ids:
                out_brw = self.browse(cr, uid, out_ids, context={})
                for o in out_brw:
                    slabs += o.pieces

            input = self.pool.get('tcv.mrp.finished_slab.inputs').\
                browse(cr, uid, input_id, context=None)
            res = {'value': {}}
            res['value'].update({'product_id': input.product_id.id,
                                 'length': input.length,
                                 'heigth': input.heigth,
                                 'pieces': input.pieces - slabs,
                                 'thickness': input.thickness,
                                 'total_area': obj_uom.
                                 _calc_area(input.pieces - slabs, input.length,
                                            input.heigth)
                                 })
        return res

    ##----------------------------------------------------- create write unlink

    def unlink(self, cr, uid, ids, context=None):
        unlink_lots = []
        for item in self.browse(cr, uid, ids, context={}):
            if item.prod_lot_id:
                unlink_lots.append(item.prod_lot_id.id)
        if unlink_lots:
            obj_lot = self.pool.get('stock.production.lot')
            obj_lot.unlink(cr, uid, unlink_lots, context)
        res = super(tcv_mrp_finished_slab_output, self).\
            unlink(cr, uid, ids, context)
        return res

    ##---------------------------------------------------------------- Workflow

tcv_mrp_finished_slab_output()
