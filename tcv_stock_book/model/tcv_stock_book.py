# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date: 07/08/2013
#    Version: 0.0.0.0
#
#    Description:
#
#
##############################################################################
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from osv import fields, osv
from tools.translate import _
#~ import pooler
import decimal_precision as dp
import time
#~ import csv
#~ import netsvc


__MOVE_TYPE__ = {
    'internal-customer': '+stock_out',
    'customer-internal': '+stock_in',
    'internal-production': '+stock_self',
    'production-internal': '+stock_in',
    'inventory-internal': '-stock_scrap',
    'internal-inventory': '+stock_scrap',
    'internal-supplier': '+stock_out',
    #~ 'production-inventory': '+stock_scrap', not a valid move
    'supplier-internal': '+stock_in',
    }


##-------------------------------------------------------------- tcv_stock_book


class tcv_stock_book(osv.osv):

    _name = 'tcv.stock.book'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def name_get(self, cr, uid, ids, context):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        res = []
        for item in self.browse(cr, uid, ids, context={}):
            res.append((item.id, '%s' % (item.name or item.period_id.name)))
        return res

    def default_get(self, cr, uid, fields, context=None):
        data = super(tcv_stock_book, self).default_get(
            cr, uid, fields, context)
        bas_date = datetime.strptime(
            time.strftime('%Y-%m-01'), '%Y-%m-%d')
        per_date = bas_date + relativedelta(days=-1)
        obj_per = self.pool.get('account.period')
        period_id = obj_per.find(cr, uid, per_date)[0]
        data.update({'period_id': period_id})
        data.update(self._get_prior_book(cr, uid, period_id, context))
        return data

    def _get_year_month(self, cr, uid, period_id, context=None):
        res = {}
        if not period_id:
            return res
        obj_per = self.pool.get('account.period')
        per_brw = obj_per.browse(cr, uid, period_id, context=context)
        date = time.strptime(per_brw.date_stop, '%Y-%m-%d')
        return {'year': date.tm_year,
                'month': date.tm_mon}

    def _get_prior_book(self, cr, uid, period_id, context=None):
        res = {}
        if not period_id:
            return res
        obj_per = self.pool.get('account.period')
        per_brw = obj_per.browse(cr, uid, period_id, context=None)
        dt = datetime.strptime(per_brw.date_start, '%Y-%m-%d')
        prior_date = (dt - timedelta(days=1)).strftime('%Y-%m-%d')
        prior_period_id = obj_per.find(cr, uid, prior_date)[0]
        if prior_period_id:
            prior_book_id = self.search(
                cr, uid, [('period_id', '=', prior_period_id)])
            if prior_book_id:
                res.update({'prior_book_id': prior_book_id[0]})
        return res

    def _clear_lines(self, cr, uid, ids, context):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        unlink_ids = []
        for item in self.browse(cr, uid, ids, context={}):
            for l in item.line_ids:
                unlink_ids.append((2, l.id))
            self.write(cr, uid, ids, {'line_ids': unlink_ids}, context=context)
        return True

    def _get_prior_book_lines(self, cr, uid, ids, prior_book, context=None):
        lines = []
        for l in prior_book.line_ids:
            if abs(l.stock_end) >= 0.0001:
                lines.append((0, 0, {
                    'product_id': l.product_id.id,
                    'stock_init': l.stock_end,
                    'cost_init': l.cost_price,
                    }))
        self.write(cr, uid, ids, {'line_ids': lines}, context=context)

    def _clean_stock_moves_data(self, cr, uid, ids, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        obj_sbl = self.pool.get('tcv.stock.book.lines')
        empty_data = {
            'stock_in': 0,
            'cost_in': 0,
            'stock_out': 0,
            'stock_self': 0,
            'stock_scrap': 0,
            'stock_end': 0,
            'check_sum': 0,
            'cost_price': 0,
            'stock_theoric': 0,
            'cost_theoric': 0
            }
        for item in self.browse(cr, uid, ids, context):
            line_ids = [x.id for x in item.line_ids]
            obj_sbl.write(cr, uid, line_ids, empty_data, context)
            unlink_ids = obj_sbl.search(cr, uid, [('book_id', '=', item.id),
                                                  ('stock_init', '=', 0)])
            if unlink_ids:
                obj_sbl.unlink(cr, uid, unlink_ids, context)
        return True

    def _get_stock_moves(self, cr, uid, ids, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        sql = '''
        select sl.usage || '-' || dl.usage as type, sm.product_id,
               sm.product_uom, pt.uom_id, sum(sm.product_qty) as qty
        from stock_move sm
        left join stock_location sl on sm.location_id = sl.id
        left join stock_location dl on sm.location_dest_id = dl.id
        left join product_uom pu on sm.product_uom = pu.id
        left join product_template pt on sm.product_id = pt.id
        where sm.state='done' and sl.usage != dl.usage and
              sm.date between '%s 00:00:00' and '%s 23:29:59' and
              pt.type = 'product'
        group by sl.usage, dl.usage, product_id, sm.product_uom, pt.uom_id
        order by sm.product_id
        '''
        obj_sbl = self.pool.get('tcv.stock.book.lines')
        obj_uom = self.pool.get('product.uom')
        product_ids = {}

        for item in self.browse(cr, uid, ids, context=context):
            for l in item.line_ids:
                product_ids.update({l.product_id.id: l.id})
            cr.execute(sql % (item.period_id.date_start,
                              item.period_id.date_stop))
            for line in cr.dictfetchall():
                if line.get('type') in __MOVE_TYPE__:
                    move_fld = __MOVE_TYPE__[line.get('type')][1:]
                    fls_sing = __MOVE_TYPE__[line.get('type')][0]
                else:
                    raise osv.except_osv(
                        _('Error!'),
                        _('Found invalid stock move: %s') % line.get('type'))
                qty = line['qty']
                if line['product_uom'] != line['uom_id']:
                    #~ uom conversion
                    qty = obj_uom._compute_qty(
                        cr, uid, line['product_uom'], qty, line['uom_id'])
                if fls_sing == '-':
                    #~ scrap sing
                    qty *= -1
                if line['product_id'] in product_ids.keys():
                    line_id = product_ids[line['product_id']]
                    sbl = obj_sbl.browse(cr, uid, line_id, context=context)
                    data = {move_fld: sbl[move_fld] + qty}
                    obj_sbl.write(cr, uid, line_id,
                                  data, context=context)
                else:
                    data = {'book_id': item.id,
                            'product_id': line['product_id'],
                            move_fld: qty}
                    sbl_id = obj_sbl.create(cr, uid, data, context=context)
                    product_ids.update({line['product_id']: sbl_id})
        return True

    def _compute_stock_end(self, cr, uid, ids, context=None):
        obj_lin = self.pool.get('tcv.stock.book.lines')
        ids = isinstance(ids, (int, long)) and [ids] or ids
        for item in self.browse(cr, uid, ids, context=context):
            for line in item.line_ids:
                data = {'stock_end': line.check_sum}
                cost_price = obj_lin.compute_cost_price(
                    line.stock_init, line.cost_init,
                    line.stock_in, line.cost_in, line.stock_scrap)
                data.update({'cost_price': cost_price,
                             'amount_total': data['stock_end'] * cost_price})
                obj_lin.write(cr, uid, line.id, data, context=context)
        return True

    def _get_stock_theoric(self, cr, uid, ids, context=None):
        obj_loc = self.pool.get('tcv.stock.by.location.report')
        obj_lin = self.pool.get('tcv.stock.book.lines')
        ids = isinstance(ids, (int, long)) and [ids] or ids
        for item in self.browse(cr, uid, ids, context=context):
            loc_data_id = obj_loc.create(
                cr, uid, {'date': item.period_id.date_stop}, context)
            obj_loc.button_load_inventory(
                cr, uid, loc_data_id, context=context)
            loc_brw = obj_loc.browse(
                cr, uid, loc_data_id, context=context)
            res = {}
            for line in loc_brw.line_ids:
                if line.product_id.type == 'product':
                    product_id = line.product_id.id
                    if not res.get(product_id):
                        res[product_id] = {
                            'product_id': product_id,
                            'stock_theoric': 0,
                            'cost_theoric': 0,
                            'valid_cost': True,
                            }
                    res[product_id]['stock_theoric'] += line.product_qty
                    res[product_id]['cost_theoric'] += line.total_cost
                    res[product_id]['valid_cost'] = \
                        res[product_id]['valid_cost'] and \
                        line.prod_lot_id and line.total_cost and \
                        line.product_qty
            for product in res.values():
                data = product.copy()
                if data.pop('valid_cost'):
                    data.update({
                        'cost_price':
                            data['cost_theoric'] / data['stock_theoric']})
                l_id = obj_lin.search(
                    cr, uid, [('product_id', '=', product['product_id']),
                              ('book_id', '=', item.id)])
                if l_id:
                    obj_lin.write(cr, uid, l_id, data, context=context)
                else:
                    data.update({'book_id': item.id})
                    obj_lin.create(cr, uid, data, context)
        return True

    def _compute_cost_in(self, cr, uid, ids, context=None):
        '''
        Added to fix missing cost_in after load data lines
            cost_in = average cost of inputs
        '''
        obj_lin = self.pool.get('tcv.stock.book.lines')
        ids = isinstance(ids, (int, long)) and [ids] or ids
        for item in self.browse(cr, uid, ids, context=context):
            for line in item.line_ids:
                #~ Adjust cost_in value
                stock_in = line.stock_in or 0.0
                cost_in = line.cost_in or 0.0
                if stock_in and not cost_in:
                    data = {}
                    #~ when loan only data in stock_in
                    stock_init = line.stock_init or 0.0
                    cost_init = line.cost_init or 0.0
                    cost_price = line.cost_price or 0.0
                    stock_in_cost = (stock_init + stock_in) * cost_price
                    initial_cost = stock_init * cost_init
                    variation = stock_in_cost - initial_cost
                    if stock_in:
                        data['cost_in'] = round(variation / stock_in, 2)
                    obj_lin.write(cr, uid, [line.id], data, context=context)

    ##--------------------------------------------------------- function fields

    _order = 'period_id desc'

    _columns = {

        'name': fields.char(
            'Name', size=64, required=False, readonly=True,
            states={'draft': [('readonly', False)]}),
        'period_id': fields.many2one(
            'account.period', 'Period', required=True, ondelete='restrict',
            domain=[('special', '=', False)],
            readonly=True, states={'draft': [('readonly', False)]}),
        'year': fields.integer(
            'Year', required=True, readonly=True,
            states={'draft': [('readonly', False)]}),
        'month': fields.integer(
            'Month', required=True, readonly=True,
            states={'draft': [('readonly', False)]}),
        'line_ids': fields.one2many(
            'tcv.stock.book.lines', 'book_id', 'lines',
            readonly=True, states={'draft': [('readonly', False)]}),
        'state': fields.selection(
            [('draft', 'Draft'), ('done', 'Done'), ('cancel', 'Cancelled')],
            string='State', required=True, readonly=True),
        'company_id': fields.many2one(
            'res.company', 'Company', required=True, readonly=True,
            ondelete='restrict'),
        'prior_book_id': fields.many2one(
            'tcv.stock.book', 'Prior book', required=False, readonly=True,
            ondelete='restrict'),
        'empty_book': fields.boolean(
            'Print empty book'),
        }

    _defaults = {
        'state': lambda *a: 'draft',
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company').
        _company_default_get(cr, uid, 'obj_name', context=c),
        }

    _sql_constraints = [
        ('month_range', 'CHECK(month between 1 and 12)',
         'The month must be in 1-12 range!'),
        ('period_unique', 'UNIQUE(year,month)', 'The period must be unique!'),
        ('period_uniq', 'UNIQUE(period_id)', 'The period must be unique!'),
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    def button_update_book(self, cr, uid, ids, context=None):
        for item in self.browse(cr, uid, ids, context={}):
            if item.prior_book_id:
                self._clear_lines(cr, uid, item.id, context)
                self._get_prior_book_lines(
                    cr, uid, item.id, item.prior_book_id, context)
            else:
                self._clean_stock_moves_data(cr, uid, item.id, context)
        self._get_stock_moves(cr, uid, ids, context)
        self._compute_stock_end(cr, uid, ids, context)
        self._get_stock_theoric(cr, uid, ids, context)
        self._compute_cost_in(cr, uid, ids, context)
        return True

    ##------------------------------------------------------------ on_change...

    def on_change_period_id(self, cr, uid, ids, period_id):
        res = {}
        if period_id:
            res.update(self._get_prior_book(
                cr, uid, period_id, context=None))
        return {'value': res}

    ##----------------------------------------------------- create write unlink

    def create(self, cr, uid, vals, context=None):
        if vals.get('period_id'):
            vals.update(self._get_year_month(
                cr, uid, vals['period_id'], context))
            vals.update(self._get_prior_book(
                cr, uid, vals['period_id'], context))
        res = super(tcv_stock_book, self).create(cr, uid, vals, context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        if vals.get('period_id'):
            vals.update(self._get_year_month(
                cr, uid, vals['period_id'], context))
            vals.update(self._get_prior_book(
                cr, uid, vals['period_id'], context))
        res = super(tcv_stock_book, self).write(cr, uid, ids, vals, context)
        return res

    def unlink(self, cr, uid, ids, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        for item in self.browse(cr, uid, ids, context={}):
            if item.state not in ('draft', 'cancel'):
                raise osv.except_osv(
                    _('Invalid action !'),
                    _('Cannot delete stock book that are already Done!'))
        res = super(tcv_stock_book, self).unlink(cr, uid, ids, context)
        return res

    ##---------------------------------------------------------------- Workflow

    def button_draft(self, cr, uid, ids, context=None):
        vals = {'state': 'draft'}
        return self.write(cr, uid, ids, vals, context)

    def button_done(self, cr, uid, ids, context=None):
        vals = {'state': 'done'}
        return self.write(cr, uid, ids, vals, context)

    def button_cancel(self, cr, uid, ids, context=None):
        vals = {'state': 'cancel'}
        return self.write(cr, uid, ids, vals, context)

    def test_draft(self, cr, uid, ids, *args):
        return True

    def test_done(self, cr, uid, ids, *args):
        for item in self.browse(cr, uid, ids, context={}):
            if item.prior_book_id and item.prior_book_id.state != 'done':
                raise osv.except_osv(
                    _('Error!'),
                    _('Can\'t set a book done when prior book is not done'))
        return True

    def test_cancel(self, cr, uid, ids, *args):
        #~ ids = isinstance(ids, (int, long)) and [ids] or ids
        #~ for i in ids:
            #~ next_id = self.search(cr, uid, [('prior_book_id', '=', i)])
            #~ if next_id:
                #~ raise osv.except_osv(
                    #~ _('Error!'),
                    #~ _('You can not reset a book used as a previous book'))
        return True

tcv_stock_book()


##-------------------------------------------------------- tcv_stock_book_lines


class tcv_stock_book_lines(osv.osv):

    _name = 'tcv.stock.book.lines'

    _description = ''

    #~ _order = 'code'
    _order = 'name,code'

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def _compute_check_sum(self, cr, uid, item, context=None):
        return round(item['stock_init'] + item['stock_in'] -
                     item['stock_out'] - item['stock_self'] -
                     item['stock_scrap'], 4)

    def _search_errors(self, cr, uid, obj, field_name, args, context):
        if not args:
            return []
        cr.execute('''
        select id
        from tcv_stock_book_lines
        where stock_init < 0 or stock_end < 0 or
              abs(stock_init + stock_in - stock_out -
                  stock_self - stock_scrap - stock_end) > 0.001 or
              -- stock_in > 0 and cost_in = 0 or
              stock_end > 0 and cost_price = 0

        ''')
        res = cr.fetchall()
        if not res:
            return [('id', '=', '0')]
        return [('id', 'in', [x[0] for x in res])]

    ##--------------------------------------------------------- function fields

    def _compute_all(self, cr, uid, ids, name, arg, context=None):
        if context is None:
            context = {}
        if not len(ids):
            return []
        res = {}
        for item in self.browse(cr, uid, ids, context={}):
            check_sum = self._compute_check_sum(cr, uid, item, context)
            res[item.id] = {
                'check_sum': check_sum,
                'amount_total': round(item.stock_end * item.cost_price, 2),
                'on_error': item.book_id.state == 'draft' and (
                    (abs(check_sum - item. stock_end) > 0.0001) or
                    (item.stock_init < 0.0) or (item.stock_end < 0.0) or
                    #~ (item.stock_in and not item.cost_in) or
                    item.stock_end and not item.cost_price or False),
                }
        return res

    ##-------------------------------------------------------------------------

    _columns = {
        'book_id': fields.many2one(
            'tcv.stock.book', 'Stock book', required=True, ondelete='cascade'),
        'name': fields.char(
            'Period', size=16, required=False, readonly=True),
        'period_id': fields.related(
            'book_id', 'period_id', type='many2one',
            relation='account.period', string='Period',
            store=True, readonly=True),
        'product_id': fields.many2one(
            'product.product', 'Product', ondelete='restrict'),
        'categ_id': fields.related(
            'product_id', 'categ_id', type='many2one',
            relation='product.category', string='Category', store=True,
            readonly=True),
        'uom_id': fields.related(
            'product_id', 'uom_id', type='many2one',
            relation='product.uom', string='Uom',
            store=False, readonly=True),
        'code': fields.related(
            'product_id', 'default_code', type='char',
            string='code', store=True, readonly=True,
            size=32),
        'stock_init': fields.float(
            'Initial', digits_compute=dp.get_precision('Product UoM'),
            required=True),
        'cost_init': fields.float(
            'init cost', digits_compute=dp.get_precision('Account'),
            required=True),
        'stock_in': fields.float(
            'Input', digits_compute=dp.get_precision('Product UoM'),
            required=True),
        'cost_in': fields.float(
            'Input cost', digits_compute=dp.get_precision('Account'),
            required=True),
        'stock_out': fields.float(
            'Output', digits_compute=dp.get_precision('Product UoM'),
            required=True),
        'stock_self': fields.float(
            'Self', digits_compute=dp.get_precision('Product UoM'),
            required=True),
        'stock_scrap': fields.float(
            'Scrap', digits_compute=dp.get_precision('Product UoM'),
            required=True),
        'stock_end': fields.float(
            'End', digits_compute=dp.get_precision('Product UoM'),
            required=True),
        'cost_price': fields.float(
            'Amount', digits_compute=dp.get_precision('Account'),
            required=True),
        'stock_theoric': fields.float(
            'Theoric', digits_compute=dp.get_precision('Product UoM'),
            required=True),
        'cost_theoric': fields.float(
            'Theo. Amount', digits_compute=dp.get_precision('Account'),
            required=True),
        'check_sum': fields.function(
            _compute_all, method=True, type='float', string='Check sum',
            digits_compute=dp.get_precision('Product UoM'), multi='all'),
        'amount_total': fields.function(
            _compute_all, method=True, type='float', string='Total amount',
            digits_compute=dp.get_precision('Account'), multi='all'),
        'on_error': fields.function(
            _compute_all, method=True, type='bool', string='Error',
            multi='all', fnct_search=_search_errors),
        'note': fields.char(
            'Notes', size=128, required=False, readonly=False),
        }

    _defaults = {
        'stock_init': 0,
        'cost_init': 0,
        'stock_in': 0,
        'cost_in': 0,
        'stock_out': 0,
        'stock_self': 0,
        'stock_scrap': 0,
        'stock_end': 0,
        'check_sum': 0,
        'cost_price': 0,
        'stock_theoric': 0,
        'cost_theoric': 0,
        }

    _sql_constraints = [
        ('product_unique', 'UNIQUE(book_id, product_id)',
         'The product must be unique (for this period)!'),
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    def compute_cost_price(self, stock_init, cost_init, stock_in, cost_in,
                           stock_scrap):
        inputs = stock_in if stock_scrap >= 0 else stock_in - stock_scrap
        if (inputs and not cost_in) or ((stock_init + inputs) == 0):
            return 0
        if not inputs:
            return cost_init
        v1 = stock_init * cost_init
        v2 = inputs * cost_in
        st = stock_init + inputs
        return round((v1 + v2) / st, 2) or 0

    ##-------------------------------------------------------- buttons (object)

    def button_detail(self, cr, uid, ids, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        item = self.browse(cr, uid, ids[0], context={})
        return {'name': _('Stock detail (%s)') % item.product_id.default_code,
                'type': 'ir.actions.act_window',
                'res_model': 'tcv.stock.by.location.report',
                'view_type': 'form',
                'view_id': False,
                'view_mode': 'form',
                'nodestroy': True,
                'target': 'current',
                'domain': "",
                'context': {
                    'default_date': item.book_id.period_id.date_stop,
                    'default_product_id': item.product_id.id,
                    'do_autoload': True,
                    }}

    ##------------------------------------------------------------ on_change...

    def on_change_stock(self, cr, uid, ids, stock_init, cost_init, stock_in,
                        cost_in, stock_out, stock_self, stock_scrap, stock_end,
                        cost_price):
        check_sum = self._compute_check_sum(
            cr, uid, {'stock_init': stock_init,
                      'stock_in': stock_in,
                      'stock_out': stock_out,
                      'stock_self': stock_self,
                      'stock_scrap': stock_scrap,
                      'stock_end': stock_end,
                      })
        if not stock_in and not cost_in and stock_scrap < 0:
            cost_in = cost_init
        cost_price = self.compute_cost_price(
            stock_init, cost_init, stock_in, cost_in, stock_scrap)
        values = {'check_sum': check_sum,
                  'stock_end': check_sum,
                  'cost_price': cost_price,
                  'cost_in': cost_in,
                  'amount_total': round(check_sum * cost_price, 2)
                  }
        res = {'value': values}
        return res

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_stock_book_lines()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
