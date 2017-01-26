# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date: 17/09/2012
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


##------------------------------------------------------ tcv_import_cost_wizard


class tcv_import_cost_wizard(osv.osv_memory):

    _name = 'tcv.import.cost.wizard'

    _description = ''

    ##-------------------------------------------------------------------------

    ##--------------------------------------------------------- function fields

    _columns = {
        'import_id': fields.many2one(
            'tcv.import.management', 'Import expedient', required=True,
            readonly=True, ondelete='cascade'),
        'currency_id': fields.many2one(
            'res.currency', 'Currency', readonly=True),
        'line_ids': fields.one2many(
            'tcv.import.product.wizard.lines', 'line_id', 'Detail'),
        'tax_ids': fields.one2many(
            'tcv.import.product.wizard.taxes', 'tax_id', 'Taxes'),
        'base': fields.selection(
            [('product_qty', 'Quantity'), ('price_unit', 'Unit price'),
             ('total_amount', 'Total amount'), ('manual', 'Manual')],
            string='Calculation base', required=True),
        'valid': fields.boolean(
            'Valid'),
        }

    _defaults = {
        'base': lambda *a: 'total_amount',
        'total_charges': lambda *a: 0.0,
        'valid': lambda *a: False,
        }

    _sql_constraints = [
        ]

    ##----------------------------------------------------------------- Buttons

    def load_products(self, cr, uid, ids, context):
        if not context.get('default_import_id'):
            return False
        obj_line = self.pool.get('tcv.import.product.wizard.lines')
        obj_tax = self.pool.get('tcv.import.product.wizard.taxes')
        obj_curr = self.pool.get('res.currency')
        obj_inv = self.pool.get('account.invoice')
        obj_prec = self.pool.get('decimal.precision')
        obj_prd = self.pool.get('product.product')

        precision = obj_prec.precision_get(cr, uid, 'Import management data')
        obj_comp = self.pool.get('res.company')
        company_id = self.pool.get('res.users').browse(
            cr, uid, uid, context=context).company_id.id
        company_currency = obj_comp.browse(
            cr, uid, company_id, context=context).currency_id.id
        cr.execute('''
        Select i.id as invoice_id, l.product_id, sum(l.quantity) as quantity,
               sum(l.price_subtotal) as price_subtotal,
               i.currency_id, p.type, l.uos_id from account_invoice i
        left join account_invoice_line l on i.id = l.invoice_id
        left join product_template p on l.product_id = p.id
        where i.import_id = %s and i.state != 'cancel'
        group by i.id, l.product_id, l.price_unit, i.currency_id, p.type,
                 l.uos_id
        having sum(l.quantity) > 0
        order by p.type, product_id, i.id
        ''' % context.get('default_import_id'))
        data = {'currency_id': company_currency,
                'line_ids': [],
                'tax_ids': []}
        for p in cr.fetchall():

            d = {'invoice_id': p[0], 'product_id': p[1], 'quantity': p[2],
                 'price_subtotal': p[3], 'currency_id': p[4], 'type': p[5]}

            product = obj_prd.browse(cr, uid, d['product_id'], context=context)
            uom_id = p[6]

            if uom_id != product.uom_id.id and d['quantity']:
                obj_uom = self.pool.get('product.uom')
                d.update({
                    'quantity': obj_uom._compute_qty(cr, uid, uom_id,
                                                     d['quantity'],
                                                     product.uom_id.id)})

            inv = obj_inv.browse(cr, uid, d['invoice_id'], context=context)
            if inv.currency_id.id != company_currency:
                context.update({
                    'date': inv.date_invoice or inv.date_document})
                price_subtotal = obj_curr.compute(
                    cr, uid, inv.currency_id.id, company_currency,
                    d['price_subtotal'], round=True, context=context)
            else:
                price_subtotal = d['price_subtotal']

            if d['type'] in ('product', 'consu'):
                total_charges = 0.0
                total_amount = price_subtotal
            else:
                total_charges = price_subtotal
                total_amount = 0.0
            data['line_ids'].append((0, 0, {
                'invoice_id': d['invoice_id'],
                'name': inv.reference,
                'date': inv.date_document or inv.date_invoice,
                'product_id': d['product_id'],
                'product_qty': d['quantity'],
                'price_unit': round(price_subtotal / d['quantity'], precision),
                'total_amount': total_amount,
                'total_charges': total_charges,
                'apply_cost': d['type'] in ('product', 'consu'),
                'cost_pct': 0.0,
                'applied_cost': 0.0,
                'applied_tax': 0.0,
                }))
        if ids:
            for item in self.browse(cr, uid, ids, context=context):
                #~ Clear previusly created lines
                if item.line_ids:
                    l_ids = []
                    for line in item.line_ids:
                        l_ids = []
                        l_ids.append(line.id)
                    obj_line.unlink(cr, uid, l_ids, context)
                if item.tax_ids:
                    t_ids = []
                    for line in item.tax_ids:
                        t_ids.append(line.id)
                    obj_tax.unlink(cr, uid, t_ids, context)
                if item.import_id and item.import_id.tax_ids:
                    for tax in item.import_id.tax_ids:
                        for tax_line in tax.cfl_ids:
                            if not tax_line.tax_code.vat_detail and \
                                    tax_line.amount:
                                data['tax_ids'].append((0, 0, {
                                    'date': tax.date_liq,
                                    'name': tax.name,
                                    'ref': tax.ref,
                                    'tax_name': tax_line.tax_code.name,
                                    'amount': tax_line.amount,
                                    }))
            self.write(cr, uid, ids, data, context)
            self.auto_distribute_cost_pct(cr, uid, ids, context)
            self.compute_cost_pct(cr, uid, ids, context)
        else:
            context.update({'load_products_data': data})
        return True

    def base_field_value(self, calculation, line, context):
        base = context.get('base', calculation.base)
        if base == 'product_qty':
            return line.product_qty
        elif base == 'price_unit':
            return line.price_unit
        elif base == 'total_amount':
            return line.total_amount
        return 0.0

    def auto_distribute_cost_pct(self, cr, uid, ids, context):
        total_cost, total_charges = 0.0, 0.0
        obj_line = self.pool.get('tcv.import.product.wizard.lines')
        obj_prec = self.pool.get('decimal.precision')
        precision = obj_prec.precision_get(cr, uid, 'Import management data')
        for item in self.browse(cr, uid, ids, context={}):
            for line in item.line_ids:
                if line.apply_cost:
                    total_cost += self.base_field_value(item, line, context)
                else:
                    if line.total_amount:
                        total_charges += line.total_amount
                    if line.total_charges:
                        total_charges += line.total_charges
            for line in item.line_ids:
                line_pct = 0.0
                if line.apply_cost and total_cost:
                    line_pct = round(
                        (self.base_field_value(item, line, context) * 100.0) /
                        total_cost, precision)
                obj_line.write(
                    cr, uid, [line.id],
                    {'cost_pct': line_pct if line_pct else 0.0}, context)
        return True

    def compute_cost_pct(self, cr, uid, ids, context):
        total_cost, total_charges, total_pct, total_taxes = 0.0, 0.0, 0.0, 0.0
        obj_line = self.pool.get('tcv.import.product.wizard.lines')
        obj_prec = self.pool.get('decimal.precision')
        precision = obj_prec.precision_get(cr, uid, 'Import management data')
        for item in self.browse(cr, uid, ids, context={}):
            for line in item.line_ids:
                total_charges += line.total_charges - line.direct_cost
                total_pct += line.cost_pct
            for line in item.tax_ids:
                total_taxes += line.amount
            if abs(total_pct - 100.0) > 0.0001:
                raise osv.except_osv(
                    _('Error!'),
                    _('The percet total to distribute must be = 100.00%%'))
            #~ total_charges = item.total_charges - total_direct
            for line in item.line_ids:
                if line.apply_cost and total_charges:
                    line_pct = line.cost_pct or 0.0
                    line_applied = round(
                        (total_charges * line_pct) / 100.0, precision)
                    tax_applied = round(
                        (total_taxes * line_pct) / 100.0, precision)
                    real_cost_total = (
                        line.total_amount + line_applied + line.direct_cost +
                        tax_applied)
                    real_cost_unit = round(
                        real_cost_total / line.product_qty, precision)
                    obj_line.write(
                        cr, uid, [line.id],
                        {'cost_pct': line_pct if line_pct else 0,
                         'applied_cost': line_applied if line_applied else 0,
                         'applied_tax': tax_applied if tax_applied else 0,
                         'real_cost_total': real_cost_total if real_cost_total
                         else 0,
                         'real_cost_unit': real_cost_unit if real_cost_unit
                         else 0,
                         }, context)
        self.write(cr, uid, ids, {'valid': True}, context)
        return True

    def apply_and_update(self, cr, uid, ids, context):
        obj_line = self.pool.get('tcv.import.management.lines')
        obj_note = self.pool.get('tcv.import.notes')
        obj_exp = self.pool.get('tcv.import.management')
        context.update({'unlock_cost_distribution_data': True})
        for item in self.browse(cr, uid, ids, context={}):
            # clear all exiting cost lines
            exp = obj_exp.browse(cr, uid, item.import_id.id, context=context)
            if exp.line_ids:
                unlink_ids = []
                for line in exp.line_ids:
                    unlink_ids.append((2, line.id))
                if unlink_ids:
                    obj_exp.write(cr, uid, item.id, {'line_ids': unlink_ids},
                                  context)
            # add new cost lines
            if item.line_ids:
                for line in item.line_ids:
                    if line.cost_pct > 0:
                        data = {
                            'import_id': item.import_id.id,
                            'invoice_id': line.invoice_id.id,
                            'name': line.name,
                            'date': line.date,
                            'product_id': line.product_id.id,
                            'product_qty': line.product_qty,
                            'price_unit': line.price_unit,
                            'total_amount': line.total_amount,
                            'direct_cost': line.direct_cost,
                            'cost_pct': line.cost_pct,
                            'applied_cost': line.applied_cost,
                            'applied_tax': line.applied_tax,
                            'real_cost_total': line.real_cost_total,
                            'real_cost_unit': line.real_cost_unit,
                            }
                        obj_line.create(cr, uid, data, context)
                obj_note.create(
                    cr, uid,
                    {'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                     'name': _('Cost distribution data updated!'),
                     'locked': True,
                     },
                    context)
        context.update({'unlock_cost_distribution_data': False})
        return {'type': 'ir.actions.act_window_close'}

    def cancel_and_exit(self, cr, uid, ids, context):
        return {'type': 'ir.actions.act_window_close'}

    ##------------------------------------------------------------- Default_get

    def default_get(self, cr, uid, fields, context=None):
        res = super(tcv_import_cost_wizard, self).default_get(
            cr, uid, fields, context=context)
        if not res.get('currency_id'):
            company_id = self.pool.get('res.users').browse(
                cr, uid, uid, context=context).company_id.id
            obj_comp = self.pool.get('res.company')
            res.update({'currency_id': obj_comp.browse(
                cr, uid, company_id, context=context).currency_id.id})
        return res

    ##------------------------------------------------------------ on_change...

    def on_change_base(self, cr, uid, ids, import_id, base, line_ids):
        if line_ids:
            context = {'base': base}
            self.auto_distribute_cost_pct(cr, uid, ids, context)
            self.compute_cost_pct(cr, uid, ids, context)
        return {'value': {'valid': False}}

    def on_change_lines_ids(self, cr, uid, ids, lines_ids):
        res = {'value': {'valid': False, 'base': 'manual'}}
        return res

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_import_cost_wizard()


