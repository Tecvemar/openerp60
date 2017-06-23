# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2015-10-13
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

##-------------------------------------------------- tcv_municipal_taxes_config


class tcv_municipal_taxes_config(osv.osv):

    _name = 'tcv.municipal.taxes.config'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def name_get(self, cr, uid, ids, context):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        res = []
        for item in self.browse(cr, uid, ids, context={}):
            res.append((item.id, '[%s] %s' % (item.code, item.name)))
        return res

    def name_search(self, cr, user, name, args=None, operator='ilike',
                    context=None, limit=100):
        res = super(tcv_municipal_taxes_config, self).name_search(
            cr, user, name, args, operator, context, limit)
        if not res and name:
            ids = self.search(
                cr, user, [('code', 'ilike', name.upper())] + args,
                limit=limit)
            if ids:
                res = self.name_get(cr, user, ids, context=context)
        return res

    ##--------------------------------------------------------- function fields

    _order = 'code'

    _columns = {
        'code': fields.char(
            'Code', size=16, required=True, readonly=False),
        'name': fields.char(
            'Name', size=128, required=True, readonly=False),
        'tax_amount': fields.float(
            'Tax', digits_compute=dp.get_precision('Account'),
            required=True, help="Tax rate for sales"),
        'wh_rate': fields.float(
            'Wh rate', digits_compute=dp.get_precision('Account'),
            required=True, help="Tax rate for supplier withholding"),
        'company_id': fields.many2one(
            'res.company', 'Company', required=True, readonly=True,
            ondelete='restrict'),
        }

    _defaults = {
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company').
        _company_default_get(cr, uid, self._name, context=c),
        'tax_amount': lambda *a: 0,
        'wh_rate': lambda *a: 0,
        }

    _sql_constraints = [
        ('code_uniq', 'UNIQUE(code,company_id)', 'The code must be unique!'),
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow


tcv_municipal_taxes_config()


##----------------------------------------------------------- tcv_municipal_tax


class tcv_municipal_tax(osv.osv):

    _name = 'tcv.municipal.tax'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def default_get(self, cr, uid, fields, context=None):
        data = super(tcv_municipal_tax, self).default_get(
            cr, uid, fields, context)
        if not data.get('fiscalyear_id'):
            date = time.strftime('%Y-%m-%d')
            obj_per = self.pool.get('account.period')
            period_id = obj_per.find(cr, uid, date)[0]
            brw_per = obj_per.browse(cr, uid, period_id, context=context)
            data.update({'fiscalyear_id': brw_per.fiscalyear_id.id})
        return data

    def _get_bm_name(self, date):
        __BIMONTHLYS__ = ('0102', '0304', '0506', '0708', '0910', '1112')
        index = int((time.strptime(date, '%Y-%m-%d').tm_mon + 1) / 2) - 1
        return __BIMONTHLYS__[index]

    ##--------------------------------------------------------- function fields

    _order = 'fiscalyear_id desc'

    _rec_name = 'fiscalyear_id'

    _columns = {
        'fiscalyear_id': fields.many2one(
            'account.fiscalyear', 'Fiscal Year', required=True,
            ondelete='restrict'),
        'date_start': fields.related(
            'fiscalyear_id', 'date_start', string='Start Date',
            readonly=True, type='date', store=False),
        'date_stop': fields.related(
            'fiscalyear_id', 'date_stop', string='End Date',
            readonly=True, type='date', store=False),
        'company_id': fields.many2one(
            'res.company', 'Company', required=True, readonly=True,
            ondelete='restrict'),
        'line_ids': fields.one2many(
            'tcv.municipal.tax.lines', 'line_id', 'Lines', readonly=True),
        'line_bm_ids': fields.one2many(
            'tcv.municipal.tax.lines', 'line_id', 'Lines', readonly=True),
        'state': fields.selection(
            [('draft', 'Draft'), ('done', 'Done'), ('cancel', 'Cancelled')],
            string='State', required=True, readonly=True),
        'amount_total': fields.float(
            'Amount total', readonly=True,
            digits_compute=dp.get_precision('Account')),
        'tax_total': fields.float(
            'Tax total', readonly=True,
            digits_compute=dp.get_precision('Account')),
        }

    _defaults = {
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company').
        _company_default_get(cr, uid, self._name, context=c),
        'state': lambda *a: 'draft',
        }

    _sql_constraints = [
        ('fiscalyear_uniq', 'UNIQUE(fiscalyear_id)',
         'The fiscalyear must be unique!'),
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    def get_municipal_taxes(self, cr, uid, ids, context=None):
        context = context or {}
        ids = isinstance(ids, (int, long)) and [ids] or ids
        res = {}
        for item in self.browse(cr, uid, ids, context={}):
            params = {
                'company_id': item.company_id.id,
                'date_start': context.get('date_start',
                                          item.fiscalyear_id.date_start),
                'date_stop': context.get('date_stop',
                                         item.fiscalyear_id.date_stop),
                }
            sql = '''
            select mt.id as muni_tax_id, mt.code, mt.name, q.product_code,
                   q.product_name, q.number_invoice, q.date_invoice,
                   sum(q.price_subtotal) as total_amount, mt.tax_amount,
                   q.partner_name, q.currency_id, q.type, q.invoice_id
            from (
                select case when pm.prod_tax_id > 0 then pm.prod_tax_id else
                       cm.muni_tax_id end as muni_tax_id,
                       pp.default_code as product_code,
                       pt.name as product_name, ail.price_subtotal,
                       ai.number as number_invoice, ai.date_invoice,
                       rp.name as partner_name, ai.currency_id, ai.type,
                       ai.id as invoice_id
                from account_invoice_line ail
                left join account_invoice ai on ail.invoice_id = ai.id
                left join product_template pt on ail.product_id = pt.id
                left join product_product pp on ail.product_id = pp.id
                left join product_category pc on pt.categ_id = pc.id
                left join res_partner rp on ai.partner_id = rp.id
                left join (select cast(substring(value_reference from
                                       position(',' in value_reference)+1)
                                       as int) as muni_tax_id,
                                  cast(substring(res_id from
                                       position(',' in res_id)+1)
                                       as int) as categ_id
                           from ir_property
                           where value_reference like
                                 'tcv.municipal.taxes.config%%' and
                                 company_id = %(company_id)s and
                                 res_id like 'product.category%%')
                           as cm on pt.categ_id = cm.categ_id
                left join (select cast(substring(value_reference from
                                       position(',' in value_reference)+1)
                                       as int) as prod_tax_id,
                                  cast(substring(res_id from
                                       position(',' in res_id)+1)
                                       as int) as product_id
                           from ir_property
                           where value_reference like
                                 'tcv.municipal.taxes.config%%' and
                                 company_id = %(company_id)s and
                                 res_id like 'product.product%%')
                           as pm on pt.id = pm.product_id
                where ai.type in ('out_invoice', 'out_refund') and
                      ai.date_invoice between '%(date_start)s' and
                                              '%(date_stop)s' and
                      ai.state in ('open', 'paid')) as q
            left join tcv_municipal_taxes_config mt on q.muni_tax_id = mt.id
            group by mt.id, mt.code, mt.name, q.product_code, q.product_name,
                     q.number_invoice, q.date_invoice, mt.tax_amount,
                     q.partner_name, q.currency_id, q.type, q.invoice_id
            order by mt.code, q.product_name, q.date_invoice,
                     q.number_invoice''' % params
            cr.execute(sql)
            for row in cr.dictfetchall():
                code = row['code'] or _('unassigned')
                product_code = row['product_code']
                total_amount = row['total_amount']
                if row['type'] == 'out_refund':
                    #~ out_refund: negative amount
                    total_amount = -row['total_amount']
                    row['partner_name'] = _('%s (N/C)') % row['partner_name']
                if item.company_id.currency_id.id != row['currency_id']:
                    #~ Currency (export): amount * rate
                    obj_inv = self.pool.get('account.invoice')
                    obj_cur = self.pool.get('res.currency')
                    inv_brw = obj_inv.browse(
                        cr, uid, row['invoice_id'], context=context)
                    rate = obj_inv.get_invoice_currency_rate(cr, uid, inv_brw)
                    total_amount = total_amount * rate
                    cur_brw = obj_cur.browse(
                        cr, uid, row['currency_id'], context=context)
                    row['partner_name'] = '%s (%s: %.2f)' % (
                        row['partner_name'],
                        cur_brw.symbol,
                        row['total_amount'])
                if not res.get(code):
                    res.update({
                        code: {
                            'muni_tax_id': row.get('muni_tax_id', None),
                            'code': code,
                            'name': row['name'] or '',
                            'products': {},
                            'tax_amount': row['tax_amount'],
                            'total_sales': 0,
                            'total_0102': 0,
                            'total_0304': 0,
                            'total_0506': 0,
                            'total_0708': 0,
                            'total_0910': 0,
                            'total_1112': 0,
                            }
                        })
                if not res[code]['products'].get(product_code):
                    res[code]['products'].update({
                        product_code: {
                            'product_code': product_code,
                            'product_name': row['product_name'],
                            'invoices': [],
                            'total_product': 0,
                            }})
                res[code]['products'][product_code]['invoices'].append({
                    'number_invoice': row['number_invoice'],
                    'date_invoice': row['date_invoice'],
                    'partner_name': row['partner_name'],
                    'total_amount': total_amount,
                    })

                res[code]['total_sales'] += total_amount
                bm_key = 'total_%s' % self._get_bm_name(row['date_invoice'])
                res[code][bm_key] += total_amount
                res[code]['products'][product_code]['total_product'] += \
                    total_amount
        #~ Sort municipal taxes by code
        tmp_res = sorted(res.values(), key=lambda k: k['code'])
        #~ Sort products by product name
        for item in tmp_res:
            tmp_prd = sorted(item['products'].values(),
                             key=lambda k: k['product_name'])
            item['products'] = tmp_prd
        return tmp_res

    def clear_wizard_lines(self, cr, uid, item, context):
        unlink_ids = []
        for l in item.line_ids:
            unlink_ids.append(l.id)
        obj_lin = self.pool.get('tcv.municipal.tax.lines')
        if unlink_ids:
            obj_lin.unlink(cr, uid, unlink_ids, context=context)
        return unlink_ids

    ##-------------------------------------------------------- buttons (object)

    def button_load(self, cr, uid, ids, context=None):
        for muni in self.browse(cr, uid, ids, context={}):
            self.clear_wizard_lines(cr, uid, muni, context)
            data = self.get_municipal_taxes(cr, uid, ids, context)
            lines = []
            amount_total = 0
            tax_total = 0
            for item in data:
                if item['muni_tax_id']:
                    values = {
                        'muni_tax_id': item['muni_tax_id'],
                        'amount': item['total_sales'],
                        'amount_0102': item['total_0102'],
                        'amount_0304': item['total_0304'],
                        'amount_0506': item['total_0506'],
                        'amount_0708': item['total_0708'],
                        'amount_0910': item['total_0910'],
                        'amount_1112': item['total_1112'],
                        'tax_amount': item['tax_amount'],
                        }
                    lines.append((0, 0, values))
                    amount_total += item['total_sales']
                    if item['tax_amount']:
                        tax_total += item['total_sales'] * \
                            item['tax_amount'] / 100
                else:
                    products = ', '.join(
                        [x['product_code'] for x in item['products']])
                    raise osv.except_osv(
                        _('Error!'),
                        _('Must set a municipal tax settings for ' +
                          'product(s):\n%s') % products)
            if lines:
                self.write(cr, uid, [muni.id], {'line_ids': lines,
                                                'amount_total': amount_total,
                                                'tax_total': tax_total,
                                                },
                           context=context)
        return True

    def button_print_report(self, cr, uid, ids, context=None):
        brw = self.browse(cr, uid, ids, context=context)[0]
        return {'name': _('Print municipal tax'),
                'type': 'ir.actions.act_window',
                'res_model': 'tcv.municipal.tax.print',
                'view_type': 'form',
                'view_id': False,
                'view_mode': 'form',
                'nodestroy': True,
                'target': 'new',
                'domain': "",
                'context': {'default_muni_tax_id': brw.id},
                }

    ##------------------------------------------------------------ on_change...

    def on_change_fiscalyear_id(self, cr, uid, ids, fiscalyear_id):
        res = {}
        if not fiscalyear_id:
            return {}
        obj_fy = self.pool.get('account.fiscalyear')
        fy = obj_fy.browse(cr, uid, fiscalyear_id, context=None)
        res.update({'date_start': fy.date_start,
                    'date_stop': fy.date_stop})
        return {'value': res}
    ##----------------------------------------------------- create write unlink

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
            if not item.line_ids:
                raise osv.except_osv(
                    _('Error!'),
                    _('Must load ivoices data'))
        return True

    def test_cancel(self, cr, uid, ids, *args):
        return True


tcv_municipal_tax()


##----------------------------------------------------- tcv_municipal_tax_lines


class tcv_municipal_tax_lines(osv.osv):

    _order = 'muni_tax_id'

    _name = 'tcv.municipal.tax.lines'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def _compute_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for item in self.browse(cr, uid, ids, context=context):
            if item.muni_tax_id and item.tax_amount > 0:
                res[item.id] = {
                    'total_tax': (item.amount * item.tax_amount) / 100,
                    'tax_0102': (item.amount_0102 * item.tax_amount) / 100,
                    'tax_0304': (item.amount_0304 * item.tax_amount) / 100,
                    'tax_0506': (item.amount_0506 * item.tax_amount) / 100,
                    'tax_0708': (item.amount_0708 * item.tax_amount) / 100,
                    'tax_0910': (item.amount_0910 * item.tax_amount) / 100,
                    'tax_1112': (item.amount_1112 * item.tax_amount) / 100,
                    }
        return res

    ##--------------------------------------------------------- function fields

    _columns = {
        'line_id': fields.many2one(
            'tcv.municipal.tax', 'Tax lines', required=True,
            ondelete='cascade'),
        'muni_tax_id': fields.many2one(
            'tcv.municipal.taxes.config', 'Municipal tax',
            ondelete='restrict', required=False),
        'amount': fields.float(
            'Amount', digits_compute=dp.get_precision('Account'),
            required=True),
        'tax_amount': fields.float(
            'Tax', digits_compute=dp.get_precision('Account'),
            required=True),
        'total_tax': fields.function(
            _compute_all, method=True, type='float', string='Total tax',
            digits_compute=dp.get_precision('Account'), multi='all',
            store=True),
        'amount_0102': fields.float(
            'Base 01-02', digits_compute=dp.get_precision('Account'),
            required=True),
        'amount_0304': fields.float(
            'Base 03-04', digits_compute=dp.get_precision('Account'),
            required=True),
        'amount_0506': fields.float(
            'Base 05-06', digits_compute=dp.get_precision('Account'),
            required=True),
        'amount_0708': fields.float(
            'Base 07-08', digits_compute=dp.get_precision('Account'),
            required=True),
        'amount_0910': fields.float(
            'Base 09-10', digits_compute=dp.get_precision('Account'),
            required=True),
        'amount_1112': fields.float(
            'Base 11-12', digits_compute=dp.get_precision('Account'),
            required=True),
        'tax_0102': fields.function(
            _compute_all, method=True, type='float', string='Tax 01-02',
            digits_compute=dp.get_precision('Account'), multi='all',
            store=True),
        'tax_0304': fields.function(
            _compute_all, method=True, type='float', string='Tax 03-04',
            digits_compute=dp.get_precision('Account'), multi='all',
            store=True),
        'tax_0506': fields.function(
            _compute_all, method=True, type='float', string='Tax 05-06',
            digits_compute=dp.get_precision('Account'), multi='all',
            store=True),
        'tax_0708': fields.function(
            _compute_all, method=True, type='float', string='Tax 07-08',
            digits_compute=dp.get_precision('Account'), multi='all',
            store=True),
        'tax_0910': fields.function(
            _compute_all, method=True, type='float', string='Tax 09-10',
            digits_compute=dp.get_precision('Account'), multi='all',
            store=True),
        'tax_1112': fields.function(
            _compute_all, method=True, type='float', string='Tax 11-12',
            digits_compute=dp.get_precision('Account'), multi='all',
            store=True),
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


tcv_municipal_tax_lines()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
