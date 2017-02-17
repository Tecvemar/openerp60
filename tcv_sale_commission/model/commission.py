# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description:
#
#
##############################################################################
from osv import fields, osv
from tools.translate import _
#~ import pooler
import decimal_precision as dp
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta

pct_sale_comm_digits = (7, 4)


def _compute_pct(amount, pct, round_to=2):
    return round(amount * pct / 100, round_to)


def row_as_dict(row, fields):
    dict = {}
    for i in range(len(fields)):
        dict.update({fields[i]: row[i]})
    return dict


class tcv_excluded_partner(osv.osv):

    _name = 'tcv.excluded.partner'

    _description = 'List of excluded partners for sale commissions'

    _columns = {
        'company_id': fields.many2one(
            'res.company', 'Company', required=True, readonly=True,
            ondelete='restrict'),
        'partner_id': fields.many2one(
            'res.partner', 'Partner', required=True,
            domain=[('customer', '=', True)], ondelete='restrict'),
        'name': fields.char('Note', size=64, required=False),
        }

    _defaults = {'company_id': lambda self, cr, uid, context: self.pool.get(
        'res.users').browse(cr, uid, uid, context=context).company_id.id,
        }

    _sql_constraints = [
        ('company_partner_uniq', 'UNIQUE(company_id,partner_id)',
         'The partner must be unique!'),
    ]

tcv_excluded_partner()


class tcv_excluded_product(osv.osv):

    _name = 'tcv.excluded.product'

    _description = 'List of excluded partners for sale commissions'

    _columns = {'company_id': fields.many2one(
                'res.company', 'Company', required=True, readonly=True,
                ondelete='restrict'),
                'product_id': fields.many2one(
                'product.product', 'Product', required=True,
                domain=[('sale_ok', '=', True)], ondelete='restrict'),
                'name': fields.char('Note', size=64, required=False),
                }

    _defaults = {'company_id': lambda self, cr, uid, context: self.pool.get(
        'res.users').browse(cr, uid, uid, context=context).company_id.id,
        }

    _sql_constraints = [
        ('company_product_uniq', 'UNIQUE(company_id,product_id)',
         'The product must be unique!'),
    ]

tcv_excluded_product()


class tcv_sale_salesman(osv.osv):

    _name = 'tcv.sale.salesman'

    _description = 'List of excluded partners for sale commissions'

    _columns = {
        'company_id': fields.many2one(
            'res.company', 'Company', required=True, readonly=True,
            ondelete='restrict'),
        'user_id': fields.many2one(
            'res.users', 'Salesman', required=True, ondelete='restrict'),
        'sale_commission': fields.float(
            'Sale commission', digits=pct_sale_comm_digits, required=True),
        'name': fields.char(
            'Note', size=64, required=False),
        }

    _defaults = {'company_id': lambda self, cr, uid, context: self.pool.get(
        'res.users').browse(cr, uid, uid, context=context).company_id.id,
        }

    _sql_constraints = [
        ('company_user_uniq', 'UNIQUE(company_id,user_id)',
         'The salesman must be unique!'),
        ('comission_range', 'CHECK(sale_commission between 0 and 100)',
         'The sale comssion must be in 0-100 range'),
    ]

    def get_salesman_list(self, cr, uid, context=None):
        res = {'salesman': [], 'sale_commission': []}
        context = context or {}
        sm_obj = self.pool.get('tcv.sale.salesman')
        if context.get('company_id'):
            ids = sm_obj.search(cr, uid, [('company_id', '=',
                                context['company_id'])])
            for sm in sm_obj.browse(cr, uid, ids, context=context):
                res['salesman'].append(sm.user_id.id)
                res['sale_commission'].append(sm.sale_commission)
        return res


tcv_sale_salesman()


class tcv_commission_config(osv.osv):

    _name = 'tcv.commission.config'

    _description = 'Set global commission parameters'

    _columns = {
        'company_id': fields.many2one(
            'res.company', 'Company', required=True, readonly=True,
            ondelete='restrict'),
        'extra_payment_days': fields.integer(
            'Extra payment days', required=True),
        'use_gen_commission': fields.boolean(
            'Use general commission', required=True),
        'pct_gen_commission': fields.float(
            'General commission (%)', digits=pct_sale_comm_digits,
            required=True),
        'gen_commission_name': fields.char(
            'Note for gen. comm.', size=64, required=False, readonly=False),
        }

    _defaults = {'company_id': lambda self, cr, uid, context: self.pool.get(
                 'res.users').browse(
                 cr, uid, uid, context=context).company_id.id,
                 'extra_payment_days': 0,
                 'use_gen_commission': False,
                 'pct_gen_commission': 0.0,
                 }

    _sql_constraints = [
        ('company_uniq', 'UNIQUE(company_id)', 'The company must be unique!'),
        ('comission_range', 'CHECK(pct_gen_commission between 0 and 100)',
         'The sale comssion must be in 0-100 range'),
        ]

    def write(self, cr, uid, ids, vals, context=None):
        if 'use_gen_commission' in vals:
            if not vals['use_gen_commission']:
                vals.update({'pct_gen_commission': 0.0,
                             'gen_commission_name': ''})
            else:
                if not vals.get('pct_gen_commission'):
                    raise osv.except_osv(
                        _('Error!'),
                        _("You must indicate a sale " +
                          "commission"))
        return super(tcv_commission_config, self).write(
            cr, uid, ids, vals, context)