##--------------------------------------------- tcv_import_product_wizard_lines


class tcv_import_product_wizard_lines(osv.osv_memory):

    _name = 'tcv.import.product.wizard.lines'

    _description = ''

    ##-------------------------------------------------------------------------

    ##--------------------------------------------------------- function fields

    _columns = {
        'line_id': fields.many2one(
            'tcv.import.cost.wizard', 'Import document', required=True,
            ondelete='cascade'),
        'invoice_id': fields.many2one(
            'account.invoice', 'Invoice', ondelete='restrict', select=True),
        'name': fields.char(
            'Invoice ref', size=32, readonly=True),
        'date': fields.date(
            'Date', readonly=True),
        'product_id': fields.many2one(
            'product.product', 'Product', readonly=True),
        'product_qty': fields.float(
            'Quantity', digits_compute=dp.get_precision('Product UoM'),
            readonly=True),
        'price_unit': fields.float(
            'Unit price',
            digits_compute=dp.get_precision('Import management data'),
            readonly=True),
        'total_amount': fields.float(
            'Total amount', digits_compute=dp.get_precision('Account'),
            readonly=True),
        'total_charges': fields.float(
            'Total charges', digits_compute=dp.get_precision('Account'),
            readonly=True),
        'apply_cost': fields.boolean(
            'Apply cost', readonly=True),
        'direct_cost': fields.float(
            'Direct cost', digits_compute=dp.get_precision('Account'),
            readonly=False),
        'cost_pct': fields.float(
            '% of cost', digits_compute=dp.get_precision('Account'),
            readonly=False),
        'applied_cost': fields.float(
            'Applied cost', digits_compute=dp.get_precision('Account'),
            readonly=True),
        'applied_tax': fields.float(
            'Applied tax', digits_compute=dp.get_precision('Account'),
            readonly=True),
        'real_cost_total': fields.float(
            'Total cost', digits_compute=dp.get_precision('Account'),
            readonly=True),
        'real_cost_unit': fields.float(
            'Unit cost',
            digits_compute=dp.get_precision('Import management data'),
            readonly=True),
        }

    _defaults = {
        }

    _sql_constraints = [
        ('pct_valid_comm_range', 'CHECK(cost_pct between 0 and 100)',
         'The %% of cost must be in 0-100 range'),
        ]

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_import_product_wizard_lines()


##--------------------------------------------- tcv_import_product_wizard_taxes


class tcv_import_product_wizard_taxes(osv.osv_memory):

    _name = 'tcv.import.product.wizard.taxes'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'tax_id': fields.many2one(
            'tcv.import.cost.wizard', 'Import document', required=True,
            ondelete='cascade'),
        'date': fields.date(
            'Date', required=True, readonly=True),
        'name': fields.char(
            'Form #', size=64, required=False, readonly=True),
        'ref': fields.char(
            'Reference', size=64, required=False, readonly=True),
        'tax_name': fields.char(
            'Tax', size=64, required=False, readonly=True),
        'amount': fields.float(
            'Amount', digits_compute=dp.get_precision('Account'),
            readonly=True),
        }

    _defaults = {
        }

    _sql_constraints = [
        ]

    ##-----------------------------------------------------

    ##----------------------------------------------------- public methods

    ##----------------------------------------------------- buttons (object)

    ##----------------------------------------------------- on_change...

    ##----------------------------------------------------- create write unlink

    ##----------------------------------------------------- Workflow

tcv_import_product_wizard_taxes()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
