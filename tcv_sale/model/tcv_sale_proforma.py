# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2014-04-04
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


def _lang_get(self, cr, uid, context=None):
    obj = self.pool.get('res.lang')
    ids = obj.search(cr, uid, [('translatable', '=', True)])
    res = obj.read(cr, uid, ids, ['code', 'name'], context=context)
    res = [(r['code'], r['name']) for r in res]
    return res

##----------------------------------------------------------- tcv_sale_proforma


class tcv_sale_proforma(osv.osv):

    _name = 'tcv.sale.proforma'

    _description = 'tcv_sale_proforma'

    _order='name desc'

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def _compute_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for item in self.browse(cr, uid, ids, context=context):
            total = 0
            for line in item.line_ids:
                total += line.line_total
            res[item.id] = {'amount_total': total}
        return res

    ##--------------------------------------------------------- function fields

    _columns = {
        'name': fields.char(
            'Reference', size=16, required=True, readonly=True),
        'date': fields.date(
            'Date', required=True, readonly=True,
            states={'draft': [('readonly', False)]}, select=True),
        'revision': fields.integer(
            'Revision', readonly=True),
        'context_lang': fields.selection(
            _lang_get, 'Language', required=True,
            help="Sets the language for the interface, when UI " +
            "translations are available"),
        'partner_id': fields.many2one(
            'res.partner', 'Partner', change_default=True, readonly=True,
            required=True, states={'draft': [('readonly', False)]},
            ondelete='restrict'),
        'partner_address_id': fields.many2one(
            'res.partner.address', 'Invoice Address', readonly=True,
            required=True, states={'draft': [('readonly', False)]},
            help="Invoice address for current proforma."),
        'sale_order_id': fields.many2one(
            'sale.order', 'Sale order', change_default=True, readonly=False,
            ondelete='set null'),
        'incoterm_id': fields.many2one(
            'stock.incoterms', 'Incoterm', readonly=True, required=True,
            states={'draft': [('readonly', False)]}, ondelete='restrict'),
        'pricelist_id': fields.many2one(
            'product.pricelist', 'Pricelist', required=True, readonly=True,
            states={'draft': [('readonly', False)]},
            help="Pricelist for current proforma."),
        'currency_id': fields.related(
            'pricelist_id', 'currency_id', type='many2one',
            relation='res.currency', string='Currency', store=False,
            readonly=True),
        'user_id': fields.many2one(
            'res.users', 'User', readonly=True, select=True,
            states={'draft': [('readonly', False)]}, ondelete='restrict'),
        'narration': fields.text(
            'Notes', readonly=False),
        'shipment_port': fields.char(
            'Shipment port', size=24, readonly=True,
            states={'draft': [('readonly', False)]}),
        'arrival_port': fields.char(
            'Arrival port', size=24, readonly=True,
            states={'draft': [('readonly', False)]}),
        'amount_total': fields.function(
            _compute_all, method=True, type='float', string='Total amount',
            digits_compute=dp.get_precision('Account'), multi='all'),
        'line_ids': fields.one2many(
            'tcv.sale.proforma.lines', 'proforma_id', 'Lines', readonly=True,
            states={'draft': [('readonly', False)]}),
        'state': fields.selection(
            [('draft', 'Draft'), ('done', 'Done'), ('cancel', 'Cancelled')],
            string='State', required=True, readonly=True),
        'company_id': fields.many2one(
            'res.company', 'Company', required=True, readonly=True,
            ondelete='restrict'),
        'payment_term': fields.many2one(
            'account.payment.term', 'Payment Term', readonly=True,
            states={'draft': [('readonly', False)]}),
        }

    _defaults = {
        'name': '/',
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        'revision': 0,
        'state': 'draft',
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company').
        _company_default_get(cr, uid, self._name, context=c),
        'currency_id': lambda self, cr, uid, c: self.pool.get('res.users').
        browse(cr, uid, uid, c).company_id.currency_id.id,
        'user_id': lambda s, c, u, ctx: u,
        'context_lang': 'en_US',
        }

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', 'The reference must be unique!'),
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    def button_sale_order(self, cr, uid, ids, context=None):
        if not ids:
            return []
        ids = isinstance(ids, (int, long)) and [ids] or ids
        item = self.browse(cr, uid, ids[0], context=context)
        if item.sale_order_id:
            raise osv.except_osv(_('Error!'), _('Can\'t create order!'))
        return {
            'name': _("Sale order"),
            'view_mode': 'form',
            'view_id': self.pool.get('ir.ui.view').
            search(cr, uid, [('model', '=', 'sale.order'),
                             ('name', '=', 'sale.order.form')]),
            'view_type': 'form',
            'res_model': 'sale.order',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'domain': '[]',
            'context': {
                'default_partner_id': item.partner_id.id,
                'default_partner_shipping_id': item.partner_address_id.id,
                'default_origin': 'Proforma: %s, Rev: %s' % (item.name,
                                                             item.revision),
                'default_incoterm': item.incoterm_id.id,
                'default_pricelist_id': item.pricelist_id.id,
                'default_order_policy': 'manual',
                'default_user_id': item.user_id.id,
                'default_payment_term': item.payment_term.id,
                'default_proforma_id': item.id,
                }
        }

    ##------------------------------------------------------------ on_change...

    def on_change_partner_id(self, cr, uid, ids, partner_id):
        res = {'partner_address_id': False}
        if partner_id:
            obj_prn = self.pool.get('res.partner')
            partner = obj_prn.browse(cr, uid, partner_id, context=None)
            address_id = [addr for addr in partner.address if
                          addr.type == 'invoice']
            if address_id:
                res.update({'partner_address_id': address_id[0].id})
        return {'value': res}

    def on_change_line_ids(self, cr, uid, ids, line_ids):
        res = {'amount_total': 0}
        if line_ids:
            total = 0
            for line in line_ids:
                total += line[2]['line_total']
            res.update({'amount_total': total})
        return {'value': res}
    ##----------------------------------------------------- create write unlink

    def create(self, cr, uid, vals, context=None):
        if not vals.get('name') or vals.get('name') == '/':
            vals.update({'name': self.pool.get('ir.sequence').
                         get(cr, uid, 'tcv.sale.proforma')})
        res = super(tcv_sale_proforma, self).create(cr, uid, vals, context)
        return res

    ##---------------------------------------------------------------- Workflow

    def button_draft(self, cr, uid, ids, context=None):
        vals = {'state': 'draft'}
        return self.write(cr, uid, ids, vals, context)

    def button_done(self, cr, uid, ids, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        for item in self.browse(cr, uid, ids, context={}):
            vals = {'state': 'done',
                    'revision': item.revision + 1}
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

tcv_sale_proforma()


##----------------------------------------------------- tcv_sale_proforma_lines


class tcv_sale_proforma_lines(osv.osv):

    _name = 'tcv.sale.proforma.lines'

    _description = 'tcv_sale_proforma_lines'

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def _compute_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for item in self.browse(cr, uid, ids, context=context):
            res[item.id] = {'line_total': item.qty * item.price}
        return res

    ##--------------------------------------------------------- function fields

    _columns = {
        'proforma_id': fields.many2one(
            'tcv.sale.proforma', 'Proforma', required=True,
            ondelete='cascade'),
        'product_id': fields.many2one(
            'product.product', 'Product', ondelete='restrict'),
        'uom_id': fields.related(
            'product_id', 'uom_id', type='many2one', relation='product.uom',
            string='Uom', store=False, readonly=True),
        'qty': fields.float(
            'Quantity', digits_compute=dp.get_precision('Account'),
            readonly=False),
        'price': fields.float(
            'Unit price', digits_compute=dp.get_precision('Account'),
            readonly=False),
        'line_total': fields.function(
            _compute_all, method=True, type='float', string='Total amount',
            digits_compute=dp.get_precision('Account'), multi='all'),
        }

    _defaults = {
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    def on_change_product_id(self, cr, uid, ids, product_id):
        res = {}
        if product_id:
            obj_prd = self.pool.get('product.product')
            prd_brw = obj_prd.browse(cr, uid, product_id, context={})
            res.update({'uom_id': prd_brw.uom_id.id})
        return {'value': res}

    def on_change_qty(self, cr, uid, ids, qty, price):
        res = {'line_total': 0}
        if qty and price:
            res.update({'line_total': qty * price})
        return {'value': res}

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_sale_proforma_lines()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
