# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2013-09-10
#    Version: 0.0.0.1
#
#    Description:
#
#
##############################################################################

from datetime import timedelta
from datetime import datetime
from osv import fields, osv
from tools.translate import _
#~ import pooler
import decimal_precision as dp
import time
import netsvc
import logging
logger = logging.getLogger('server')

##------------------------------------------------------------------ sale_order


class sale_order(osv.osv):

    _inherit = 'sale.order'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def _compute_committed_stock(self, cr, uid, ids, prod_lot_id,
                                 context=None):
        obj_sol = self.pool.get('sale.order.line')
        sol_ids = obj_sol.search(cr, uid, [('prod_lot_id', '=', prod_lot_id),
                                           ('id', 'not in', ids)])
        committed_stock = 0
        stock_in_moves = 0
        comm_lines = []
        for item in obj_sol.browse(cr, uid, sol_ids, context={}):
            for move in item.move_ids:
                if move.state != 'cancel' and \
                        move.prodlot_id.id == prod_lot_id:
                    stock_in_moves += move.product_qty
                elif move.state == 'cancel' and \
                        move.prodlot_id.id == prod_lot_id:
                    committed_stock -= move.product_qty
            if item.order_id.state not in ('draft', 'cancel'):
                committed_stock += item.product_uom_qty
                comm_lines.append(item.order_id.name)
        if comm_lines:
            context.update({'committed_stock_info': ', '.join(comm_lines)})
        res = {'comm_stock': committed_stock - stock_in_moves,
               'comm_stock_info': ', '.join(comm_lines) if comm_lines else ''}
        return res

    def _make_invoice(self, cr, uid, order, lines, context=None):
        inv_id = super(sale_order, self).\
            _make_invoice(cr, uid, order, lines, context)
        if inv_id:
            obj_val = self.pool.get('ir.values')
            res_journal_default = obj_val.get(
                cr, uid, 'default', 'type=out_invoice', ['account.invoice'])
            journal_id = 0
            for j in res_journal_default:
                if j[1] == 'journal_id':
                    journal_id = j[2]
            if journal_id:
                obj_inv = self.pool.get('account.invoice')
                obj_inv.write(cr, uid, inv_id, {'journal_id': journal_id},
                              context={})

        return inv_id

    def _overdue(self, cursor, user, ids, name, arg, context=None):
        res = {}
        for sale in self.browse(cursor, user, ids, context=context):
            res[sale.id] = False
            if sale.state == 'progres' and \
                    sale.date_due > time.strftime('%Y-%m-%d 23:59:59') and\
                    sale.order_policy == 'prepaid':
                for invoice in sale.invoice_ids:
                    if invoice.state == 'draft':
                        res[sale.id] = True
                        break
                if not sale.invoice_ids:
                    res[sale.id] = True
        return res

    def _overdue_search(self, cursor, user, obj, name, args, context=None):
        if not len(args):
            return []
        context = context or {}
        cursor.execute(
            '''
            select * from
            (select id, string_agg(state, ', ' order by state) as state from
             (select so.id, COALESCE(ai.state, 'draft') as state
              from sale_order so
              left join sale_order_invoice_rel sor on so.id=sor.order_id
              left join account_invoice ai on sor.invoice_id=ai.id
              where so.state in ('draft', 'progress') and
                    so.date_due<=%(date_today)s
              ) as t group by id
             ) as q where not(state like '%%paid%%' or state like '%%open%%')
            order by id
            ''', {'date_today': context.get(
                'date_today', time.strftime('%Y-%m-%d 23:59:59'))})
        res = cursor.fetchall()
        if not res:
            return [('id', '=', 0)]
        return [('id', 'in', [x[0] for x in res])]

    ##--------------------------------------------------------- function fields

    _columns = {
        'name': fields.char('Order Reference', size=64, required=False,
                            readonly=True, select=True),
        'date_due': fields.date('Date due', required=False, readonly=False,
                                select=True,
                                help="Date until this order is valid"),
        'date_order': fields.date('Ordered Date', required=True,
                                  readonly=False, select=True),
        'payment_term': fields.many2one('account.payment.term', 'Payment Term',
                                        required=True),
        'order_policy': fields.selection([
            ('prepaid', 'Payment Before Delivery'),
            ('manual', 'Shipping & Manual Invoice'),
            ('postpaid', 'Invoice On Order After Delivery'),
            ('picking', 'Invoice From The Picking'),
        ], 'Shipping Policy', required=True, readonly=False),
        'user_id': fields.many2one('res.users', 'Salesman',
                                   states={'draft': [('readonly', False)]},
                                   select=True, required=True),
        'overdue': fields.function(
            _overdue, method=True, string='Overdue',
            fnct_search=_overdue_search, type='boolean',
            help="It indicates that an sale order has been overdue."),
        }

    _defaults = {
        'name': lambda *a: '/',
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    def action_invoice_create(self, cr, uid, ids, grouped=False,
                              states=['confirmed', 'done', 'exception'],
                              date_inv=False, context=None):
        for item in self.browse(cr, uid, ids, context={}):
            if not item.partner_id.customer:
                raise osv.except_osv(
                    _('Error!'),
                    _('Please must set partner as customer first'))
        res = super(sale_order, self).\
            action_invoice_create(cr, uid, ids, grouped, states, date_inv,
                                  context)
        return res

    ##---------------------------------------------------------- public methods

    def copy_data(self, cr, uid, id, default=None, context=None):
        res = super(sale_order, self).copy_data(cr, uid, id, default, context)
        if context.get('copy_order_lines'):
            pos = 0
            copy_order_lines = context.get('copy_order_lines')
            copy_order_lines.reverse()
            for l in copy_order_lines:
                res['order_line'][pos][2].update(
                    {'prod_lot_id': l.prod_lot_id and l.prod_lot_id.id,
                     'concept_id': l.concept_id and l.concept_id.id,
                     'tax_id': [(6, 0, [x.id for x in l.tax_id])]})
                if l.prod_lot_id and \
                        abs(l.prod_lot_id.stock_available - l.product_uom_qty):
                    #~ clear duplicated lot if not available
                    res['order_line'][pos][2].update({'prod_lot_id': 0})
                pos += 1
        #~ res['order_line'].reverse()
        return res

    def copy(self, cr, uid, id, default=None, context=None):
        default = default or {}
        context = context or {}
        sale_obj = self.browse(cr, uid, id, context=context)
        context.update({'copy_order_lines': sale_obj.order_line})
        default.update({
            'user_id': uid,
            'origin': _('%s (copy)') % sale_obj.name,
            'date_order': time.strftime('%Y-%m-%d'),
            'date_due': False,
            'name': '/',
        })
        return super(sale_order, self).\
            copy(cr, uid, id, default, context=context)

    def fields_get(self, cr, uid, fields=None, context=None):
        result = super(sale_order, self).fields_get(cr, uid, fields, context)
        for f in ('order_policy', 'user_id', 'date_due', 'origin',
                  'date_order'):
            if result.get(f):
                result[f]['readonly'] = True
                belongs = self.pool.get('res.users').\
                    user_belongs_groups(cr, uid, ('Sales / Manager', ),
                                        context)
                if belongs:
                    result[f]['readonly'] = False
        return result

    def cancel_overdue_orders(self, cr, uid, context=None):
        '''
        This method needs to be called from daily scheduled action to ensure
        to cancel all overdue sales orders.
        '''
        cfg = self.pool.get('tcv.sale.order.config').get_config(cr, uid)
        date_limit = (datetime.today() - timedelta(days=cfg.days_to_cancel)
                      ).date().strftime('%Y-%m-%d')
        logger.info(
            'Looking for sale order overdued to be cancelled. Limit date: %s' %
            date_limit)
        count = 0
        overdue_orders = self._overdue_search(
            cr, uid, None, 'overdue', [('overdue', '=', False)], context)
        overdue_ids = overdue_orders and overdue_orders[0][2] or []
        wf_service = netsvc.LocalService("workflow")
        for item in self.browse(cr, uid, overdue_ids, context={}):
            if item.date_due <= date_limit and not item.picked_rate and  \
                    not item.invoiced_rate and item.order_policy == 'prepaid':
                picking_ids = filter(None, [
                    x.id if x.state not in ('draft', 'cancel') else None
                    for x in item.picking_ids])
                if not picking_ids:
                    logger.info('Cancel overdued sale order : %s, %s' %
                                (item.name, item.partner_id.name))
                    count += 1
                    wf_service.trg_validate(
                        uid, 'sale.order', item.id, 'cancel', cr)
                    self.write(
                        cr, uid, item.id,
                        {'note': '\n'.join((
                            _('Cancel overdued sale order %s') %
                            time.strftime('%d-%m-%Y'),
                            item.note or ''))},
                        context=context)
        if not count:
            logger.info('No sale orders to cancel.')
        return True

    def get_sale_price(self, cr, uid, ids, obj_price, obj_line, context=None):
        """
        Calculation total price
        """
        return True
    ##-------------------------------------------------------- buttons (object)

    def button_lot_list(self, cr, uid, ids, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        so_brw = self.browse(cr, uid, ids, context={})[0]
        context.update({'sale_order_id': so_brw.id,
                        'default_sale_id': so_brw.id,
                        'default_partner_id': so_brw.partner_id.id,
                        })
        view_id = self.pool.get('ir.ui.view').search(
            cr, uid, [('name', '=', 'tcv.sale.lot.list.form')])
        return {'name': _('Load lot list'),
                'type': 'ir.actions.act_window',
                'res_model': 'tcv.sale.lot.list',
                'view_type': 'form',
                'view_id': view_id,
                'view_mode': 'form',
                'nodestroy': True,
                'target': 'new',
                'domain': "",
                'context': context}

    def button_release_lots(self, cr, uid, ids, context=None):
        reserved_ids = self.search(
            cr, uid, [('origin', '=', 'RESERVA_ACROPOLIS_201701')])
        ids = isinstance(ids, (int, long)) and [ids] or ids
        for item in self.browse(cr, uid, ids, context={}):
            if item.id in reserved_ids:
                return True
            cr.execute('''
                delete from sale_order_line
                where id in (
                      select sol.id
                      from sale_order_line sol
                      where sol.order_id in %s and sol.prod_lot_id in (
                            select prod_lot_id from sale_order_line where
                            state != 'cancel' and
                            order_id = %s)
                            )
                ''', (tuple(reserved_ids), item.id))
        return True

    def button_update_lots_prices(self, cr, uid, ids, context=None):
        """
        Button for update actual prices of lots in lines
        """
        obj_price = self.pool.get('tcv.pricelist')
        obj_line = self.pool.get('sale.order.line')
        for sale_order in self.browse(cr, uid, ids, context=context):
            product_ids = []
            discount_percentage = \
                sale_order.partner_id.discount_id.discount_percentage
            for line in sale_order.order_line:
                if line.product_id.id not in product_ids:
                    price_id = obj_price.search(
                        cr, uid, [('product_id', '=', line.product_id.id),
                                  ('date', '<=', time.strftime('%Y-%m-%d'))],
                        order="date desc", limit=1)
                    price = price_id and obj_price.browse(
                        cr, uid, price_id[0], context=context).price_unit \
                        or line.price_unit
                    if discount_percentage:
                        discount = (price * discount_percentage) / 100
                        total_price = price - discount
                    else:
                        total_price = price
                    line_ids = obj_line.search(
                        cr, uid, [('order_id', '=', line.order_id.id),
                                  ('product_id', '=', line.product_id.id)])
                    obj_line.write(
                        cr, uid, line_ids, {'price_unit': total_price},
                        context=context)
                    product_ids.append(line.product_id.id)
        return True

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    def create(self, cr, uid, vals, context=None):
        context = context or {}
        if not vals.get('date_due'):
            cfg = self.pool.get('tcv.sale.order.config').get_config(cr, uid)
            date_due = datetime.strptime(time.strftime('%Y-%m-%d'), '%Y-%m-%d')
            date_due = (date_due +
                        timedelta(days=cfg.days_to_due)).strftime('%Y-%m-%d')
            vals.update({'date_due': date_due})
        if not vals.get('name') or vals.get('name') == '/':
            vals.update({'name': self.pool.get('ir.sequence').
                         get(cr, uid, 'sale.order')})
        if context.get('default_pricelist_id'):
            vals.update({'pricelist_id': context['default_pricelist_id']})
        res = super(sale_order, self).create(cr, uid, vals, context)
        if context.get('default_proforma_id'):
            obj_prf = self.pool.get('tcv.sale.proforma')
            obj_prf.write(cr, uid, [context['default_proforma_id']],
                          {'sale_order_id': res}, context=context)
        return res

    ##---------------------------------------------------------------- Workflow

    def test_sale_order(self, cr, uid, ids, *args):
        '''
        Make some validations before sale order aproval
        validate lot assignement for sale order
        (if product.track_outgoing == True)
        res = str with error msg (ok not(res == '')
        '''
        ids = isinstance(ids, (int, long)) and [ids] or ids
        res = ''
        dup = {}
        context = {}
        #~ obj_ail = self.pool.get('account.invoice.line')
        for i in self.browse(cr, uid, ids, context={}):
            if i.date_due and i.date_due < time.strftime('%Y-%m-%d'):
                raise osv.except_osv(
                    _('Error!'),
                    _('Can\'t validate an order while date due is < today'))
            if not i.order_line:
                raise osv.except_osv(_('No Order Lines!'),
                                     _('Please create some order lines.'))
            if i.pricelist_id.currency_id.id == i.company_id.currency_id.id:
                if not i.partner_id.vat:
                    raise osv.except_osv(
                        _('Error!'),
                        _('Please set partner\'s VAT'))
            if not i.partner_id.property_account_receivable:
                raise osv.except_osv(
                    _('Error!'),
                    _('Please check partner\'s accountin info'))
            for l in i.order_line:
                #~ Check lot's stock_available
                if l.product_id.stock_driver == 'slab' and l.prod_lot_id and \
                        l.prod_lot_id.stock_available < l.product_uom_qty:
                    raise osv.except_osv(
                        _('Error!'),
                        _('Not enough stock available: %s %s') %
                        (l.name, l.prod_lot_id and l.prod_lot_id.name))
                #~ Check if lot is assigned
                if l.product_id.track_outgoing:
                    if not(l.prod_lot_id):
                        res += '\t- %s\n' % (l.name)
                    #~ Check duplicated product lot
                    key = l.prod_lot_id and l.prod_lot_id.id or ''
                    if key:
                        if dup.get(key):
                            raise osv.except_osv(
                                _('Error!'),
                                _('This lot is duplicated in the order:\n%s') %
                                (dup[key]))
                        else:
                            dup.update({key: '%s: %s' % (
                                l.product_id.name, l.prod_lot_id.full_name)})
                if not l.product_uom_qty:
                    raise osv.except_osv(
                        _('Error!'),
                        _('Must indicate a quantity for line: %s %s') %
                        (l.name, l.prod_lot_id and l.prod_lot_id.name))

                #~ https://bugs.launchpad.net/openerp-tecvemar/+bug/1009175
                if l.product_id.track_outgoing and \
                   l.prod_lot_id.product_id and \
                   l.product_id.id != l.prod_lot_id.product_id.id:
                    raise osv.except_osv(
                        _('Product error!'),
                        _("The product: %s dosen't correspond with lot's " +
                          "product (%s - %s)") %
                        (l.product_id.name, l.prod_lot_id.full_name,
                         l.prod_lot_id.product_id.name))
                # Check for "compromised" lots
                if l.prod_lot_id:
                    cs = self._compute_committed_stock(
                        cr, uid, ids, l.prod_lot_id.id, context=context)
                    if cs.get('comm_stock'):
                        if l.prod_lot_id.virtual - cs['comm_stock'] < \
                                l.product_uom_qty:
                            raise osv.except_osv(
                                _('Error!'),
                                _('The lot %s is commited in other ' +
                                  'order(s):\n%s') %
                                (l.prod_lot_id.name,
                                 cs['comm_stock_info']))
                    # check unprocesed moves
                    for m in l.prod_lot_id.move_ids:
                        if m.state not in ('done', 'cancel'):
                            raise osv.except_osv(
                                _('Error!'),
                                _('The lot %s is compromised in picking: %s') %
                                (l.prod_lot_id.name,
                                 m.picking_id and m.picking_id.name))

        if res:  # error if lot isn't assigned
            raise osv.except_osv(_('No product lot assigned!'),
                                 _('You must assign a product lot for:\n%s') %
                                 (res))
        return True

    def action_cancel_draft(self, cr, uid, ids, *args):
        for item in self.browse(cr, uid, ids, context={}):
            if item.date_due and item.date_due < time.strftime('%Y-%m-%d'):
                raise osv.except_osv(
                    _('Error!'),
                    _('Can\'t reset an order while date due is < today'))
            if item.invoice_ids:
                raise osv.except_osv(
                    _('Error!'),
                    _('Unable to restore order as have invoices related'))
        return super(sale_order, self).action_cancel_draft(cr, uid, ids, args)


sale_order()


##------------------------------------------------------------- sale_order_line


class sale_order_line(osv.osv):

    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        """Dont confirm a sale order if not have lots"""
        for rec in self.browse(cr, uid, ids, context=context):
            if rec.state not in ['draft', 'cancel']:
                raise osv.except_osv(
                    _('Invalid action !'),
                    _('Cannot delete a sales order line which is %s !') %
                    (rec.state,))
        return super(sale_order_line, self).unlink(
            cr, uid, ids, context=context)

    def invoice_line_create(self, cr, uid, ids, context={}):
        create_ids = super(sale_order_line, self).invoice_line_create(
            cr, uid, ids, context)
        order_line_sale_brws = self.browse(cr, uid, ids)
        for line_sale in order_line_sale_brws:  # lineas de la orden de venta
            # se cargan aqui para ir reflejando updates (write)
            invoice_line_brws = self.pool.get('account.invoice.line').browse(
                cr, uid, create_ids)
            can_write = True
            for line_invoice in invoice_line_brws:  # lineas de la factura
                if can_write and line_sale.prod_lot_id.id and \
                    line_sale.product_id == line_invoice.product_id and \
                    line_sale.product_uom_qty == line_invoice.quantity and \
                        not(line_invoice.prod_lot_id):
                    # si es el mismo producto, cantidad y no se ha asignado el
                    # lote se actualiza el registro
                    # (solo 1 vez x can_write) y si tiene lote
                    # (line_sale.prod_lot_id.id)
                    upd_data = {'prod_lot_id': line_sale.prod_lot_id.id,
                                'pieces': line_sale.pieces,
                                'track_outgoing': line_sale.track_outgoing}
                    self.pool.get('account.invoice.line').write(
                        cr, uid, line_invoice.id, upd_data)
                    can_write = False
        return create_ids

    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
                          uom=False, qty_uos=0, uos=False, name='',
                          partner_id=False, lang=False, update_tax=True,
                          date_order=False, packaging=False,
                          fiscal_position=False, flag=False):

        res = super(sale_order_line, self).\
            product_id_change(cr, uid, ids, pricelist, product, qty, uom,
                              qty_uos, uos, name, partner_id, lang, update_tax,
                              date_order, packaging, fiscal_position, flag)
        if product:
            product_obj = self.pool.get('product.product')
            produc_brw = product_obj.browse(cr, uid, product)
            res['value']['track_outgoing'] = produc_brw.track_outgoing
            res['value']['stock_driver'] = produc_brw.stock_driver
        else:
            res['value']['track_outgoing'] = False

        return res

    def warning_on_prod_lot_id_used(self, cr, uid, ids, prod_lot_id):
        res = {}
        used_lot_ids = self.search(cr, uid, [('prod_lot_id', '=', prod_lot_id),
                                   ('state', '!=', 'cancel')])
        if used_lot_ids:
            used_lots = self.browse(cr, uid, used_lot_ids, context={})
            orders = '\n\t'.join(['%s - %s' %
                                 (x.order_id.name, x.order_id.user_id.name)
                                 for x in used_lots])
            res.update({'warning':
                        {'title': 'Warning',
                         'message': 'Lot: %s used in order(s):\n\t%s'
                         % (used_lots[0].prod_lot_id.name, orders)}})
        return res

    def on_change_qty(self, cr, uid, ids, partner, pricelist, id_lot, uom_qty,
                      pieces_qty, context=None):
        context = context or {}
        ids = isinstance(ids, (int, long)) and [ids] or ids
        res = {}
        product_uom_obj = self.pool.get('product.uom')
        spl_obj = self.pool.get('stock.production.lot')
        if id_lot:
            spl_brw = spl_obj.browse(cr, uid, id_lot)
            res = self.product_id_change(
                cr, uid, ids, pricelist, spl_brw.product_id.id, qty=uom_qty,
                uom=False, qty_uos=0, uos=False, name='', partner_id=partner,
                lang=False, update_tax=True, date_order=False, packaging=False,
                fiscal_position=False, flag=False)
            if spl_brw.product_id.stock_driver in ('tile', 'slab', 'block'):
                area = product_uom_obj.\
                    _compute_area(
                        cr, uid, spl_brw.product_id.stock_driver, pieces_qty,
                        spl_brw.length, spl_brw.heigth, spl_brw.width)
                if pieces_qty == 0:
                    pieces_max = product_uom_obj.\
                        _compute_pieces2(
                            cr, uid, spl_brw.product_id.stock_driver,
                            spl_brw.virtual, spl_brw.length, spl_brw.heigth,
                            spl_brw.width)
                    res['value'].update({
                        'pieces': pieces_max,
                        'product_uom_qty': spl_brw.virtual,
                        'product_uos_qty': spl_brw.virtual,
                        'product_id': spl_brw.product_id and
                        spl_brw.product_id.id,
                        'product_uom': spl_brw.product_id.uom_id and
                        spl_brw.product_id.uom_id.id,
                        'name': spl_brw.product_id and
                        spl_brw.product_id.name})
                else:
                    res['value'].update({
                        'pieces': pieces_qty,
                        'product_uom_qty': area,
                        'product_uos_qty': area,
                        'product_id': spl_brw.product_id and
                        spl_brw.product_id.id,
                        'product_uom': spl_brw.product_id.uom_id and
                        spl_brw.product_id.uom_id.id,
                        'name': spl_brw.product_id and
                        spl_brw.product_id.name})
                if area > spl_brw.virtual:
                    raise osv.except_osv(
                        _('Processing Error'),
                        _('The quantity is not available'))
                if spl_brw.product_id.stock_driver == 'block':
                    res['value'].update({'pieces': 1})
                res.update(self.warning_on_prod_lot_id_used(
                    cr, uid, ids, id_lot))
        return res

    _inherit = 'sale.order.line'

    _columns = {
        'product_uom_qty': fields.float(
            'Quantity', digits_compute=dp.get_precision('Product UoM')),
        'prod_lot_id': fields.many2one(
            'stock.production.lot', 'Production lot', ondelete='restrict'),
        'pieces': fields.integer(
            'Pieces', require=True),
        'track_outgoing': fields.related(
            'product_id', 'track_outgoing', type='bool',
            relation='product.product'),
        'stock_driver': fields.related(
            'product_id', 'stock_driver', type='char', size=16,
            relation='product.product')}

    _sql_constraints = [
        ('prod_lot_id_uniq', 'UNIQUE(prod_lot_id,order_id)',
         'The lot must be unique!'),
        ]


sale_order_line()


##------------------------------------------------------- tcv_sale_order_config


class tcv_sale_order_config(osv.osv):

    _name = 'tcv.sale.order.config'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'company_id': fields.many2one(
            'res.company', 'Company', required=True,
            readonly=True, ondelete='restrict'),
        'days_to_due': fields.integer(
            'Days to due'),
        'days_to_cancel': fields.integer(
            'Days to cancel',
            help="Autocancel sale order after # of days (from order's date)"),
        'quotation_cond': fields.text(
            'Quotation conditions', translate=True),
        'sale_order_cond': fields.text(
            'Sale order conditions', translate=True),
        'invoice_cond': fields.text(
            'Invoice conditions', translate=True),
        'proforma_cond': fields.text(
            'Invoice conditions', translate=True),
        }

    _defaults = {
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company').
        _company_default_get(cr, uid, self._name, context=c),
        'days_to_due': lambda *a: 5,
        'days_to_cancel': lambda *a: 15,
        }

    _sql_constraints = [
        ('date_due_range', 'CHECK(days_to_due >= 1)',
         'The days to due must be >= 1!'),
        ('date_cancel_range', 'CHECK(days_to_cancel >= days_to_due)',
         'The days to due must be >= days to cancel!'),
        ]

    ##-----------------------------------------------------

    ##----------------------------------------------------- public methods

    def get_config(self, cr, uid, company_id=None, context=None):
        cfg_id = self.search(cr, uid, [])
        if cfg_id and len(cfg_id) == 1:
            cfg_id = cfg_id[0]
        else:
            raise osv.except_osv(
                _("Error!"),
                _("Invalid configuration settings. (%s)") % self._name)
        return self.browse(cr, uid, cfg_id, context)

    ##----------------------------------------------------- buttons (object)

    ##----------------------------------------------------- on_change...

    ##----------------------------------------------------- create write unlink

    ##----------------------------------------------------- Workflow


tcv_sale_order_config()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