tcv_commission_config()


class tcv_sale_commission(osv.osv):

    _name = 'tcv.sale.commission'

    _description = '''Store calculated sale's commissions'''

    _order = 'date_end desc'

    def _compute_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        ids = isinstance(ids, (int, long)) and [ids] or ids
        for item in self.browse(cr, uid, ids, context=context):
            data = {'total_sales': 0, 'total_commission': 0}
            for l in item.line_ids:
                data['total_sales'] += l.sales_total
                data['total_commission'] += l.real_commission
            res[item.id] = data
        return res

    _columns = {
        'name': fields.char(
            'Ref', size=16, required=False, readonly=True),
        'company_id': fields.many2one(
            'res.company', 'Company', required=True, readonly=True,
            ondelete='restrict'),
        'state': fields.selection([(
            'draft', 'Draft'), ('confirmed', 'Confirmed'), ('paid', 'Paid')],
            string='State', required=True, readonly=True),
        'date': fields.date(
            'Date', required=True, readonly=True,
            states={'draft': [('readonly', False)]}, select=True),
        'date_start': fields.date(
            'Start date', required=True, readonly=True,
            states={'draft': [('readonly', False)]}, select=True),
        'date_end': fields.date(
            'End date', required=True, readonly=True,
            states={'draft': [('readonly', False)]}, select=True),
        'date_computed': fields.datetime(
            'Computed date', required=False, readonly=True, select=True),
        'user_id': fields.many2one(
            'res.users', 'Computed by', readonly=True, select=True,
            ondelete='restrict'),
        'narration': fields.text(
            'Notes', readonly=False),
        'auto_line_count': fields.integer(
            'Lines Count'),
        'line_ids': fields.one2many(
            'tcv.sale.commission.line', 'line_id', 'Sales commissions',
            readonly=True, states={'draft': [('readonly', False)]}),
        'total_sales': fields.function(
            _compute_all, method=True, type='float', string='Total sales',
            digits_compute=dp.get_precision('Account'), multi='all'),
        'total_commission': fields.function(
            _compute_all, method=True, type='float', string='Total commission',
            digits_compute=dp.get_precision('Account'), multi='all'),
        }

    _defaults = {
        'name': lambda *a: '/',
        'company_id': lambda self, cr, uid,
        c: self.pool.get('res.company')._company_default_get(
            cr, uid, 'obj_name', context=c),
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        'date_start': lambda * a: (
            datetime.today() + relativedelta(months=-1) +
            relativedelta(day=01)).strftime('%Y-%m-%d'),
        'date_end': lambda * a: (
            datetime.today() + relativedelta(months=-1) +
            relativedelta(day=31)).strftime('%Y-%m-%d'),
        'user_id': lambda s, c, u, ctx: u,
        'state': lambda * a: 'draft',
        }

    def _get_payment_data(self, cr, uid, ids, dict, context):
        context = context or {}
        dict_payment_days = context.get('dict_payment_days', {})
        if dict_payment_days.get(dict['invoice_id']):
            #~ los ya resueltos de guardan en este diccionario no hace
            #~ falta buscar más
            dict.update({'payment_day': dict_payment_days[dict['invoice_id']]})
            return dict
        obj_ail = self.pool.get('account.invoice.line')
        ail = obj_ail.browse(cr, uid, dict['inv_line_id'], context=context)
        day = 0
        for pay in ail.invoice_id.payment_ids:
            if pay.date > day:
                day = pay.date
        if day:
            dict.update({'payment_day': day})
            dict_payment_days.update({dict['invoice_id']: day})
        context.update({'dict_payment_days': dict_payment_days})
        return dict

    def new_salesman_commision(self, dict, comm_config, totals):
        new_salesman = {
            'user_id': dict['user_id'],
            'sale_commission': dict['sale_commission'],
            'lines_count': 0,
            'sales_total': 0.0,
            'comm_subtotal': 0.0,
            'pct_valid_comm': 100,
            'real_commission': 0.0,
            'auto': True,
            'tmp_invoice_line_ids': [],
            'name': comm_config.gen_commission_name if dict['user_id'] == 0
            else '',
            }
        totals.update({dict['user_id']: new_salesman})
        return totals

    def button_compute_click(self, cr, uid, ids, context=None):
        so_obj = self.pool.get('tcv.sale.commission')
        co_obj = self.pool.get('tcv.commission.config')
        sa_obj = self.pool.get('tcv.sale.salesman')
        ail_obj = self.pool.get('account.invoice.line')
        so_obj_l = self.pool.get('tcv.sale.commission.line')
        comp_id = self.pool.get('res.users').browse(
            cr, uid, uid, context=context).company_id.id
        context.update({'company_id': comp_id})
        config_id = co_obj.search(cr, uid, [('company_id', '=', comp_id)])
        if not config_id:
            raise osv.except_osv(
                _('Error!'),
                _("General commission config not found"))
        config_id = config_id[0]
        comm_config = co_obj.browse(cr, uid, config_id, context)
        salesman_ids = sa_obj.get_salesman_list(cr, uid, context)
        if not salesman_ids['salesman']:
            raise osv.except_osv(_('Error!'), _("No salesman found"))
        for com in self.browse(cr, uid, ids, context={}):
            max_payment_day = datetime.strptime(
                com.date_end, '%Y-%m-%d') + relativedelta(
                days=comm_config.extra_payment_days)
            #~ clear previous data
            for l in com.line_ids:
                so_obj_l.unlink(cr, uid, l.id, context=context)
                ail_ids = ail_obj.search(
                    cr, uid, [('tcv_sale_commission_id', '=', com.id)])
                ail_obj.write(
                    cr, uid, ail_ids,
                    {'tcv_sale_commission_id': None}, context=context)
            #~ load new commissions
            cr.execute('''
select l.id, i.id invoice_id, u.id user_id, s.sale_commission,
       l.price_subtotal sales_total
from account_invoice_line l
left join account_invoice i on l.invoice_id = i.id
left join res_users u on i.user_id = u.id
left join tcv_sale_salesman s on i.user_id = s.user_id
where state = 'paid' and i.company_id = %s and
      i.date_invoice between '%s' and '%s' and
      i.type  = 'out_invoice' and
      l.tcv_sale_commission_id is null and
      i.partner_id not in (select partner_id from tcv_excluded_partner pa
      where pa.company_id = i.company_id) and
      l.product_id not in (select product_id from tcv_excluded_product pr
      where pr.company_id = i.company_id)
order by u.id, l.id
                       ''' % (com.company_id.id, com.date_start,
                              com.date_end), ())
            rows = cr.fetchall()
            fields = ('inv_line_id', 'invoice_id', 'user_id',
                      'sale_commission', 'sales_total')
            totals = {}
            # create dict for sale totals
            for i in range(len(salesman_ids['salesman'])):
                d = {'user_id': salesman_ids['salesman'][i],
                     'sale_commission': salesman_ids['sale_commission'][i]}
                totals = self.new_salesman_commision(d, comm_config, totals)
            totals = self.new_salesman_commision({
                'user_id': 0, 'sale_commission':
                    comm_config.pct_gen_commission}, comm_config, totals)
            #~ Totalize invoice lines
            for row in rows:
                dict = row_as_dict(row, fields)
                dict = self._get_payment_data(cr, uid, ids, dict, context)
                if dict['user_id'] not in salesman_ids['salesman']:
                    dict['user_id'] = 0
                #~ este if es para filtrar por fecha de pago
                if dict.get('payment_day') and datetime.strptime(
                   dict['payment_day'], '%Y-%m-%d') <= max_payment_day:
                    totals[dict['user_id']]['lines_count'] += 1
                    totals[dict['user_id']]['sales_total'] += dict[
                        'sales_total']
                    totals[dict['user_id']]['tmp_invoice_line_ids'].append(
                        dict['inv_line_id'])
                    #~ para sumar en las ventas globales todo
                    if totals.get(0) and dict['user_id'] != 0:
                        totals[0]['lines_count'] += 1
                        totals[0]['sales_total'] += dict['sales_total']
            lines = []
            for t in totals:
                l = totals[t]
                if comm_config.use_gen_commission or l['user_id']:
                    comm_subtotal = _compute_pct(l['sales_total'],
                                                 l['sale_commission'])
                    l['comm_subtotal'] = comm_subtotal
                    l['real_commission'] = comm_subtotal
                    l['invoice_line_ids'] = [
                        (6, 0, l.pop('tmp_invoice_line_ids'))]
                    lines.append((0, 0, l))
            upd_rec = {'date_computed': time.strftime('%Y-%m-%d %H:%M:%S'),
                       'line_ids': lines,
                       'auto_line_count': len(lines)}
            so_obj.write(cr, uid, com.id, upd_rec, context=context)
        return True

    def button_draft(self, cr, uid, ids, context=None):
        obj = self.pool.get('tcv.sale.commission')
        vals = {'state': 'draft'}
        return obj.write(cr, uid, ids, vals, context)

    def button_confirm(self, cr, uid, ids, context=None):
        obj = self.pool.get('tcv.sale.commission')
        so_brw = self.browse(cr, uid, ids, context={})[0]
        if so_brw.name != '/':
            name = so_brw.name
        else:
            name = self.pool.get('ir.sequence').get(cr, uid, 'sale.commission')
        vals = {'state': 'confirmed', 'name': name, }
        return obj.write(cr, uid, ids, vals, context)

    def button_paid(self, cr, uid, ids, context=None):
        obj = self.pool.get('tcv.sale.commission')
        vals = {'state': 'paid'}
        return obj.write(cr, uid, ids, vals, context)

    def test_confirm(self, cr, uid, ids, * args):
        for com in self.browse(cr, uid, ids, context={}):
            if not com.line_ids:
                raise osv.except_osv(
                    _('Error!'),
                    _("You can't confirm a empty form."))
            for l in com.line_ids:
                real_commission = _compute_pct(
                    l.comm_subtotal, l.pct_valid_comm)
                if abs(l.real_commission - real_commission) > 0.0001:
                    raise osv.except_osv(
                        _('Error!'),
                        _("The net commission for %s " +
                          "dosen't seem to be correct") %
                        l.user_id.name)
            if com.auto_line_count != len(com.line_ids):
                raise osv.except_osv(
                    _('Error!'),
                    _("You cant add or delete commission lines"))
        return True

    def unlink(self, cr, uid, ids, context=None):
        unlink_ids = []
        for com in self.browse(cr, uid, ids, context={}):
            if com.state == 'draft':
                unlink_ids.append(com['id'])
            else:
                raise osv.except_osv(
                    _('Invalid action !'),
                    _('Cannot delete sale commission that are already ' +
                      'confirmed or doned !'))
        super(tcv_sale_commission, self).unlink(cr, uid, unlink_ids, context)
        return True

