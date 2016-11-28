# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2014-04-21
#    Version: 0.0.0.1
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

##---------------------------------------------------------- tcv_mrp_waste_slab


class tcv_mrp_waste_slab(osv.osv):

    _name = 'tcv.mrp.waste.slab'

    _inherit = 'tcv.mrp.finished.base'

    _description = ''

    ##-------------------------------------------------------------------------

    def _get_task_info(self, cr, uid, obj_task, context=None):
        res = ''
        for imp in obj_task.input_ids:
            info = '[%s] %s (%s %sx%s)' % (imp.product_id.default_code,
                                           imp.prod_lot_ref, imp.pieces,
                                           imp.length, imp.heigth)
            res = '%s, %s' % (res, info) if res else info
        return res[:128]

    def load_default_values(self, cr, uid, parent_id, context=None):
        '''
        If required, here you can create here a new task with any default data
        this method must be overriden in inherited models
        '''
        res = super(tcv_mrp_waste_slab, self).\
            load_default_values(cr, uid, parent_id, context)

        obj_spr = self.pool.get('tcv.mrp.subprocess')

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
        if input_list:
            date_start = (datetime.now() + relativedelta(minutes=-1)).\
                strftime("%Y-%m-%d %H:%M:%S")
            date_end = time.strftime('%Y-%m-%d %H:%M:%S')
            res.update({'default_date_start': date_start,
                        'default_date_end': date_end,
                        'default_input_ids': input_list,
                        'valid_cost': True,
                        })
        return res

    ##------------------------------------------------------- _internal methods

    def _template_params(self):
        res = super(tcv_mrp_waste_slab, self)._template_params()
        res.extend(
            [{'sequence': 130,
              'name': 'account_mrp_stock_waste',
              'type': 'account',
              'help': _('Account for the production stock loss (credit)')},
             {'sequence': 140,
              'name': 'account_mrp_waste',
              'type': 'account',
              'help': _('Account for the production loss (debit)')},
             ])
        return res

    ##--------------------------------------------------------- function fields

    _columns = {
        'input_ids': fields.one2many(
            'tcv.mrp.waste.slab.inputs', 'task_id', 'String', readonly=True,
            states={'draft': [('readonly', False)]}),
        }

    _defaults = {
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    def _create_model_account_move_lines(self, cr, uid, task, lines, context):
        '''
        Must be overridden in models inherited
        Here you create and return a acount.move.lines (list of dict)
        task is a task.browse object
        return a sum of created lines amounts
        '''
        name = context.get('move_name', '')
        company_id = context.get('move_company_id', 'Error')
        obj_tmp = self.pool.get('tcv.mrp.template')
        account_mrp_waste = obj_tmp.get_var_value(
            cr, uid, task.parent_id.template_id.id, 'account_mrp_waste') or 0
        account_mrp_stock_waste = (obj_tmp.get_var_value(
            cr, uid, task.parent_id.template_id.id,
            'account_mrp_stock_waste') or 0)
        if not account_mrp_waste or not account_mrp_stock_waste:
            raise osv.except_osv(
                _('Error!'),
                _('Please check template account params'))

        # inputs = credits (from "productos en proceso")
        input_products = {}
        for input in task.input_ids:
            prd_id = input.product_id.id
            if not input_products.get(prd_id):
                prd = input.product_id
                input_products[prd_id] = {
                    'account_id': prd.property_stock_account_output.id or
                    prd.categ_id.property_stock_account_output_categ.id,
                    'name': input.product_id.name}
            if input_products[prd_id].get('amount'):
                input_products[prd_id]['amount'] += input.total_cost
            else:
                input_products[prd_id]['amount'] = input.total_cost
        for key in input_products:
            product = input_products[key]
            lines.append(self._gen_account_move_line(
                company_id,
                account_mrp_stock_waste,
                _('%s %s') % (product['name'], name),
                0.0,
                product['amount']))
            lines.append(self._gen_account_move_line(
                company_id,
                account_mrp_waste,
                _('%s %s') % (product['name'], name),
                product['amount'],
                0.0))
        return 0.0

    def get_task_input_sumary(self, cr, uid, ids_str, context=None):
        sql = """
        select sum(i.pieces) pieces, sum(i.pieces*heigth*length) as qty
        from tcv_mrp_waste_slab_inputs i
        left join tcv_mrp_io_slab s on i.output_id = s.id
        where task_id in %s
        """ % ids_str
        cr.execute(sql)
        return cr.dictfetchone()

    ##-------------------------------------------------------- buttons (object)

    def get_task_runtime_sumary(self, cr, uid, ids_str, context=None):
        return {}

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

    def test_draft(self, cr, uid, ids, *args):
        if len(ids) != 1:
            raise osv.except_osv(
                _('Error!'),
                _('Multiple operations not allowed'))
        for task in self.browse(cr, uid, ids, context=None):
            if task.move_id and task.move_id.state != 'draft':
                raise osv.except_osv(
                    _('Error!'),
                    _('Can\'t reset a process while account move ' +
                      'state <> "Draft"'))
        return True

    def test_done(self, cr, uid, ids, *args):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        vals = {'valid_cost': True}
        self.write(cr, uid, ids, vals, context=None)
        return super(tcv_mrp_waste_slab, self).\
            test_done(cr, uid, ids, args)

tcv_mrp_waste_slab()


##--------------------------------------------------- tcv_mrp_waste_slab_inputs


class tcv_mrp_waste_slab_inputs(osv.osv):

    _name = 'tcv.mrp.waste.slab.inputs'

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
            res.append((i.id, '%s (%s x %s) ' %
                       (i.product_id.name, i.prod_lot_ref, i.pieces)))
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
            'tcv.mrp.waste.slab', 'inputs', required=True, ondelete='cascade'),
        'date_start': fields.related(
            'task_id', 'date_start', type='datetime',
            string='Date', store=False, readonly=True),
        'output_id': fields.many2one(
            'tcv.mrp.io.slab', 'inputs', required=True, ondelete='restrict',
            readonly=False),
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

tcv_mrp_waste_slab_inputs()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
