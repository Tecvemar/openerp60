# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2013-08-26
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

##-------------------------------------------------------------- tcv_block_cost


class tcv_block_cost(osv.osv):

    _name = 'tcv.block.cost'

    _description = ''

    _method_types = {'qty': 'By units', 'size': 'By sizes', 'manual': 'Manual'}

    ##-----------------------------------------------------

    def default_get(self, cr, uid, fields, context=None):
        context = context or {}
        data = super(tcv_block_cost, self).\
            default_get(cr, uid, fields, context)
        if context.get('active_model') == u'account.invoice' and \
                context.get('active_id'):
            obj_inv = self.pool.get('account.invoice')
            inv = obj_inv.browse(cr, uid, context.get('active_id'),
                                 context=context)
            data.update(
                {'date': inv.date_document,
                 'invoice_id': inv.id,
                 'supplier_invoice_number': inv.supplier_invoice_number,
                 'partner_id': inv.partner_id.id,
                 'transp_amount': inv.amount_untaxed,
                 'invoice_name': inv.name,
                 'invoice_date': inv.date_document})
        return data

    ##----------------------------------------------------- _internal methods

    def _update_lot_cost(self, cr, uid, ids, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        obj_lot = self.pool.get('stock.production.lot')
        for item in self.browse(cr, uid, ids, context={}):
            for block in item.lot_ids:
                obj_lot.write(cr, uid, block.prod_lot_id.id,
                              {'property_cost_price': block.cost_unit,
                               'date': block.date_arrival}, context=context)

    def _gen_account_move_line(self, company_id, partner_id, account_id, name,
                               debit, credit):
        return (0, 0, {
                'auto': True,
                'company_id': company_id,
                'partner_id': partner_id,
                'account_id': account_id,
                'name': name,
                'debit': debit,
                'credit': credit,
                'reconcile': False,
                })

    def _gen_account_move(self, cr, uid, ids, context=None):
        obj_move = self.pool.get('account.move')
        move_id = None
        for item in self.browse(cr, uid, ids, context={}):
            i = item.invoice_id
            transport_inv = \
                _('\n\t\tNº %s, Supplier: %s, Description: %s, date: %s') % \
                (i.number, i.partner_id.name, i.name, i.date_document)
            period_id = self.pool.get('account.period').\
                find(cr, uid, dt=item.date)
            move = {
                'ref': '%s %s' % (_('Block costing:'), item.name),
                'journal_id': item.journal_id.id,
                'date': item.date,
                'period_id': period_id[0] if period_id else 0,
                'company_id': item.company_id.id,
                'state': 'draft',
                'to_check': False,
                'narration': _('Block costing (%s):\n\n\t' +
                               'Transport invoice: %s\n\n\tBlocks:') %
                              (_(self._method_types.get(item.type, '')),
                                  transport_inv),
                }
            lines = []
            for line in item.lot_ids:
                line_name = '%s %s' % (line.prod_lot_id.name,
                                       line.product_id.name)
                line_acc = (
                    line.product_id.property_stock_account_input and
                    line.product_id.property_stock_account_input.id) or \
                    (line.product_id.categ_id.
                        property_stock_account_input_categ and
                     line.product_id.categ_id.
                        property_stock_account_input_categ.id)
                if not line_acc:
                    raise osv.except_osv(
                        _('Error!'),
                        _('Can\'t find the stock input account for %s ' +
                          'product') %
                        (line.product_id.name))
                move.update({'narration': '%s\n\t\t%s' %
                             (move['narration'], line_name)})
                lines.append(self._gen_account_move_line(
                    item.company_id.id, item.partner_id.id,
                    line_acc, '%s %s' % (_('Block costing:'), line_name),
                    line.transp_unit, 0))
            lines.append(self._gen_account_move_line(
                item.company_id.id, item.partner_id.id,
                item.account_id.id, move['ref'], 0,
                item.transp_amount))
            lines.reverse()
            move.update({'line_id': lines})
            move_id = obj_move.create(cr, uid, move, context)
            obj_move.post(cr, uid, [move_id], context=context)
            if move_id:
                self.write(cr, uid, item.id, {'move_id': move_id},
                           context=context)
                #~ self.do_reconcile(cr, uid, item, move_id, context)
        return move_id

    ##----------------------------------------------------- function fields

    _columns = {
        'name': fields.char('Ref:', size=64, required=False, readonly=True),
        'date': fields.date('Date', required=True, readonly=True,
                            states={'draft': [('readonly', False)]},
                            select=True,
                            help="The day of block arrival and account move"),
        'invoice_id': fields.many2one('account.invoice', 'Number',
                                      ondelete='restrict', select=True,
                                      required=True, readonly=True,
                                      states={'draft': [('readonly', False)]}),
        'invoice_name': fields.related('invoice_id', 'name', type='char',
                                       string='Description', size=64,
                                       store=False, readonly=True),
        'supplier_invoice_number': fields.related(
            'invoice_id', 'supplier_invoice_number', type='char',
            string='Invoice #', size=64, store=False, readonly=True),
        'partner_id': fields.related('invoice_id', 'partner_id',
                                     type='many2one', relation='res.partner',
                                     string='Supplier', store=False,
                                     readonly=True),
        'invoice_date': fields.related('invoice_id', 'date_document',
                                       type='date', string='Date inv',
                                       store=False, readonly=True),
        'transp_amount': fields.float('Amount', digits_compute=dp.
                                      get_precision('Account'), required=True,
                                      readonly=True,
                                      states={'draft': [('readonly', False)]}),
        'lot_ids': fields.one2many('tcv.block.cost.lots', 'line_id', 'String',
                                   readonly=True,
                                   states={'draft': [('readonly', False)]}),
        'type': fields.selection(
            _method_types.items(), string='Method', required=True,
            readonly=True, states={'draft': [('readonly', False)]},
            help="Method to distribute transportation cost:\n" +
            "by units, by block size (total volume) or manual"),
        'company_id': fields.many2one('res.company', 'Company',
                                      required=True, readonly=True,
                                      ondelete='restrict'),
        'journal_id': fields.many2one('account.journal', 'Journal',
                                      required=True, ondelete='restrict',
                                      readonly=True,
                                      states={'draft': [('readonly', False)]}),
        'account_id': fields.many2one(
            'account.account', 'Transp. account', required=True,
            ondelete='restrict', help="Account for block transport (stock)",
            readonly=True, states={'draft': [('readonly', False)]}),
        'move_id': fields.many2one('account.move', 'Account move',
                                   ondelete='restrict', select=True,
                                   readonly=True,
                                   help="The move of this entry line."),
        'validator': fields.many2one(
            'res.users', 'Approved by', readonly=True, select=True,
            ondelete='restrict'),
        'note': fields.char('Notes', size=128, required=False,
                            readonly=False),
        'prod_lot_id': fields.related('lot_ids', 'prod_lot_id',
                                      type='many2one',
                                      relation='stock.production.lot',
                                      string='Production lot'),
        'state': fields.selection([('draft', 'Draft'), ('done', 'Done'),
                                   ('cancel', 'Cancelled')],
                                  string='State', required=True,
                                  readonly=True),
        }

    _defaults = {
        'name': lambda *a: '/',
        'type': lambda *a: 'qty',
        'state': lambda *a: 'draft',
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company').
        _company_default_get(cr, uid, 'obj_name', context=c),
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        }

    _sql_constraints = [
        ('invoice_id_uniq', 'UNIQUE(invoice_id)',
         'The transport invoice must be unique!'),
        ]

    ##-----------------------------------------------------

    ##----------------------------------------------------- public methods

    ##----------------------------------------------------- buttons (object)

    def compute_block_cost(self, cr, uid, ids, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        obj_lin = self.pool.get('tcv.block.cost.lots')
        roundto = 2
        for item in self.browse(cr, uid, ids, context={}):
            line_ids = map(lambda x: x.id, item.lot_ids)
            if line_ids:
                if item.type == 'qty':
                    #~ count groups
                    groups = {}
                    for block in item.lot_ids:
                        if block.group == 0:
                            groups.update({block.prod_lot_id.name: block})
                        else:
                            if groups.get(block.group):
                                groups[block.group].append(block)
                            else:
                                groups.update({block.group: [block]})
                    transp_unit = round(item.transp_amount /
                                        len(groups), roundto)
                    for g in groups:
                        if isinstance(g, (int, long)):
                            vol = group_tot = 0

                            for i in groups[g]:
                                vol += i.block_size
                            for i in groups[g]:
                                transp_group = round((transp_unit *
                                                      i.block_size) /
                                                     vol, roundto)
                                obj_lin.write(cr, uid, i.id,
                                              {'transp_unit': transp_group},
                                              context=context)
                                group_tot += transp_group

                        else:
                            obj_lin.write(cr, uid, groups[g].id,
                                          {'transp_unit': transp_unit},
                                          context=context)
                elif item.type == 'size':
                    tot_size = 0
                    for block in item.lot_ids:
                        tot_size += block.block_size
                    for block in item.lot_ids:
                        transp_unit = round((item.transp_amount *
                                             block.block_size) /
                                            tot_size, roundto)
                        obj_lin.write(cr, uid, block.id,
                                      {'transp_unit': transp_unit},
                                      context=context)
                #~ else: ## manual
                    #~ return True
        return True

    ##----------------------------------------------------- on_change...

    def on_change_invoice_id(self, cr, uid, ids, invoice_id):
        if invoice_id:
            obj_invl = self.pool.get('account.invoice')
            invl = obj_invl.browse(cr, uid, invoice_id, context=None)
            res = {'value':
                   {'supplier_invoice_number': invl.supplier_invoice_number,
                    'partner_id': invl.partner_id.id,
                    'transp_amount': invl.amount_untaxed,
                    'invoice_name': invl.name,
                    'invoice_date': invl.date_document}}
        return res

    ##----------------------------------------------------- create write unlink

    def create(self, cr, uid, vals, context=None):
        if not vals.get('name') or vals.get('name') == '/':
            vals.update({'name': self.pool.get('ir.sequence').
                         get(cr, uid, 'tcv.block.cost')})
        res = super(tcv_block_cost, self).create(cr, uid, vals, context)
        return res

    def unlink(self, cr, uid, ids, context=None):
        unlink_ids = []
        for item in self.browse(cr, uid, ids, context={}):
            if item.state in ('draft', 'cancel'):
                unlink_ids.append(item.id)
            else:
                raise osv.except_osv(
                    _('Invalid action !'),
                    _('Cannot delete block costing that are already Done!'))
        res = super(tcv_block_cost, self).unlink(cr, uid, ids, context)
        return res

    ##----------------------------------------------------- Workflow

    def button_draft(self, cr, uid, ids, context=None):
        vals = {'state': 'draft'}
        return self.write(cr, uid, ids, vals, context)

    def button_done(self, cr, uid, ids, context=None):
        self.compute_block_cost(cr, uid, ids, context)
        self._update_lot_cost(cr, uid, ids, context)
        self._gen_account_move(cr, uid, ids, context)
        vals = {'state': 'done', 'validator': uid}
        return self.write(cr, uid, ids, vals, context)

    def button_cancel(self, cr, uid, ids, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        obj_move = self.pool.get('account.move')
        obj_lot = self.pool.get('stock.production.lot')
        for item in self.browse(cr, uid, ids, context={}):
            if item.move_id:
                move = obj_move.browse(cr, uid, item.move_id.id, context=None)
                if move.state == 'draft':
                    self.write(cr, uid, item.id, {'move_id': None},
                               context=context)
                    obj_move.unlink(cr, uid, [move.id])
            # Clear actual block cost
            for block in item.lot_ids:
                obj_lot.write(cr, uid, block.prod_lot_id.id,
                              {'property_cost_price': 0}, context=context)

        vals = {'state': 'cancel', 'validator': None}
        return self.write(cr, uid, ids, vals, context)

    def test_draft(self, cr, uid, ids, *args):
        return True

    def test_done(self, cr, uid, ids, *args):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        for item in self.browse(cr, uid, ids, context={}):
            amount = item.transp_amount
            for line in item.lot_ids:
                if not line.block_amount:
                    raise osv.except_osv(
                        _('Error!'),
                        _('Must indicate a cost for block: %s') %
                        (line.prod_lot_id.name))
                amount -= line.transp_unit
        if abs(amount) > 0.0001:
            raise osv.except_osv(
                _('Error!'),
                _('The transport\'s amount dosen\'t corresponds with sum ' +
                  'of the transport lines'))
        return True

    def test_cancel(self, cr, uid, ids, *args):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        for item in self.browse(cr, uid, ids, context={}):
            if item.move_id and item.move_id.id:
                move = self.pool.get('account.move').\
                    browse(cr, uid, item.move_id.id, context=None)
                if move.state == 'posted':
                    raise osv.except_osv(
                        _('Error!'),
                        _('You can not cancel a block costing while the ' +
                          'account move is posted.'))
        return True

tcv_block_cost()


##--------------------------------------------------------- tcv_block_cost_lots


class tcv_block_cost_lots(osv.osv):

    _name = 'tcv.block.cost.lots'

    _description = ''

    ##-----------------------------------------------------

    ##----------------------------------------------------- _internal methods

    def _compute_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for item in self.browse(cr, uid, ids, context=context):
            cost_tot = item.block_amount + item.transp_unit
            res[item.id] = {'cost_total': cost_tot,
                            'cost_unit': round(cost_tot / item.block_size, 2),
                            }
        return res

    ##----------------------------------------------------- function fields

    _columns = {
        'line_id': fields.many2one('tcv.block.cost', 'Cost', required=True,
                                   ondelete='cascade'),
        'prod_lot_id': fields.many2one(
            'stock.production.lot', 'Production lot', required=True,
            domain="[('stock_driver', '=', 'block')]"),
        'product_id': fields.related(
            'prod_lot_id', 'product_id',
            type='many2one', relation='product.product', string='Product',
            store=False, readonly=True),
        'block_size': fields.related(
            'prod_lot_id', 'lot_factor',
            type='float', string='Block size', store=False, readonly=True,
            digits_compute=dp.get_precision('Extra UOM data')),
        'block_invoice_id': fields.many2one(
            'account.invoice', 'Block inv.',
            ondelete='restrict', select=True, required=False),
        'block_amount': fields.float(
            'Block cost', digits_compute=dp.get_precision('Account')),
        'transp_unit': fields.float(
            'Transportation', digits_compute=dp.get_precision('Account')),
        'cost_total': fields.function(
            _compute_all, method=True, type='float', string='Total amount',
            digits_compute=dp.get_precision('Account'), multi='all'),
        'cost_unit': fields.function(
            _compute_all, method=True, type='float', string='Unit cost',
            digits_compute=dp.get_precision('Account'), multi='all'),
        'waybill': fields.char(
            'Waybill', size=32, required=False, readonly=False),
        'group': fields.integer(
            'Group transport', required=True,
            help="Indicate 0 for no group or any nro to indicate " +
            "the \"group\" of blocks transported"),
        'note': fields.char(
            'Notas', size=128, required=False, readonly=False),
        'date_arrival': fields.date(
            'Date arrival', required=True, readonly=True, select=True,
            states={'draft': [('readonly', False)]},
            help="Date of block arrival"),
        'move_ids': fields.related(
            'prod_lot_id', 'move_ids', type='one2many', relation='stock.move',
            string='Moves for this lot', store=False, readonly=True),
        }

    _defaults = {
        'group': 0,
        }

    _sql_constraints = [
        ('block_amount_gt_zero', 'CHECK(block_amount>=0)',
         'The block cost quantity must be >= 0!'),
        ('transp_unit_gt_zero', 'CHECK(transp_unit>=0)',
         'The transportation cost quantity must be >= 0!'),
        ('prod_lot_id_uniq', 'UNIQUE(prod_lot_id)',
         'The block must be unique!'),
        ]

    ##-----------------------------------------------------

    ##----------------------------------------------------- public methods

    ##----------------------------------------------------- buttons (object)

    def button_set_block_cost(self, cr, uid, ids, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        obj_lot = self.pool.get('stock.production.lot')
        for item in self.browse(cr, uid, ids, context={}):
            if item.prod_lot_id and item.block_amount and item.transp_unit:
                obj_lot.write(cr, uid, item.prod_lot_id.id,
                              {'property_cost_price': item.cost_unit},
                              context=context)
        return True

    ##----------------------------------------------------- on_change...

    def on_change_prod_lot_id(self, cr, uid, ids, prod_lot_id):
        res = {}
        if prod_lot_id:
            obj_invl = self.pool.get('account.invoice.line')
            obj_lot = self.pool.get('stock.production.lot')
            lot = obj_lot.browse(cr, uid, prod_lot_id, context=None)
            res = {'value': {'product_id': lot.product_id.id,
                             'block_size': lot.lot_factor,
                             }}
            invl_id = obj_invl.search(cr, uid,
                                      [('prod_lot_id', '=', prod_lot_id)])
            if invl_id and len(invl_id) == 1:
                invl = obj_invl.browse(cr, uid, invl_id[0], context=None)
                res['value'].update({'block_invoice_id': invl.invoice_id.id,
                                     'block_amount': invl.price_subtotal})
        return res

    def on_change_amount(self, cr, uid, ids, block_amount, transp_unit,
                         block_size):
        res = {}
        if block_amount and transp_unit and block_size:
            cost_tot = block_amount + transp_unit
            data = {'cost_total': cost_tot,
                    'cost_unit': round(cost_tot / block_size, 2)}
            res = {'value': data}
        return res

    ##----------------------------------------------------- create write unlink

    ##----------------------------------------------------- Workflow

tcv_block_cost_lots()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
