# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2018-10-16
#    Version: 0.0.0.1
#
#    Description:
#
#
##############################################################################

# ~ from datetime import datetime
from osv import fields, osv
from tools.translate import _
# ~ import pooler
import decimal_precision as dp
import time
# ~ import netsvc

##------------------------------------------------------------- tcv_consignment


class tcv_consignment(osv.osv):

    _name = 'tcv.consignment'

    _description = ''

    _stock_picking_type = 'out'

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def _get_type(self, cr, uid, context=None):
        context = context or {}
        return context.get('consignment_type', 'out_consignment')

    ##--------------------------------------------------------- function fields

    _columns = {
        'name': fields.char(
            'Reference', size=64, required=False, readonly=True),
        'date': fields.date(
            'Date', required=True, readonly=True,
            states={'draft': [('readonly', False)]}, select=True),
        'partner_id': fields.many2one(
            'res.partner', 'Partner', change_default=True,
            readonly=True, required=True,
            states={'draft': [('readonly', False)]}, ondelete='restrict'),
        'user_id': fields.many2one(
            'res.users', 'User', readonly=True, select=True,
            ondelete='restrict'),
        'narration': fields.text(
            'Notes', readonly=False),
        'line_ids': fields.one2many(
            'tcv.consignment.lines', 'line_id', 'Detail',
            readonly=True, states={'draft': [('readonly', False)]}),
        'type': fields.selection(
            [('in_consignment', 'In consignment'),
             ('out_consignment', 'Out consignment')],
            string='Type', required=True, readonly=True),
        'state': fields.selection(
            [('draft', 'Draft'), ('done', 'Done'), ('cancel', 'Cancelled')],
            string='State', required=True, readonly=True),
        'move_id': fields.many2one(
            'account.move', 'Accounting entries', ondelete='restrict',
            help="The move of this entry line.", select=True, readonly=True),
        'picking_id': fields.many2one(
            'stock.picking', 'Picking', readonly=True, ondelete='restrict',
            help="The picking for this entry line")
        }

    _defaults = {
        'name': lambda *a: '/',
        'type': _get_type,
        'user_id': lambda s, c, u, ctx: u,
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        'state': lambda *a: 'draft',
        }

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', 'The name must be unique!'),
        ]

    ##-------------------------------------------------------------------------

    def _create_model_account_move_lines(self, cr, uid, task, lines, context):
        '''
        Must be overridden in models inherited
        Here you create and return a acount.move.lines (list of dict)
        task is a task.browse object
        return a sum of created lines amounts
        '''
        return 0.0

    def _create_model_stock_move_lines(self, cr, uid, task, lines,
                                       context=None):
        return lines

    ##---------------------------------------------------------- public methods



    def create_stock_move_lines(self, cr, uid, task, lines, context=None):

        '''
        task is a task.browse object
        '''
        if lines is None:
            lines = []
        if context is None:
            context = {}

        name = '/'
        context.update({'task_name': name})

        # inherited models extra lines
        lines = []
        lines = self._create_model_stock_move_lines(
            cr, uid, task, lines, context)

        return lines


    def create_account_move_lines(self, cr, uid, task, lines=None,
                                  context=None):
        '''
        task is a task.browse object
        '''
        if lines is None:
            lines = []

        #~ company_id = context.get('task_company_id')
        #~ total_amount = 0.0
        name = self._columns['name']

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
                account_id,
                _('%s: %s') % (cost_supp.product_id.name, name), 0.0,
                cost_supp.amount))
            lines.append(self._gen_account_move_line(
                acc_cost_id,
                _('%s: %s') % (cost_supp.product_id.name, name),
                cost_supp.amount, 0.0))

        # Operator & factory overhead
        for cost_line in task.costs_ids:

            settings = self._account_move_settings()
            # operator and factory overhead
            fo_oc_cost = 0
            for key in settings:
                amount = getattr(cost_line, key, 0.0)
                if amount != 0.0:
                    #~ total_amount += amount
                    lines.append(self._gen_account_move_line(
                        account_id, _('%s: %s') %
                        (settings[key]['name'], name), 0.0, amount))
                    if not settings[key].get('isproduct'):
                        fo_oc_cost += amount
                    else:
                        acc_cost_id = self._get_settings_acc_cost_id(
                            cr, uid, key, cost_line, task)
                        lines.append(self._gen_account_move_line(
                            acc_cost_id, _('%s: %s') %
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
            if not account_id:
                raise osv.except_osv(
                    _('Error!'),
                    _('No output product account found, please check ' +
                      'product and category account settings (%s)') %
                    product.name)
            #  Added to fix very low cost special case (roundig error)
            if total_cost - fo_oc_cost < 0 and \
                    total_cost - fo_oc_cost > -0.02:
                fo_oc_cost += total_cost - fo_oc_cost
            lines.append(self._gen_account_move_line(
                acc_cost_id, _('%s: %s') %
                (product.name, name), 0.0, total_cost - fo_oc_cost))
            lines.append(self._gen_account_move_line(
                account_id, _('%s: %s') %
                (product.name, name), total_cost, 0.0))
        self._check_rounding_diff(lines, name, context)
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
            date = task.date  # stock_move.date = start of task
            context.update({'task_company_id': company_id,
                            'task_config': mrp_cfg,
                            'task_date': date})
            #~ origin = '[%s - %s] %s' % (
                #~ task.parent_id.process_id.ref, task.parent_id.ref,
                #~ task.name) if task.name else '[%s - %s] %s' % (
                    #~ task.parent_id.process_id.ref, task.parent_id.ref,
                    #~ task.parent_id.template_id.name)
            origin = self._columns['name'],
            picking = {'name': '/',
                       'type': self._stock_picking_type,
                       'origin': origin,
                       'date': date,
                       'invoice_state': 'none',
                       'stock_journal_id': mrp_cfg.stock_journal_id.id,
                       'company_id': company_id,
                       'auto_picking': False,
                       'move_type': 'one',
                       'partner_id': company.partner_id.id,
                       'state_rw': 0,
                       'note': _('Date: %s - %s\n\tInfo: %s') % (
                               task.date, task.date, task.date),
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

    ##-------------------------------------------------------- buttons (object)

    def button_lot_list(self, cr, uid, ids, context=None):
        return True
        # ~ ids = isinstance(ids, (int, long)) and [ids] or ids
        # ~ so_brw = self.browse(cr, uid, ids, context={})[0]
        # ~ context.update({'sale_order_id': so_brw.id,
                        # ~ 'default_sale_id': so_brw.id,
                        # ~ 'default_partner_id': so_brw.partner_id.id,
                        # ~ })
        # ~ return {'name': _('Load lot list'),
                # ~ 'type': 'ir.actions.act_window',
                # ~ 'res_model': 'tcv.sale.lot.list',
                # ~ 'view_type': 'form',
                # ~ 'view_id': False,
                # ~ 'view_mode': 'form',
                # ~ 'nodestroy': True,
                # ~ 'target': 'new',
                # ~ 'domain': "",
                # ~ 'context': context}

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    def create(self, cr, uid, vals, context=None):
        context = context or {}
        if not vals.get('name') or vals.get('name') == '/':
            if context.get('consignment_type') == 'out_consignment':
                seq_name = 'tcv.consignment.sale'

            elif context.get('consignment_type') == 'in_consignment':
                seq_name = 'tcv.consignment.purchase'
            else:
                raise osv.except_osv(
                    _('Error!'),
                    _('Must indicate consignment_type in context'))
            vals.update({
                'name': self.pool.get('ir.sequence').get(cr, uid, seq_name),
                })
        res = super(tcv_consignment, self).create(
            cr, uid, vals, context)
        return res

    ##---------------------------------------------------------------- Workflow

    def button_draft(self, cr, uid, ids, context=None):
        vals = {'state': 'draft'}
        return self.write(cr, uid, ids, vals, context)

    def button_done(self, cr, uid, ids, context=None):
        pickind_id = self.create_stock_picking(cr, uid, ids, context)
        move_id = self.create_account_move(cr, uid, ids, context)
        vals = {
            'state': 'done',
            'pickind_id': pickind_id,
            'move_id': move_id,
            }
        return self.write(cr, uid, ids, vals, context)

    def button_cancel(self, cr, uid, ids, context=None):
        vals = {'state': 'cancel'}
        return self.write(cr, uid, ids, vals, context)

    def test_draft(self, cr, uid, ids, *args):
        return True

    def test_done(self, cr, uid, ids, *args):
        return True

    def test_cancel(self, cr, uid, ids, *args):
        return True


tcv_consignment()


##------------------------------------------------------- tcv_consignment_lines


class tcv_consignment_lines(osv.osv):

    _name = 'tcv.consignment.lines'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'line_id': fields.many2one(
            'tcv.consignment', 'Line', required=True, ondelete='cascade'),
        'name': fields.char(
            'Name', size=64, required=False, readonly=False),
        'prod_lot_id': fields.many2one(
            'stock.production.lot', 'Production lot', required=True),
        'product_id': fields.related(
            'prod_lot_id', 'product_id', type='many2one',
            relation='product.product', string='Product', store=False,
            readonly=True),
        'quantity': fields.float(
            'quantity', digits_compute=dp.get_precision('Product UoM')),
        'pieces': fields.integer(
            'Pieces'),
        }

    _defaults = {
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    def on_change_prod_lot_id(self, cr, uid, ids, prod_lot_id):
        res = {}
        if not prod_lot_id:
            return {'value': res}
        obj_lot = self.pool.get('stock.production.lot')
        lot = obj_lot.browse(cr, uid, prod_lot_id, context=None)
        res.update({
            'product_id': lot.product_id.id,
            'quantity': lot.stock_available,
            'pieces': round(lot.stock_available / lot.lot_factor, 0),
            })
        return {'value': res}

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow


tcv_consignment_lines()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
