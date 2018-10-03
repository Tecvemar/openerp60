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
import time
#~ import netsvc
import logging
logger = logging.getLogger('server')


##---------------------------------------------------------- tcv_mrp_basic_task


class tcv_mrp_basic_task(osv.osv):

    _name = 'tcv.mrp.basic.task'

    _description = ''

    _stock_picking_type = 'out'

    # Form this date: Oper & F/O cost from hrs to m2
    _change_method_date = '2014-04-01'

    def _template_params(self):
        res = [
            {'sequence': 10, 'name': 'operator_cost', 'type': 'float',
             'help': 'Costo por hora del personal asignado a la tarea'},
            {'sequence': 15, 'name': 'operator_cost_m2', 'type': 'float',
             'help': 'Costo por m2 del personal asignado a la tarea'},
            {'sequence': 20, 'name': 'factory_overhead', 'type': 'float',
             'help': 'Costo por hora por concepto de carga fabril'},
            {'sequence': 25, 'name': 'factory_overhead_m2', 'type': 'float',
             'help': 'Costo por m2 por concepto de carga fabril'},
            {'sequence': 10, 'name': 'account_operator_cost', 'type':
             'account', 'help':
             _('Account for the cost of operator cost applied')},
            {'sequence': 120, 'name': 'account_factory_overhead', 'type':
             'account', 'help':
             _('Account for the cost of the factory overhead applied')},
            {'sequence': 121, 'name': 'account_applied_cost', 'type':
             'account', 'help': _('Account for the proccess applied cost')},
            ]
        return res

    def _account_move_settings(self):
        res = {
            'operator_cost': {'name': _('Operator cost'), 'isproduct': False},
            'factory_overhead': {'name': _('Factory overhead'),
                                 'isproduct': False},
            }
        return res

    ##-------------------------------------------------------------------------

    def _compute_run_time(self, cr, uid, date_start, date_end, context=None):
        '''Must return date_end - date_start in hours'''
        if date_start and date_end and date_start < date_end:
            try:
                ts = time.mktime(time.strptime(
                    date_start, '%Y-%m-%d %H:%M:%S'))
                #TODO usar: tools.DEFAULT_SERVER_DATE_FORMAT
                te = time.mktime(time.strptime(
                    date_end, '%Y-%m-%d %H:%M:%S'))
                rt = (te - ts)  # Result in seconds
                h = (rt) // 3600
                m = ((rt) % 3600.0) / 60.0 / 60.0
                # decimales (0.10 = 6 seg) usa regla de 3: 1 -> 60seg | m -> s
                res = h + m
            except:
                return None
            return res

    def _compute_operator_cost(self, task, round_to):
        if task.run_time < 0:
            raise osv.except_osv(_('Error!'), _('Run time must be > 0'))
        return round(task.run_time * task.operator_cost, round_to)

    def _compute_factory_overhead(self, task, round_to):
        if task.run_time < 0:
            raise osv.except_osv(_('Error!'), _('Run time must be > 0'))
        return round(task.run_time * task.factory_overhead, round_to)

    def _compute_cost_by_m2(self, cr, uid, task, area, round_to):
        obj_tmp = self.pool.get('tcv.mrp.template')
        tmpl_id = task.parent_id.template_id.id
        operator_m2 = obj_tmp.get_var_value(
            cr, uid, tmpl_id, 'operator_cost_m2')
        factory_m2 = obj_tmp.get_var_value(
            cr, uid, tmpl_id, 'factory_overhead_m2')
        res = {'operator_m2': operator_m2,
               'operator_cost_m2': round(area * operator_m2, round_to),
               'factory_m2': factory_m2,
               'factory_overhead_m2': round(area * factory_m2, round_to),
               }
        return res

    def _get_task_info(self, cr, uid, obj_task, context=None):
        return ''

    ##--------------------------------------------------------- function fields

    def _compute_all_fields(self, cr, uid, ids, name, arg, context=None):
        context = context or {}
        if not len(ids):
            return []
        res = {}
        for item in self.browse(cr, uid, ids, context={}):
            run_time = self._compute_run_time(
                cr, uid, item.date_start, item.date_end, context) - \
                item.downtime
            supplies_cost = 0
            for supp in item.supplies_ids:
                supplies_cost += supp.amount
            res[item.id] = {'run_time': run_time,
                            'supplies_cost': supplies_cost,
                            'task_info': self._get_task_info(
                                cr, uid, item, context)}
        return res

    ##-------------------------------------------------------------------------

    _columns = {
        'parent_id': fields.many2one(
            'tcv.mrp.subprocess', 'Subprocess', required=True,
            readonly=True, ondelete='cascade'),
        'name': fields.char(
            'Name', size=64, required=False, readonly=True,
            states={'draft': [('readonly', False)]}),
        'narration': fields.text(
            'Notes', readonly=False),
        'supplies_ids': fields.one2many(
            'tcv.mrp.basic.task.supplies', 'task_id', 'Supplies',
            readonly=True, states={'draft': [('readonly', False)]}),
        'costs_ids': fields.one2many(
            'tcv.mrp.basic.task.costs', 'task_id', 'Output data',
            readonly=True),
        'stops_ids': fields.one2many(
            'tcv.mrp.basic.task.stops', 'task_id', 'Stop issues',
            readonly=False),
        'date_start': fields.datetime(
            'Date started', required=True, readonly=True,
            states={'draft': [('readonly', False)]}, select=True,
            help="Date on which this process has been started."),
        'date_end': fields.datetime(
            'Date finished', required=True, select=True, readonly=True,
            states={'draft': [('readonly', False)]},
            help="Date on which this process has been finished."),
        'run_time': fields.function(
            _compute_all_fields, method=True, type='float',
            string='Production runtime', multi='all',
            help="The production time in hours (the decimal part represents " +
            "the hour's fraction 0.50 = 30 min) (minus downtime)."),
        'downtime': fields.float(
            'Downtime', required=True, readonly=True,
            states={'draft': [('readonly', False)]},
            help="The downtime (in hours) of actual process"),
        'operator_cost': fields.float(
            'Operator cost', digits_compute=dp.get_precision('Account'),
            readonly=True, states={'draft': [('readonly', False)]},
            help="Estimated operator cost per hour, from template " +
            "(operator_cost)"),
        'factory_overhead': fields.float(
            'Factory Overhead', digits_compute=dp.get_precision('Account'),
            readonly=True, states={'draft': [('readonly', False)]},
            help="Estimated factory Overhead per hour, from template " +
            "(factory_overhead)"),
        'supplies_cost': fields.function(
            _compute_all_fields, method=True, type='float',
            string='Supplies cost', digits_compute=dp.get_precision('Account'),
            multi='all'),
        'valid_cost': fields.boolean(
            'Valid cost', help="set to true when cost is calculated ok",
            readonly=True),
        # This state field not is a standart workflow "state" fields,
        # is only a flag (draft-done) to lock-unlock data
        'state': fields.selection([(
            'draft', 'Draft'), ('done', 'Done')], string='State',
            required=True, readonly=True),
        'move_id': fields.many2one(
            'account.move', 'Account move', ondelete='restrict',
            help="The accounting move of this entry.", readonly=True),
        'picking_id': fields.many2one(
            'stock.picking', 'Stock picking', ondelete='restrict',
            help="The stock picking of this entry.", select=True,
            readonly=True),
        'task_info': fields.function(
            _compute_all_fields, method=True, type='char', size=128,
            string='Task name', multi='all'),
        }

    _defaults = {
        'valid_cost': lambda *a: False,
        'downtime': lambda *a: 0,
        'state': lambda *a: 'draft',
        }

    _sql_constraints = [
        ('run_time_gt_zero', 'CHECK (date_start<date_end)',
         'The run time must be > 0 !'),
        ('downtime_gt_zero', 'CHECK (downtime>=0)',
         'The downtime must be >= 0 !'),
        ]

    ##-------------------------------------------------------------------------

    def _clear_previous_cost_distribution(self, cr, uid, obj_cost,
                                          context=None):
        unlink_ids = []
        for line in obj_cost.costs_ids:
            unlink_ids.append((2, line.id))
        if unlink_ids:
            self.write(
                cr, uid, obj_cost.id, {'costs_ids': unlink_ids}, context)

    def cost_distribution(self, cr, uid, ids, context=None):
        return True

    def process_all_input(self, cr, uid, ids, context=None):
        '''
        Send all input data to output valid for input = io.slab
        '''
        output_ids = []
        for item in self.browse(cr, uid, ids, context):
            for line in item.input_ids:
                output_ids.append((0, 0, {'input_id': line.id,
                                          'product_id': line.product_id.id,
                                          'pieces': line.pieces,
                                          'length': line.length,
                                          'heigth': line.heigth,
                                          'thickness': line.thickness,
                                          }))
            if output_ids:
                self.write(cr, uid, item.id,
                           {'output_ids': output_ids}, context)
        return True

    def show_products_resulting(self, cr, uid, ids, context=None):
        if not ids:
            return []
        res = {}
        brw = self.browse(cr, uid, ids[0], context={})
        model = brw.parent_id.template_id.output_model.model
        res.update({'name':
                    _('Products resulting (%s)') %
                    brw.parent_id.template_id.name,
                    'type': 'ir.actions.act_window',
                    'res_model': model,
                    'view_type': 'tree',
                    'view_id': self.pool.get('ir.ui.view').search(
                        cr, uid, [('model', '=', model)]),
                    'view_mode': 'tree',
                    'nodestroy': True,
                    'target': 'current',
                    'domain': [('task_ref', '=', brw.id),
                               ('subprocess_ref', '=', brw.parent_id.id)],
                    'context': {}
                    })
        return res

    def load_default_values(self, cr, uid, parent_id, context=None):
        '''
        If required, here you can create here a new task with any default data
        this method must be overriden in inherited models
        Return a dict with default values
            ex:{'default_product_id':product_id}
        Don't forget to add "default_" in field names
        '''
        obj_tmp = self.pool.get('tcv.mrp.template')
        obj_spr = self.pool.get('tcv.mrp.subprocess')
        subp = obj_spr.browse(cr, uid, parent_id, context=context)
        if subp.template_id.input_model and subp.prior_id.state != 'done':
            raise osv.except_osv(
                _('Error!'),
                _('You must set the prior task as "Done" before continuing'))
        operator_cost = obj_tmp.get_var_value(
            cr, uid, subp.template_id.id, 'operator_cost_m2')
        factory_overhead = obj_tmp.get_var_value(
            cr, uid, subp.template_id.id, 'factory_overhead_m2')
        return {'default_operator_cost': operator_cost,
                'default_factory_overhead': factory_overhead}

    def get_output_data_line(self, item, line):
        '''
        Must be overridden in models inherited
        Create output data in template.output_model
        '''
        return {}

    def save_output_products(self, cr, uid, ids, context=None):
        so_brw = self.browse(cr, uid, ids, context={})
        for item in so_brw:
            model = item.parent_id.template_id.output_model.model
            obj_out = self.pool.get(model)
            unlink_ids = obj_out.search(
                cr, uid, [('task_ref', '=', item.id),
                          ('subprocess_ref', '=', item.parent_id.id)])
            if unlink_ids:
                obj_out.unlink(cr, uid, unlink_ids, context)
            for line in item.costs_ids:
                data = self.get_output_data_line(item, line)
                if data:
                    obj_out.create(cr, uid, data, context)
                else:
                    logger.warn('No output products generated ' +
                                '(%s.save_output_products)' % self._name)
        return True

    def _gen_account_move_line(self, company_id, account_id,
                               name, debit, credit):
        return (0, 0, {'auto': True,
                       'company_id': company_id,
                       'account_id': account_id,
                       'name': name[: 64],
                       'debit': round(debit, 2),
                       'credit': round(credit, 2),
                       'reconcile': False,
                       })

    def _check_rounding_diff(self, lines, company_id, name, context):
        amount_diff = 0.0
        for l in lines:
            amount_diff += l[2]['credit'] - l[2]['debit']
        if abs(amount_diff) > 0.0001:
            account_id = context.get('task_config').rounding_account_id.id
            amount_diff = round(amount_diff, 2)
            debit, credit = (0.0, abs(amount_diff)) if amount_diff < 0 else (
                amount_diff, 0.0)
            lines.append(self._gen_account_move_line(
                company_id, account_id,
                _('Unit cost rounding diff %s') % (name), debit, credit))

    def _get_settings_acc_cost_id(self, cr, uid, cost_name, cost_line, task):
        '''
        Must be overridden in models inherited
        Return an account id for cost applied (blades & abrasive)
        '''
        return 0

    def _create_model_account_move_lines(self, cr, uid, task, lines, context):
        '''
        Must be overridden in models inherited
        Here you create and return a acount.move.lines (list of dict)
        task is a task.browse object
        return a sum of created lines amounts
        '''
        return 0.0

    def call_create_account_move_lines(self, cr, uid, ids, context=None):
        context = context or {}
        obj_cfg = self.pool.get('tcv.mrp.config')
        company_id = self.pool.get('res.users').browse(
            cr, uid, uid, context=context).company_id.id
        cfg_id = obj_cfg.search(cr, uid, [('company_id', '=', company_id)])
        if cfg_id:
            mrp_cfg = obj_cfg.browse(cr, uid, cfg_id[0], context=context)
        task = self.browse(
            cr, uid, ids, context=context)
        context.update({
            'task_company_id': company_id,
            'task_config': mrp_cfg,
            'task_date': task.date_end})
        return self.create_account_move_lines(
            cr, uid, task, lines=None, context=context)

    def create_account_move_lines(self, cr, uid, task, lines=None,
                                  context=None):
        '''
        task is a task.browse object
        '''
        if lines is None:
            lines = []

        company_id = context.get('task_company_id')
        obj_tmp = self.pool.get('tcv.mrp.template')
        template_params = obj_tmp.get_all_values(
            cr, uid, task.parent_id.template_id.id)
        #~ total_amount = 0.0
        name = '(%s/%s) %s' % (task.parent_id.process_id.ref,
                               task.parent_id.ref[-6:],
                               task.parent_id.template_id.name)
        context.update({'move_name': name, 'move_company_id': company_id})

        # inherited models extra lines
        total_amount = self._create_model_account_move_lines(
            cr, uid, task, lines, context)
        # Supplies
        for cost_supp in task.supplies_ids:
            account_id = cost_supp.product_id.property_stock_account_output.\
                id or cost_supp.product_id.categ_id.\
                property_stock_account_output_categ.id
            acc_cost_id = cost_supp.product_id.property_account_expense.id or \
                cost_supp.product_id.categ_id.property_account_expense_categ.id
            if not account_id:
                raise osv.except_osv(
                    _('Error!'),
                    _('No supplies account found, please check product and ' +
                      'category account settings (%s)') %
                    cost_supp.product_id.name)
            total_amount += cost_supp.amount
            lines.append(self._gen_account_move_line(
                company_id, account_id,
                _('%s: %s') % (cost_supp.product_id.name, name), 0.0,
                cost_supp.amount))
            lines.append(self._gen_account_move_line(
                company_id, acc_cost_id,
                _('%s: %s') % (cost_supp.product_id.name, name),
                cost_supp.amount, 0.0))

        # Operator & factory overhead
        for cost_line in task.costs_ids:

            settings = self._account_move_settings()
            # operator and factory overhead
            fo_oc_cost = 0
            for key in settings:
                amount = getattr(cost_line, key, 0.0)
                account_id = template_params['account_%s' % key]
                if amount != 0.0:
                    #~ total_amount += amount
                    lines.append(self._gen_account_move_line(
                        company_id, account_id, _('%s: %s') %
                        (settings[key]['name'], name), 0.0, amount))
                    if not settings[key].get('isproduct'):
                        fo_oc_cost += amount
                    else:
                        acc_cost_id = self._get_settings_acc_cost_id(
                            cr, uid, key, cost_line, task)
                        lines.append(self._gen_account_move_line(
                            company_id, acc_cost_id, _('%s: %s') %
                            (settings[key]['name'], name), amount, 0.0))
            # warning!
            # this code call .output_id and this field is defined in inherited
            # models mut be created in this model (also output_ids field
            # and _output model)
            total_cost = cost_line.total_cost - cost_line.cumulative_cost
            # Productos en proceso
            product = cost_line.output_id.product_id
            account_id = product.property_stock_account_input.id or \
                product.categ_id.property_stock_account_input_categ.id
            acc_cost_id = template_params.get('account_applied_cost')
            if not account_id:
                raise osv.except_osv(
                    _('Error!'),
                    _('No output product account found, please check ' +
                      'product and category account settings (%s)') %
                    product.name)
            lines.append(self._gen_account_move_line(
                company_id, acc_cost_id, _('%s: %s') %
                (product.name, name), 0.0, total_cost - fo_oc_cost))
            lines.append(self._gen_account_move_line(
                company_id, account_id, _('%s: %s') %
                (product.name, name), total_cost, 0.0))
        self._check_rounding_diff(lines, company_id, name, context)
        return lines

    def create_account_move(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        obj_move = self.pool.get('account.move')
        obj_cfg = self.pool.get('tcv.mrp.config')
        obj_per = self.pool.get('account.period')
        company_id = self.pool.get('res.users').browse(
            cr, uid, uid, context=context).company_id.id
        cfg_id = obj_cfg.search(cr, uid, [('company_id', '=', company_id)])
        if cfg_id:
            mrp_cfg = obj_cfg.browse(cr, uid, cfg_id[0], context=context)
        else:
            raise osv.except_osv(_('Error!'),
                                 _('Please set a valid configuration '))
        so_brw = self.browse(cr, uid, ids, context={})
        move_ids = []
        for task in so_brw:
            date = task.date_end  # account_move.date = end of task
            context.update({'task_company_id': company_id,
                            'task_config': mrp_cfg, 'task_date': date})
            ref = '[%s - %s] %s' % (
                task.parent_id.process_id.ref, task.parent_id.ref,
                task.name) if task.name else '[%s - %s] %s' % (
                task.parent_id.process_id.ref, task.parent_id.ref,
                task.parent_id.template_id.name)
            period_id = obj_per.find(cr, uid, date)[0]
            move = {'ref': ref[: 64],
                    'journal_id': task.parent_id.template_id.journal_id.id,
                    'date': date,
                    'min_date': date,
                    'company_id': company_id,
                    'state': 'draft',
                    'to_check': False,
                    'period_id': period_id,
                    'narration': _('Production process: \n\tTemplate: ' +
                                   '%s\n\tProcess: %s\n\tSubprocess: ' +
                                   '%s\n\tDate: %s - %s\n\tInfo: %s') % (
                                       task.parent_id.template_id.name,
                                       task.parent_id.process_id.ref,
                                       task.parent_id.ref,
                                       task.date_start, task.date_end,
                                       task.task_info),
                    }
            lines = self.create_account_move_lines(
                cr, uid, task, None, context)
            if lines:
                move.update({'line_id': lines})
                move_id = obj_move.create(cr, uid, move, context)
                if move_id:
                    obj_move.post(cr, uid, [move_id], context=context)
                    move_ids.append(move_id)
                    self.write(
                        cr, uid, task.id, {'move_id': move_id,
                                           'valid_cost': True}, context)
        return move_ids

    def _create_model_stock_move_lines(self, cr, uid, task, lines,
                                       context=None):
        return lines

    def create_stock_move_lines(self, cr, uid, task, lines, context=None):
        '''
        task is a task.browse object
        '''
        if lines is None:
            lines = []
        if context is None:
            context = {}

        name = '(%s/%s) %s' % (
            task.parent_id.process_id.ref, task.parent_id.ref[-6:],
            task.parent_id.template_id.name)
        context.update({'task_name': name})
        obj_lot = self.pool.get('stock.production.lot')

        # inherited models extra lines
        lines = []
        lines = self._create_model_stock_move_lines(
            cr, uid, task, lines, context)

        # Supplies
        for cost_supp in task.supplies_ids:
            location_id = [97]
            if cost_supp.prod_lot_id:
                location_id = obj_lot.get_actual_lot_location(
                    cr, uid, cost_supp.prod_lot_id.id, context) or [97]
            if cost_supp.product_id.id in (744, 608, 2518, 2519, 2520) and \
                    location_id == [97]:
                location_id = [3510]
            if not location_id:
                raise osv.except_osv(_('Error!'),
                                     _('Missign location for product (%s)') %
                                     cost_supp.prod_lot_id.name)
            supp = {'product_id': cost_supp.product_id.id,
                    'name': name,
                    'date': context.get('task_date'),
                    'location_id': location_id[0],
                    'location_dest_id': context.get(
                        'task_config').location_id.id,
                    'product_qty': cost_supp.quantity,
                    'product_uos_qty': cost_supp.quantity,
                    'product_uom': cost_supp.product_id.uom_id.id,
                    'prodlot_id': cost_supp.prod_lot_id.id if
                    cost_supp.prod_lot_id else 0,
                    'state': 'draft'}
            lines.append((0, 0, supp))

        return lines

    def create_stock_picking(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        obj_pck = self.pool.get('stock.picking')
        obj_cfg = self.pool.get('tcv.mrp.config')
        company_id = self.pool.get('res.users').browse(
            cr, uid, uid, context=context).company_id.id
        company = self.pool.get('res.company').browse(
            cr, uid, company_id, context=context)
        cfg_id = obj_cfg.search(cr, uid, [('company_id', '=', company_id)])
        if cfg_id:
            mrp_cfg = obj_cfg.browse(cr, uid, cfg_id[0], context=context)
        else:
            raise osv.except_osv(_('Error!'),
                                 _('Please set a valid configuration '))
        so_brw = self.browse(cr, uid, ids, context={})
        pick_ids = []
        for task in so_brw:
            date = task.date_start  # stock_move.date = start of task
            context.update({'task_company_id': company_id,
                            'task_config': mrp_cfg,
                            'task_date': date})
            origin = '[%s - %s] %s' % (
                task.parent_id.process_id.ref, task.parent_id.ref,
                task.name) if task.name else '[%s - %s] %s' % (
                    task.parent_id.process_id.ref, task.parent_id.ref,
                    task.parent_id.template_id.name)
            picking = {'name': '/',
                       'type': self._stock_picking_type,
                       'origin': origin[:64],
                       'date': date,
                       'invoice_state': 'none',
                       'stock_journal_id': mrp_cfg.stock_journal_id.id,
                       'company_id': company_id,
                       'auto_picking': False,
                       'move_type': 'one',
                       'partner_id': company.partner_id.id,
                       'state_rw': 0,
                       'note': _(
                           'Production process: \n\tTemplate: %s\n\t' +
                           'Process: %s\n\tSubprocess: %s\n\t' +
                           'Date: %s - %s\n\tInfo: %s') % (
                               task.parent_id.template_id.name,
                               task.parent_id.process_id.ref,
                               task.parent_id.ref,
                               task.date_start, task.date_end,
                               task.task_info),
                       }
            lines = self.create_stock_move_lines(cr, uid, task, None, context)
            if lines:
                picking.update({'move_lines': lines})
                pick_id = obj_pck.create(cr, uid, picking, context)
                if pick_id:
                    pick_ids.append(pick_id)
                    self.write(
                        cr, uid, task.id, {'picking_id': pick_id,
                                           'valid_cost': True}, context)
        return pick_ids

    def get_task_ids_by_date_range(self, cr, uid, template_id,
                                   date_from, date_to, context=None):
        sql = """
        select tk.id as task_id from tcv_mrp_subprocess sp
        left join %s tk on sp.id = tk.parent_id
        where template_id = %s and
              tk.date_end between '%s 00:00:00' and '%s 23:59:59'
        """ % (self._name.replace('.', '_'), template_id, date_from, date_to)
        cr.execute(sql)
        res = cr.fetchall()
        if res:
            l_ids = map(lambda i: i[0], res)
            res = (str(l_ids)[1: - 1]).replace('L', '')
            return '(%s)' % res, len(l_ids)
        else:
            return [], 0

    def get_task_input_sumary(self, cr, uid, ids_str, context=None):
        return {}

    def get_task_output_sumary(self, cr, uid, ids_str, context=None):
        return {}

    def get_task_runtime_sumary(self, cr, uid, ids_str, context=None):
        sql = """
        select sum(EXTRACT(EPOCH FROM date_end-date_start)/3600) as run_time,
               sum(downtime) as down_time
        from %s g
        where g.id in %s;
        """ % (self._name.replace('.', '_'), ids_str)
        cr.execute(sql)
        return cr.dictfetchone() or {'run_time': 0, 'downtime': 0}

    def button_update_downtime(self, cr, uid, ids, context):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        for item in self.browse(cr, uid, ids, context={}):
            downtime = 0
            for dt in item.stops_ids:
                downtime += dt.stop_time
            if downtime:
                self.write(
                    cr, uid, [item.id], {'downtime': downtime},
                    context=context)
        return True

    #------------------------------------------------------------- on_change...

    def on_change_run_time(self, cr, uid, ids, date_start, date_end):
        return {'value': {'run_time': self._compute_run_time(
            cr, uid, date_start, date_end)}}

    ##----------------------------------------------------- create write unlink

    def write(self, cr, uid, ids, vals, context=None):
        invalidate_calc = False
        for key in vals:
            invalidate_calc = invalidate_calc or bool(vals[key])
        if invalidate_calc and not vals.get('valid_cost'):
            vals.update({'valid_cost': False})
        res = super(tcv_mrp_basic_task, self).write(
            cr, uid, ids, vals, context)
        return res

    def unlink(self, cr, uid, ids, context=None):
        so_brw = self.browse(cr, uid, ids, context={})
        unlink_ids = []
        for task in so_brw:
            if task.state == 'draft':
                unlink_ids.append(task['id'])
            else:
                raise osv.except_osv(_('Invalid action !'),
                                     _('Cannot delete task that are ' +
                                       'already Done!'))
        res = super(tcv_mrp_basic_task, self).unlink(cr, uid, ids, context)
        return res

    ##---------------------------------------------------------------- Workflow

    def test_draft(self, cr, uid, ids, *args):
        if len(ids) != 1:
            raise osv.except_osv(_('Error!'),
                                 _('Multiple operations not allowed'))
        for task in self.browse(cr, uid, ids, context=None):
            if task.parent_id.progress > 0 and \
                    task._name != 'tcv.mrp.finished.slab':
                raise osv.except_osv(_('Error!'),
                                     _('Can\'t reset a process with ' +
                                       'proceced outputs'))
            if task.move_id and task.move_id.state != 'draft':
                raise osv.except_osv(_('Error!'), _(
                    'Can\'t reset a process while account move state ' +
                    '<> "Draft"'))
        return True

    def button_draft(self, cr, uid, ids, context=None):
        if self.test_draft(cr, uid, ids, context):
            task = self.browse(cr, uid, ids[0], context=context)
            task_move_id = task.move_id.id if task and task.move_id else False
            task_picking_id = task.picking_id.id if task and \
                task. picking_id else False
            vals = {'state': 'draft', 'move_id': 0, 'picking_id': 0,
                    'operator_cost': 0, 'factory_overhead': 0}
            res = self.write(cr, uid, ids, vals, context)
            if task_move_id:
                self.pool.get('account.move').unlink(
                    cr, uid, [task_move_id], context)
            if task_picking_id:
                self.pool.get('stock.picking').unlink(
                    cr, uid, [task_picking_id], context)
                #~ self.reverse_stock_picking(cr,uid,task_picking_id,context)
            return res

    def test_done(self, cr, uid, ids, *args):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        for item in self.browse(cr, uid, ids, context={}):
            if not item.valid_cost:
                raise osv.except_osv(_('Error!'),
                                     _('You must calculate cost ' +
                                       'distribution first!'))
        return True

    def do_before_done(self, cr, uid, ids, context=None):
        return True

    def button_done(self, cr, uid, ids, context=None):
        context = context or {}
        if self.test_done(cr, uid, ids, context):
            self.do_before_done(cr, uid, ids, context)
            self.create_account_move(cr, uid, ids, context)
            self.create_stock_picking(cr, uid, ids, context)
            vals = {'state': 'done', 'valid_cost': True}
            return self.write(cr, uid, ids, vals, context)

tcv_mrp_basic_task()


##------------------------------------------------- tcv_mrp_basic_task_supplies


class tcv_mrp_basic_task_supplies(osv.osv):

    _name = 'tcv.mrp.basic.task.supplies'

    _description = ''

    ##-------------------------------------------------------------------------

    ##--------------------------------------------------------- function fields

    def _get_unit_price(self, cr, uid, ids, name, arg, context=None):
        if context is None:
            context = {}
        if not len(ids):
            return []
        res = {}
        obj_cst = self.pool.get('tcv.cost.management')
        for item in self.browse(cr, uid, ids, context={}):
            res[item.id] = {}
            unit_price = obj_cst.get_tcv_cost(
                cr, uid, item.prod_lot_id.id, item.product_id.id, context)
            res[item.id]['unit_price'] = unit_price
            res[item.id]['amount'] = unit_price * item.quantity
        return res

    ##-------------------------------------------------------------------------

    _columns = {
        'task_id': fields.many2one(
            'tcv.mrp.basic.task', 'Supplies',
            required=True, ondelete='cascade'),
        'date_start': fields.related(
            'task_id', 'date_start', type='datetime', string='Date started',
            store=False, readonly=True),
        'date_end': fields.related(
            'task_id', 'date_end', type='datetime', string='Date finished',
            store=False, readonly=True),
        'product_id': fields.many2one(
            'product.product', 'Product', ondelete='restrict',
            required=True),
        'prod_lot_id': fields.many2one(
            'stock.production.lot', 'lot #'),
        'quantity': fields.float(
            'Quantity', digits_compute=dp.get_precision('Product UoM'),
            required=True),
        'unit_price': fields.function(
            _get_unit_price, method=True, type='float', string='Unit price',
            digits_compute=dp.get_precision('Account'), multi='all'),
        'amount': fields.function(
            _get_unit_price, method=True, type='float', string='Amount',
            digits_compute=dp.get_precision('Account'), multi='all'),
        }

    _defaults = {
        }

    _sql_constraints = [
        ('quantity_gt_zero', 'CHECK (quantity>0)',
         'The quantity of supplies must be > 0!'),
        ]

    ##-------------------------------------------------------------------------

    def _get_total_supplies_cost(self, cr, uid, ids, context):
        total = 0.0
        for item in self.browse(cr, uid, ids, context={}):
            total += item.amount
        return total

    ##------------------------------------------------------------ on_change...

    def on_change_prod_lot_id(self, cr, uid, ids, prod_lot_id):
        res = {}
        if prod_lot_id:
            obj_lot = self.pool.get('stock.production.lot')
            lot_brw = obj_lot.browse(cr, uid, prod_lot_id, context=None)
            res.update({'product_id': lot_brw.product_id.id})
        return {'value': res}

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_mrp_basic_task_supplies()

##---------------------------------------------------- tcv_mrp_basic_task_costs


class tcv_mrp_basic_task_costs(osv.osv):

    _name = 'tcv.mrp.basic.task.costs'

    _description = 'Calc basic costs'

    #~ _rec_name='prod_lot_id'

    ##-------------------------------------------------------------------------

    ##--------------------------------------------------------- function fields

    _columns = {
        'task_id': fields.many2one(
            'tcv.mrp.basic.task', 'costs', required=False, ondelete='cascade'),
        'cumulative_cost': fields.float(
            'Cumulative cost', digits_compute=dp.get_precision('Account'),
            readonly=False, help="Cumulative cost of processed products"),
        'supplies_cost': fields.float(
            'Supplies cost', digits_compute=dp.get_precision('Account'),
            readonly=False, help="Cost of supplies used, distributed " +
            "according to the relative area"),
        'operator_cost': fields.float(
            'Operator cost', digits_compute=dp.get_precision('Account'),
            readonly=False, help="Labor cost determined based on runtime, " +
            "distributed according to the relative area, use the factor of " +
            "the template: operator_cost"),
        'factory_overhead': fields.float(
            'Factory overhead', digits_compute=dp.get_precision('Account'),
            readonly=False, help="Factory overhead determined based on " +
            "runtime, distributed according to the relative area, use the " +
            "factor of the template: factory_overhead"),
        'real_unit_cost': fields.float(
            'Unit cost', digits_compute=dp.get_precision('MRP unit cost'),
            readonly=True),
        'total_cost': fields.float(
            'Total cost', digits_compute=dp.get_precision('Account'),
            readonly=False),
        }

    _defaults = {
        'cumulative_cost': lambda *a: 0.0,
        'supplies_cost': lambda *a: 0.0,
        'operator_cost': lambda *a: 0.0,
        'factory_overhead': lambda *a: 0.0,
        'real_unit_cost': lambda *a: 0.0,
        'total_cost': lambda *a: 0.0,
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_mrp_basic_task_costs()

##---------------------------------------------------- tcv_mrp_basic_task_stops


class tcv_mrp_basic_task_stops(osv.osv):

    _name = 'tcv.mrp.basic.task.stops'

    _description = ''

    _order = 'stop_start'

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    def _compute_all_fields(self, cr, uid, ids, name, arg, context=None):
        context = context or {}
        if not len(ids):
            return []
        res = {}
        obj_tsk = self.pool.get('tcv.mrp.basic.task')
        for item in self.browse(cr, uid, ids, context={}):

            stop_time = obj_tsk._compute_run_time(
                cr, uid, item.stop_start, item.stop_end, context)
            res[item.id] = {'stop_time': stop_time,
                            }
        return res

    ##-------------------------------------------------------------------------

    _columns = {
        'task_id': fields.many2one(
            'tcv.mrp.basic.task', 'Stops', required=True, ondelete='cascade'),
        'parent_id': fields.related(
            'task_id', 'parent_id', type='many2one',
            relation='tcv.mrp.subprocess', string='Subprocess',
            store=False, readonly=True),
        'template_id': fields.related(
            'parent_id', 'template_id', type='many2one',
            relation='tcv.mrp.template', string='Task template',
            store=False, readonly=True),
        'stop_issue_id': fields.many2one(
            'tcv.mrp.stops.issues', 'Issue', readonly=False, required=True,
            ondelete='restrict'),
        'name': fields.char(
            'Description', size=256, required=False, readonly=False),
        'stop_start': fields.datetime(
            'Stop start', required=True, readonly=False,
            help="Date on which this stop has been started."),
        'stop_end': fields.datetime(
            'Stop end', required=True, select=True, readonly=False,
            help="Date on which this stop has been finished."),
        'stop_time': fields.function(
            _compute_all_fields, method=True, type='float',
            string='Stop time', multi='all',
            help="The stop time in hours (the decimal part represents " +
            "the hour's fraction 0.50 = 30 min) (minus downtime)."),
        'employee_id': fields.many2one(
            'hr.employee', "Operator", required=False, ondelete='restrict',
            help="Machine operator name"),
        }

    _defaults = {
        }

    _sql_constraints = [
        ('stop_time_gt_zero', 'CHECK (stop_start<stop_end)',
         'The stop time must be > 0 !'),
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    def on_change_stop_time(self, cr, uid, ids, stop_start, stop_end):
        obj_tsk = self.pool.get('tcv.mrp.basic.task')
        return {'value':
                {'stop_time': obj_tsk._compute_run_time(
                    cr, uid, stop_start, stop_end)}}

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_mrp_basic_task_stops()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
