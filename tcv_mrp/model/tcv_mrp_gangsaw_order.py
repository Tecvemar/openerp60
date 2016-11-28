# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2016-03-08
#    Version: 0.0.0.1
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
from itertools import count, product, islice
from string import ascii_uppercase
from datetime import datetime, timedelta

##------------------------------------------------------- tcv_mrp_gangsaw_order


class tcv_mrp_gangsaw_order(osv.osv):

    _name = 'tcv.mrp.gangsaw.order'

    _description = ''

    _order = 'ref desc'

    ##-------------------------------------------------------------------------

    def name_get(self, cr, uid, ids, context):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        res = []
        for item in self.browse(cr, uid, ids, context={}):
            res.append(
                (item.id, '[%s] %s' % (item.ref, item.template_id.name)))
        return res

    ##------------------------------------------------------- _internal methods

    def _get_supplies_yield(self, cr, uid,
                            template_id, product_id, supplie_id):
        if not(template_id and product_id and supplie_id):
            return 0
        sql = '''
        select supplie_id, product_id,
               round(avg(yield), 3) as avg_yield
        from (
            select product_id, supplie_id,
                   round((quantity*round(vol/total_vol, 3))/area,3) as yield
            from (
                select b.product_id, p.name,
                       round((b.net_length*b.net_heigth*b.slab_qty),4) as area,
                       round((length*heigth*width),4) as vol,
                       tb.total_vol,
                       p2.id as supplie_id,
                       s.quantity
                from tcv_mrp_gangsaw g
                left join tcv_mrp_gangsaw_blocks b on b.gangsaw_id = g.id
                left join tcv_mrp_subprocess sp on g.parent_id = sp.id
                left join tcv_mrp_template t on sp.template_id = t.id
                left join stock_production_lot l on b.prod_lot_id = l.id
                left join product_template p on b.product_id = p.id
                left join tcv_mrp_gangsaw_supplies s on g.id = s.task_id
                left join product_template p2 on s.product_id = p2.id
                left join (
                    select gangsaw_id,
                       round(sum(length*heigth*width),4) as total_vol
                    from tcv_mrp_gangsaw_blocks
                    left join stock_production_lot spl on prod_lot_id = spl.id
                    where gangsaw_id=tcv_mrp_gangsaw_blocks.gangsaw_id
                    group by gangsaw_id) tb on tb.gangsaw_id = b.gangsaw_id
                where g.date_end > '2015-01-01 00:00:00' and
                      t.id = %s
                ) as q1
            ) as q2 where supplie_id = %s and product_id = %s
        group by supplie_id, product_id
        order by supplie_id, product_id
        '''
        cr.execute(sql % (template_id, supplie_id, product_id))
        res = cr.dictfetchall()
        return res and res[0].get('avg_yield', 0) or 0

    def _compute_cut_down_feed(self, cr, uid, item, context):
        '''
        item: browse object -> tcv.mrp.gangsaw.order.lines
        return cut_down_feed
        '''
        obj_gbl = self.pool.get('tcv.mrp.gangsaw.blocks')
        gbl_ids = obj_gbl.search(
            cr, uid, [
                ('date_end', '>=', '2015-01-01 00:00:00'),
                ('product_id', '=', item.product_id.id),
                ('template_id', '=', item.gangsaw_order_id.template_id.id),
                ])
        total_cdf = 0.0
        qty = 0.0
        for item in obj_gbl.browse(cr, uid, gbl_ids, context={}):
            total_cdf += item.cut_down_feed
            qty += 1
        return total_cdf / qty if qty else 0

    def _create_process(self, cr, uid, item, context):
        obj_prc = self.pool.get('tcv.mrp.process')
        data = {'date': time.strftime('%Y-%m-%d'),
                'name': item.name}
        return obj_prc.create(cr, uid, data, context)

    def _create_subprocess(self, cr, uid, item, process_id, context):
        obj_prc = self.pool.get('tcv.mrp.subprocess')
        data = {'template_id': item.template_id.id,
                'process_id': process_id,
                'name': item.template_id.name}
        return obj_prc.create(cr, uid, data, context)

    def _create_gangsaw(self, cr, uid, item, process_id, subprocess_id,
                        context):
        obj_prc = self.pool.get('tcv.mrp.gangsaw')
        obj_tmp = self.pool.get('tcv.mrp.template')
        new_blade_heigth = obj_tmp.get_var_value(
            cr, uid, item.template_id.id, 'new_blade_heigth') or 0
        supplies = [(0, 0, {'product_id': x.product_id.id,
                            'quantity': x.product_qty or 100
                            })
                    for x in item.supplies_ids]
        blocks = [(0, 0, {'prod_lot_id': x.prod_lot_id.id,
                          'block_ref': x.block_ref,
                          'net_length': x.length,
                          'net_heigth': x.heigth,
                          'thickness': x.thickness,
                          'blade_id': item.blade_id.id,
                          'blade_qty': x.blade_qty,
                          'slab_qty': x.blade_qty - 1,
                          'blade_start': new_blade_heigth,
                          'blade_end': new_blade_heigth - x.blade_heigth_used,
                          })
                  for x in item.line_ids]
        date_end = (
            datetime.strptime(item.date_start, '%Y-%m-%d %H:%M:%S') +
            timedelta(hours=item.run_time or 96)).strftime(
            '%Y-%m-%d %H:%M:%S')
        data = {'parent_id': subprocess_id,
                'narration': _('Gangsaw order: %s') % item.ref,
                'date_start': item.date_start,
                'date_end': date_end,
                'supplies_ids': supplies,
                'gangsaw_ids': blocks,
                }
        return obj_prc.create(cr, uid, data, context)

    def _notify_users(self, cr, uid, ids, context=None):
        request = self.pool.get('res.request')
        obj_cfg = self.pool.get('tcv.mrp.config')
        company_id = self.pool.get('res.users').browse(
            cr, uid, uid, context=context).company_id.id
        cfg_id = obj_cfg.search(cr, uid, [('company_id', '=', company_id)])
        if cfg_id:
            mrp_cfg = obj_cfg.browse(cr, uid, cfg_id[0], context=context)
        for item in self.browse(cr, uid, ids, context=context):
            if mrp_cfg.block_check_user_id and mrp_cfg.block_check_user_id.id:
                block_lines = []
                for block in item.line_ids:
                    block_lines.append(_('Block: %s - %s') % (
                        block.prod_lot_id.name, block.product_id.name))
                rq_id = request.create(
                    cr, uid, {
                        'name': _("Check block cost (%s)") % item.ref,
                        'act_from': uid,
                        'act_to': mrp_cfg.block_check_user_id.id,
                        'body': '\n'.join(block_lines),
                        'trigger_date': time.strftime('%Y-%m-%d %H:%M:%S')
                        }, context)
                request.request_send(cr, uid, [rq_id])
        return True

    ##--------------------------------------------------------- function fields

    def _compute_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for item in self.browse(cr, uid, ids, context=context):
            if item.date_start and item.run_time:
                date_end = (
                    datetime.strptime(item.date_start, '%Y-%m-%d %H:%M:%S') +
                    timedelta(hours=item.run_time or 96)).strftime(
                    '%Y-%m-%d %H:%M:%S')
                res[item.id] = {'date_end': date_end}
            else:
                res[item.id] = {'date_end': item.date_start}
            throwput = 0
            for l in item.line_ids:
                throwput += l.throwput
            res[item.id].update({'throwput': throwput})
        return res

    ##-------------------------------------------------------------------------

    _columns = {
        'ref': fields.char(
            'Reference', size=64, required=False, readonly=True),
        'name': fields.char(
            'Info', size=128, required=False, readonly=False),
        'template_id': fields.many2one(
            'tcv.mrp.template', 'Task template', required=True,
            ondelete='restrict', readonly=True,
            states={'draft': [('readonly', False)]},
            domain=[('res_model', '=', 'tcv.mrp.gangsaw')]),
        'blade_id': fields.many2one(
            'product.product', 'Blade / Product',
            ondelete='restrict', required=False,
            help="The product (blade) used, using the factor " +
            "of the template: default_blade_product"),
        'date': fields.date(
            'Date', required=True, readonly=True,
            states={'draft': [('readonly', False)]}, select=True,
            help="Gangsaw order\s date"),
        'date_start': fields.datetime(
            'Date started', required=False, readonly=False,
            states={'done': [('readonly', True)]}, select=True,
            help="Date when the process in planned to start."),
        'date_end': fields.function(
            _compute_all, method=True, type='datetime', string='Date finished',
            multi='all', help="Estimated date end"),
        'run_time': fields.float(
            'Production runtime', readonly=True,
            digits_compute=dp.get_precision('Account'),
            help="Estimated production time in hours (the decimal part " +
            "represents the hour's fraction 0.50 = 30 min) (minus downtime)."),
        'employee_id': fields.many2one(
            'hr.employee', "Operator", required=False, ondelete='restrict',
            readonly=False, states={'done': [('readonly', True)]}),
        'state': fields.selection(
            [('draft', 'Draft'), ('to_produce', 'To produce'),
             ('in_progress', 'In progress'), ('done', 'Done'),
             ('cancel', 'Cancelled')],
            string='State', required=True, readonly=True,
            help="'Draft': User\'s state (data transcription) no process " +
                 "started\n" +
                 "'To produce': Blocks ready to be loaded (in load\'s car)\n" +
                 "'In progress': Blocks in cutting process (gangsaw)\n" +
                 "'Done': Blocks gangsaw done."),
        'line_ids': fields.one2many(
            'tcv.mrp.gangsaw.order.lines', 'gangsaw_order_id', 'Blocks',
            readonly=True, states={'draft': [('readonly', False)]}),
        'supplies_ids': fields.one2many(
            'tcv.mrp.gangsaw.order.supplies', 'gangsaw_order_id',
            'Supplies', readonly=True),
        'narration': fields.text(
            'Notes', readonly=False),
        'company_id': fields.many2one(
            'res.company', 'Company', required=True, readonly=True,
            ondelete='restrict'),
        'params_id': fields.many2one(
            'tcv.mrp.gangsaw.params', 'Params', required=True, readonly=True,
            ondelete='restrict'),
        'process_id': fields.many2one(
            'tcv.mrp.process', 'Process', readonly=True,
            ondelete='restrict'),
        'subprocess_id': fields.many2one(
            'tcv.mrp.subprocess', 'Subprocess', readonly=True,
            ondelete='set null'),
        'gangsaw_id': fields.many2one(
            'tcv.mrp.gangsaw', 'Gangsaw', readonly=True,
            ondelete='set null'),
        'throwput': fields.function(
            _compute_all, method=True, store=False, type='float',
            string='Throwput (E)',
            digits_compute=dp.get_precision('Product UoM'), multi='all'),
        }

    _defaults = {
        'ref': lambda *a: '/',
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        'state': lambda *a: 'draft',
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company').
        _company_default_get(cr, uid, self._name, context=c),
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    def clear_supplies_lines(self, cr, uid, item, context):
        unlink_ids = []
        for l in item.supplies_ids:
            unlink_ids.append(l.id)
        obj_lin = self.pool.get('tcv.mrp.gangsaw.order.supplies')
        if unlink_ids:
            obj_lin.unlink(cr, uid, unlink_ids, context=context)
        return unlink_ids

    ##-------------------------------------------------------- buttons (object)

    def button_compute(self, cr, uid, ids, context=None):
        '''
        Compute supplies qty and run_time
        '''
        obj_tmp = self.pool.get('tcv.mrp.template')
        obj_lin = self.pool.get('tcv.mrp.gangsaw.order.lines')
        obj_uom = self.pool.get('product.uom')
        for item in self.browse(cr, uid, ids, context={}):
            steel_grit_prd = obj_tmp.get_var_value(
                cr, uid, item.template_id.id, 'default_steel_grit_product')
            steel_grit_id = self.pool.get('product.product').search(
                cr, uid, [('default_code', '=', steel_grit_prd)])[0]
            steel_grit_qty = 0
            lime_prd = obj_tmp.get_var_value(
                cr, uid, item.template_id.id, 'default_lime_product')
            lime_id = self.pool.get('product.product').search(
                cr, uid, [('default_code', '=', lime_prd)])[0]
            lime_qty = 0
            run_time = 0
            for line in item.line_ids:
                #~ Compute and update blade_qty
                blade_qty = obj_lin._compute_blade_qty(
                    cr, uid, line.width, line.thickness,
                    item.template_id.id)
                #~ compute throwput
                throwput = obj_uom._calc_area(
                    blade_qty - 1, line.length, line.heigth)
                #~ compute runtime
                line_cdf = self._compute_cut_down_feed(
                    cr, uid, line, context) or 999
                line_run_time = round(line.heigth * 1000 / line_cdf, 2)
                if line_run_time > run_time:
                    run_time = line_run_time
                #~ Compute supplies
                steel_grit_qty += round(
                    self._get_supplies_yield(
                        cr, uid, item.template_id.id, line.product_id.id,
                        steel_grit_id) *
                    throwput / 10, 0) * 10
                lime_qty += round(
                    self._get_supplies_yield(
                        cr, uid, item.template_id.id, line.product_id.id,
                        lime_id) *
                    throwput / 10, 0) * 10
                obj_lin.write(
                    cr, uid, [line.id], {'blade_qty': blade_qty},
                    context=context)
            values = [
                {'product_id': steel_grit_id, 'product_qty': steel_grit_qty},
                {'product_id': lime_id, 'product_qty': lime_qty}
                ]
            data = [(0, 0, x) for x in values]
            self.clear_supplies_lines(cr, uid, item, context)
            self.write(cr, uid, [item.id], {'supplies_ids': data,
                                            'run_time': run_time},
                       context=context)
        return True

    ##------------------------------------------------------------ on_change...

    def on_change_template_id(self, cr, uid, ids, template_id):
        res = {}
        if template_id:
            obj_tmp = self.pool.get('tcv.mrp.template')
            blade_prd = obj_tmp.get_var_value(
                cr, uid, template_id, 'default_blade_product')
            blade_id = self.pool.get('product.product').search(
                cr, uid, [('default_code', '=', blade_prd)])
            obj_prm = self.pool.get('tcv.mrp.gangsaw.params')
            params_id = obj_prm.search(
                cr, uid, [('template_id', '=', template_id)])
        res.update({'blade_id': blade_id and blade_id[0],
                    'params_id': params_id and params_id[0]})
        return {'value': res}

    ##----------------------------------------------------- create write unlink

    def create(self, cr, uid, vals, context=None):
        if not vals.get('ref') or vals.get('ref') == '/':
            vals.update({'ref': self.pool.get('ir.sequence').get(
                cr, uid, 'tcv.mrp.gangsaw.order')})
        if not vals.get('blade_id'):
            obj_tmp = self.pool.get('tcv.mrp.template')
            blade_prd = obj_tmp.get_var_value(
                cr, uid, vals.get('template_id'), 'default_blade_product')
            blade_id = self.pool.get('product.product').search(
                cr, uid, [('default_code', '=', blade_prd)])
            vals.update({'blade_id': blade_id and blade_id[0]})
        if not vals.get('params_id'):
            obj_prm = self.pool.get('tcv.mrp.gangsaw.params')
            params_id = obj_prm.search(
                cr, uid, [('template_id', '=', vals.get('template_id'))])
            vals.update({'params_id': params_id and params_id[0]})
        res = super(tcv_mrp_gangsaw_order, self).create(
            cr, uid, vals, context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        if vals.get('template_id'):
            obj_tmp = self.pool.get('tcv.mrp.template')
            blade_prd = obj_tmp.get_var_value(
                cr, uid, vals.get('template_id'), 'default_blade_product')
            blade_id = self.pool.get('product.product').search(
                cr, uid, [('default_code', '=', blade_prd)])
            vals.update({'blade_id': blade_id and blade_id[0]})
            obj_prm = self.pool.get('tcv.mrp.gangsaw.params')
            params_id = obj_prm.search(
                cr, uid, [('template_id', '=', vals.get('template_id'))])
            vals.update({'params_id': params_id and params_id[0]})
        res = super(tcv_mrp_gangsaw_order, self).write(
            cr, uid, ids, vals, context)
        return res

    ##---------------------------------------------------------------- Workflow

    def button_draft(self, cr, uid, ids, context=None):
        vals = {'state': 'draft'}
        return self.write(cr, uid, ids, vals, context)

    def button_to_produce(self, cr, uid, ids, context=None):
        '''
        Assign block letter secuence.
        see:
        http://stackoverflow.com/questions/14381940/
        python-pair-alphabets-after-loop-is-completed
        '''

        def multiletters(seq):
            for n in count(1):
                for s in product(seq, repeat=n):
                    yield ''.join(s)

        vals = {'state': 'to_produce'}
        res = self.write(cr, uid, ids, vals, context)
        obj_blk = self.pool.get('tcv.mrp.gangsaw.order.lines')
        obj_tmp = self.pool.get('tcv.mrp.template')
        for item in self.browse(cr, uid, ids, context={}):
            block_list = []
            for block in item.line_ids:
                if not block.block_ref:
                    block_num = int(self.pool.get('ir.sequence').get(
                        cr, uid, 'tcv.mrp.gangsaw.order.lines'))
                    block_ref = list(islice(
                        multiletters(ascii_uppercase), block_num))[-1]
                    obj_blk.write(
                        cr, uid, [block.id], {'block_ref': block_ref},
                        context=context)
                else:
                    block_ref = block.block_ref
                block_list.append('[%s] %s (%s)' % (
                    block.product_id.default_code, block.prod_lot_id.name,
                    block_ref))
            ref_name = obj_tmp.get_var_value(
                cr, uid, item.template_id.id,
                'ref_name') or ''
            name = '%s - %s' % (ref_name, ', '. join(block_list))
            self.write(cr, uid, ids, {'name': name}, context)
        self._notify_users(cr, uid, ids, context)
        return res

    def button_in_progress(self, cr, uid, ids, context=None):
        vals = {'state': 'in_progress'}
        return self.write(cr, uid, ids, vals, context)

    def button_done(self, cr, uid, ids, context=None):
        for item in self.browse(cr, uid, ids, context={}):
            data = {}
            #~ process
            if not item.process_id:
                process_id = self._create_process(
                    cr, uid, item, context)
                data.update({'process_id': process_id})
            else:
                process_id = item.process_id.id
            #~ subprocess
            if not item.subprocess_id:
                subprocess_id = self._create_subprocess(
                    cr, uid, item, process_id, context)
                data.update({'subprocess_id': subprocess_id})
            else:
                subprocess_id = item.subprocess_id.id
            #~ gangsaw
            if not item.gangsaw_id:
                gangsaw_id = self._create_gangsaw(
                    cr, uid, item, process_id, subprocess_id, context)
                data.update({'gangsaw_id': gangsaw_id})
            if data:
                self.write(cr, uid, [item.id], data, context)
        vals = {'state': 'done'}
        return self.write(cr, uid, ids, vals, context)

    def button_cancel(self, cr, uid, ids, context=None):
        vals = {'state': 'cancel'}
        return self.write(cr, uid, ids, vals, context)

    def test_draft(self, cr, uid, ids, *args):
        return True

    def test_done(self, cr, uid, ids, *args):
        for item in self.browse(cr, uid, ids, context={}):
            if not item.date_start:
                raise osv.except_osv(
                    _('Error!'),
                    _('Must indicate date started'))
        return True

    def test_in_progress(self, cr, uid, ids, *args):
        for item in self.browse(cr, uid, ids, context={}):
            if not item.date_start:
                raise osv.except_osv(
                    _('Error!'),
                    _('Must indicate date started'))
            if item.gangsaw_id or item.subprocess_id:
                raise osv.except_osv(
                    _('Error!'),
                    _('Can\'t reset an order with related gangsaw data. ' +
                      'Must delete gangsaw data manually first'))
        return True

    def test_to_produce(self, cr, uid, ids, *args):
        return True

    def test_cancel(self, cr, uid, ids, *args):
        return True

tcv_mrp_gangsaw_order()


##------------------------------------------------- tcv_mrp_gangsaw_order_lines


class tcv_mrp_gangsaw_order_lines(osv.osv):

    _name = 'tcv.mrp.gangsaw.order.lines'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def _compute_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        obj_uom = self.pool.get('product.uom')
        obj_tmp = self.pool.get('tcv.mrp.template')
        sql = '''
        select product_id, template_id,
               round(cast(avg(blade_yield) as numeric), 3) as blade_yield
        from (
            select pt.id as product_id, sp.template_id,
                   (b.blade_start - b.blade_end) - b.net_heigth as blade_yield
            from tcv_mrp_gangsaw g
            left join tcv_mrp_gangsaw_blocks b on b.gangsaw_id = g.id
            left join product_product pp on b.product_id = pp.id
            left join product_template pt on b.product_id = pt.id
            left join tcv_mrp_subprocess sp on g.parent_id = sp.id
            where g.date_end > '2015-01-01 00:00:00'
            ) as q
        group by product_id, template_id
        order by 1
        '''
        cr.execute(sql)
        yields = {}
        for item in self.browse(cr, uid, ids, context=context):
            if not yields:
                for y in cr.dictfetchall():
                    if y['template_id'] == \
                            item.gangsaw_order_id.template_id.id:
                        yields[y['product_id']] = y['blade_yield']
            blade_useful_height = obj_tmp.get_var_value(
                cr, uid, item.gangsaw_order_id.template_id.id,
                'blade_useful_height') or 0
            new_blade_heigth = obj_tmp.get_var_value(
                cr, uid, item.gangsaw_order_id.template_id.id,
                'new_blade_heigth') or 0

            min_blade_h = new_blade_heigth - blade_useful_height
            blade_heigth_used = yields.get(
                item.product_id.id, 0) * item.heigth
            blade_min_heigth = min_blade_h + blade_heigth_used \
                if blade_heigth_used else 0
            res[item.id] = {
                'throwput': obj_uom._calc_area(item.blade_qty - 1,
                                               item.length, item.heigth),
                'blade_min_heigth': blade_min_heigth,
                'blade_heigth_used': blade_heigth_used,
                }
        return res

    def _compute_blade_qty(self, cr, uid, width, thickness, template_id):
        '''
        compute blades quantity using:

        block width - (2 * flank) / thickness + thickness_factor_correction

        all measures must be set in mm
        '''
        if not (thickness and template_id and width):
            return 0
        obj_tmp = self.pool.get('tcv.mrp.template')
        block_flanks = obj_tmp.get_var_value(
            cr, uid, template_id, 'block_flanks') * 2
        tfc = obj_tmp.get_var_value(
            cr, uid, template_id, 'thickness_factor_correction')
        usefull_width = (width * 1000) - block_flanks * 10
        blade_qty = round(usefull_width / (thickness + tfc), 0) + 1
        return blade_qty

    ##--------------------------------------------------------- function fields

    _columns = {
        'gangsaw_order_id': fields.many2one(
            'tcv.mrp.gangsaw.order', 'Order', required=True,
            ondelete='cascade'),
        'state': fields.related(
            'gangsaw_order_id', 'state', type='string', size=32,
            string='State', store=False, readonly=True),
        'prod_lot_id': fields.many2one(
            'stock.production.lot', 'Block (lot Nº)', required=True),
        'block_ref': fields.char(
            'Block ref', size=8, required=False, readonly=False,
            help="Characters for internal block reference"),
        'product_id': fields.related(
            'prod_lot_id', 'product_id', type='many2one',
            relation='product.product', string='Block / Product',
            store=False, readonly=True),
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
        'throwput': fields.function(
            _compute_all, method=True, store=False, type='float',
            string='Throwput (E)',
            digits_compute=dp.get_precision('Product UoM'), multi='all'),
        'blade_qty': fields.integer(
            'Blade qty', readonly=True),
        'blade_min_heigth': fields.function(
            _compute_all, method=True, store=False, type='float',
            string='Min blade', help="Minimal blade heigth required",
            digits_compute=dp.get_precision('Account'), multi='all'),
        'blade_heigth_used': fields.function(
            _compute_all, method=True, store=False, type='float',
            string='Blade h', help="Estimated blade heigth used",
            digits_compute=dp.get_precision('Account'), multi='all'),
        'thickness': fields.integer(
            'Thickness (mm)', required=False),
        }

    _defaults = {
        'thickness': lambda *a: 20,
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    def button_rotate(self, cr, uid, ids, context=None):
        obj_lot = self.pool.get('stock.production.lot')

        for item in self.browse(cr, uid, ids, context={}):
            if item.prod_lot_id and item.product_id.stock_driver == 'block':
                obj_lot.write(
                    cr, uid, [item.prod_lot_id.id],
                    {'heigth': item.prod_lot_id.width,
                     'width': item.prod_lot_id.heigth}, context=context)
                blade_qty = self._compute_blade_qty(
                    cr, uid, item.width, item.thickness,
                    item.gangsaw_order_id.template_id.id)
                self.write(cr, uid, [item.id], {'blade_qty': blade_qty},
                           context=context)
        return True

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
                                 })
        return res

    ##----------------------------------------------------- create write unlink

    def write(self, cr, uid, ids, vals, context=None):
        if vals.get('blade_qty'):
            res = super(tcv_mrp_gangsaw_order_lines, self).write(
                cr, uid, ids, vals, context)
        else:
            for item in self.browse(cr, uid, ids, context={}):
                blade_qty = self._compute_blade_qty(
                    cr, uid, item.width, item.thickness,
                    item.gangsaw_order_id.template_id.id)
                vals.update({'blade_qty': blade_qty})
                return super(tcv_mrp_gangsaw_order_lines, self).write(
                    cr, uid, ids, vals, context)

        return res

    ##---------------------------------------------------------------- Workflow

tcv_mrp_gangsaw_order_lines()


##---------------------------------------------- tcv_mrp_gangsaw_order_supplies


class tcv_mrp_gangsaw_order_supplies(osv.osv):

    _name = 'tcv.mrp.gangsaw.order.supplies'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'gangsaw_order_id': fields.many2one(
            'tcv.mrp.gangsaw.order', 'Order', required=True,
            ondelete='cascade'),
        'product_id': fields.many2one(
            'product.product', 'Product', ondelete='restrict'),
        'product_qty': fields.integer(
            'Quantity'),
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

tcv_mrp_gangsaw_order_supplies()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