tcv_sale_commission()


class tcv_sale_commission_line(osv.osv):

    _name = 'tcv.sale.commission.line'

    _description = ''

    _columns = {
        'line_id': fields.many2one(
            'tcv.sale.commission', 'Sales commissions', required=True,
            ondelete='cascade', readonly=True,
            states={'draft': [('readonly', False)]}),
        'user_id': fields.many2one(
            'res.users', 'Salesman', readonly=True, select=True,
            ondelete='restrict'),
        'lines_count': fields.integer(
            'Lines count', readonly=True),
        'sales_total': fields.float(
            'Sales total', digits_compute=dp.get_precision('Account'),
            readonly=True, required=True,),
        'sale_commission': fields.float(
            'Sale commission (%)', digits=pct_sale_comm_digits, readonly=True,
            required=True,),
        'comm_subtotal': fields.float(
            'Commission subtotal', digits_compute=dp.get_precision('Account'),
            readonly=True, required=True,),
        'pct_valid_comm': fields.integer(
            'Valid commission (%)', required=True),
        'real_commission': fields.float(
            'Net commission', digits_compute=dp.get_precision('Account'),
            readonly=False, required=True,),
        'name': fields.char(
            'Notes', size=64, required=False, readonly=False),
        'auto': fields.boolean(
            'auto'),
        'invoice_line_ids': fields.one2many(
            'account.invoice.line', 'tcv_sale_commission_id',
            'Invoice Lines', readonly=True),
        }
    _defaults = {'sales_total': lambda *a: 0.0,
                 'sale_commission': lambda *a: 0.0,
                 'comm_subtotal': lambda *a: 0.0,
                 'pct_valid_comm': lambda *a: 100,
                 'real_commission': lambda *a: 0.0,
                 'name': lambda *a: None,
                 'auto': lambda *a: False,
                 }

    _sql_constraints = [
        ('pct_valid_comm_range', 'CHECK(pct_valid_comm between 0 and 100)',
         'The %% of valid comssion must be in 0-100 range'),
        ('only_auto_line', 'CHECK(auto)',
         'Only auto generated lines allowed.'),
        ]

    def on_change_pct_valid_comm(self, cr, uid, ids, comm_subtotal,
                                 pct_valid_comm):
        res = {}
        real_commission = _compute_pct(comm_subtotal, pct_valid_comm)
        res = {'value': {'real_commission': real_commission}}
        return res

    def unlink(self, cr, uid, ids, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        res = super(tcv_sale_commission_line, self).unlink(
            cr, uid, ids, context)
        obj_ail = self.pool.get('account.invoice.line')
        ail_ids = obj_ail.search(
            cr, uid, [('tcv_sale_commission_id', 'in', ids)])
        obj_ail.write(
            cr, uid, ail_ids, {'tcv_sale_commission_id': 0}, context=context)
        return res


tcv_sale_commission_line()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
