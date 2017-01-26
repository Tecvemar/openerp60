# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date: 13/09/2012
#    Version: 0.0.0.0
#
#    Description:
#
#
##############################################################################
from datetime import datetime
from osv import fields, osv
from tools.translate import _
#~ import pooler
import decimal_precision as dp
import time
#~ import netsvc


##------------------------------------------------------------------ class_name


class tcv_import_management(osv.osv):

    _name = 'tcv.import.management'

    _description = 'Handles data related to importing goods'

    ##-------------------------------------------------------------------------

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        res = []
        for record in self.browse(cr, uid, ids, context={}):
            if record.name:
                name = '%s, Exp: %s (%s)' % (record.ref, record.name,
                                             record.status)
            else:
                name = '%s (%s)' % (record.ref, record.status)
            res.append((record.id, name))
        return res

    ##--------------------------------------------------------- function fields

    def _calc_days(self, shipment_date, arrival_date, reception_date):
        days_ship = 0
        days_custom = 0
        if shipment_date and arrival_date:
            d1 = datetime.strptime(shipment_date, '%Y-%m-%d')
            d2 = datetime.strptime(arrival_date, '%Y-%m-%d')
            days_ship = abs((d2 - d1).days)
            if reception_date:
                d3 = datetime.strptime(reception_date, '%Y-%m-%d')
                days_custom = abs((d3 - d2).days)
        days_total = days_ship + days_custom
        res = {
            'days_ship': days_ship,
            'days_custom': days_custom,
            'days_total': days_total
            }
        return res

    def _days_all(self, cr, uid, ids, name, args, context=None):
        res = {}
        for imp in self.browse(cr, uid, ids, context=context):
            res[imp.id] = self._calc_days(imp.shipment_date,
                                          imp.arrival_date,
                                          imp.reception_date)
        return res

    def _cost_applied(self, cr, uid, ids, name, args, context=None):
        res = {}
        for imp in self.browse(cr, uid, ids, context=context):
            res[imp.id] = bool(imp.invoice_ids)
            for inv in imp.invoice_ids:
                res[imp.id] = res[imp.id] and inv.cost_applied
        return res

    def _container_qty(self, cr, uid, ids, name, args, context=None):
        res = {}
        for imp in self.browse(cr, uid, ids, context=context):
            res[imp.id] = len(imp.container_ids)
        return res

    def _compute_forms_ids(self, cr, uid, ids, name, args, context=None):
        result = {}
        for item in self.browse(cr, uid, ids, context=context):
            dua_ids = []
            tax_ids = []
            for invoice in item.invoice_ids:
                if invoice.dua_form_id:
                    dua_ids.append(invoice.dua_form_id.id)
                    if invoice.dua_form_id.customs_form_ids:
                        tax_ids.extend([x.id for x in
                                        invoice.dua_form_id.customs_form_ids])
            #~ Remove duplicated keys from dua_ids & tax_ids
            result[item.id] = {'dua_ids': list(set(dua_ids)),
                               'tax_ids': list(set(tax_ids))}
        return result

    ##-------------------------------------------------------------------------

    _status = [
        ('sale_order', 'Sale order'),
        ('proforma', 'Proforma'),
        ('invoiced', 'Invoiced'),
        ('production', 'Production'),
        ('shipment_port', 'Shipment port'),
        ('navigating', 'Navigating'),
        ('arrival_port', 'Arrival port'),
        ('customs', 'Customs'),
        ('partial_arrived', 'Partially arrived'),
        ('arrived', 'Arrived'),
        ]

    _order = 'ref desc'

    _columns = {
        'ref': fields.char(
            'Reference', size=24, required=True, select=True, readonly=True),
        'name': fields.char(
            'Expedient #', size=24, required=False, select=True,
            readonly=True, states={'open': [('readonly', False)]}),
        'open_date': fields.date(
            'Open Date', readonly=True),
        'close_date': fields.date(
            'Close Date', readonly=True),
        'broker_id': fields.many2one(
            'res.partner', 'Broker', change_default=True, readonly=True,
            required=True, states={'open': [('readonly', False)]},
            ondelete='restrict'),
        'partner_id': fields.many2one(
            'res.partner', 'Partner', change_default=True, readonly=True,
            required=True, states={'open': [('readonly', False)]},
            ondelete='restrict'),
        'folder': fields.char(
            'Folder', size=24, readonly=True,
            states={'open': [('readonly', False)]}),
        'description': fields.char(
            'Description', size=64, required=False, readonly=True,
            states={'open': [('readonly', False)]}),
        'currency_id': fields.many2one(
            'res.currency', 'Currency', required=True, readonly=True,
            states={'open': [('readonly', False)]}),
        'company_id': fields.many2one(
            'res.company', 'Company', required=True, select=True,
            readonly=True, states={'open': [('readonly', False)]}),
        'invoice_ids': fields.one2many(
            'account.invoice', 'import_id', 'Related invoices', readonly=True),
        'purchase_ids': fields.one2many(
            'purchase.order', 'import_id', 'Related p/o', readonly=True),
        'advance_ids': fields.many2many(
            'account.voucher', 'tim_advance_rel', 'tim_id',
            'advance_id', 'Advance', readonly=True,
            domain=[('voucher_type', '=', 'advance')],
            states={'open': [('readonly', False)]}),
        'notes_ids': fields.one2many(
            'tcv.import.notes', 'import_id', 'Notes', readonly=True,
            states={'open': [('readonly', False)]}),
        'state': fields.selection(
            [('open', 'Open'), ('done', 'Done'), ('cancel', 'Cancelled')],
            string='State', required=True, readonly=True),
        'account_date': fields.date(
            'Account date', readonly=True,
            states={'open': [('readonly', False)]}, select=True,
            help="Date of nacionalization"),
        'shipment_date': fields.date(
            'Shipment date', readonly=True,
            states={'open': [('readonly', False)]}, select=True),
        'shipment_port': fields.char(
            'Shipment port', size=24, readonly=True,
            states={'open': [('readonly', False)]}),
        'ship_name': fields.char(
            'Ship name', size=24, readonly=True,
            states={'open': [('readonly', False)]}),
        'arrival_date': fields.date(
            'Arrival date', readonly=True,
            states={'open': [('readonly', False)]}, select=True),
        'arrival_port': fields.char(
            'Arrival port', size=24, readonly=True,
            states={'open': [('readonly', False)]}),
        'reception_date': fields.date(
            'Reception date', readonly=True,
            states={'open': [('readonly', False)]}, select=True,
            help="Date of receipt of the goods (in the company)"),
        'bl': fields.char(
            'B.L. #', size=24, readonly=True,
            states={'open': [('readonly', False)]}),
        'status': fields.selection(
            _status, string='Status', required=True, readonly=True,
            states={'open': [('readonly', False)]}, select=True),
        'broker_date': fields.date(
            'Delivery date ', readonly=True,
            states={'open': [('readonly', False)]}, select=True,
            help="Delivery date of the file to the broker"),
        'container_qty': fields.function(
            _container_qty, method=True, type='integer',
            string='Containers (Qty)', store=False),
        'container_ids': fields.one2many(
            'tcv.import.container', 'import_id', 'Container', readonly=True,
            states={'open': [('readonly', False)]}),
        'incoterm_id': fields.many2one(
            'stock.incoterms', 'Incoterms', readonly=True, required=False,
            states={'open': [('readonly', False)]}, ondelete='restrict'),
        'days_ship': fields.function(
            _days_all, method=True, type='integer', string='Days at ship',
            store=False, multi='all'),
        'days_custom': fields.function(
            _days_all, method=True, type='integer', string='Days at custom',
            store=False, multi='all'),
        'days_total': fields.function(
            _days_all, method=True, type='integer', string='Total days',
            store=False, multi='all'),
        'cost_applied': fields.function(
            _cost_applied, method=True, type='boolean', string='Cost applied',
            store=False),
        'total_amount_currency': fields.float(
            'Total amount', digits_compute=dp.get_precision('Account'),
            readonly=True),
        'total_products_currency': fields.float(
            'Total products', digits_compute=dp.get_precision('Account'),
            readonly=True),
        'total_charges_currency': fields.float(
            'Total charges', digits_compute=dp.get_precision('Account'),
            readonly=True),
        'line_ids': fields.one2many(
            'tcv.import.management.lines', 'import_id', 'Cost distribution',
            readonly=False),
        'move_id': fields.many2one(
            'account.move', 'Account move', ondelete='restrict',
            help="The move of this entry line.", select=True, readonly=True),
        'dua_ids': fields.function(
            _compute_forms_ids, method=True, relation='dua.form',
            type="one2many", string='DUA forms', multi=True),
        'tax_ids': fields.function(
            _compute_forms_ids, method=True, relation='customs.form',
            type="one2many", string='Taxes forms', multi=True),
        }

    _defaults = {
        'ref': lambda *a: '/',
        'name': lambda *a: '',
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company').
        _company_default_get(cr, uid, self._name, context=c),
        'state': lambda *a: 'open',
        'status': lambda *a: 'sale_order',
        }

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Expedient # must be unique!'),
        ('ref_uniq', 'unique(ref)', 'Expedient # must be unique!'),
        ('check_arrival', 'check(shipment_date<=arrival_date)',
         'The arrival date must be greater than the shipment date!'),
        ('check_reception', 'check(arrival_date<=reception_date)',
         'The reception date must be greater than the arrival date!'),
        ]

    ##-------------------------------------------------------------------------

    def get_import_config(self, cr, uid):
        obj_cfg = self.pool.get('tcv.import.config')
        company_id = self.pool.get('res.users').\
            browse(cr, uid, uid, context={}).company_id.id
        cfg_id = obj_cfg.search(cr, uid, [('company_id', '=', company_id)])
        if cfg_id:
            imp_cfg = obj_cfg.browse(cr, uid, cfg_id[0], context={})
        else:
            raise osv.except_osv(
                _('Error!'), _('Please set a valid import configuration'))
        return imp_cfg

    def cost_distribution_wizard(self, cr, uid, ids, context):
        if not ids:
            return []
        return {
            'name': 'Cost distribution wizard',
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'tcv.import.cost.wizard',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': {'default_import_id': ids[0]},
            }

    def _gen_account_move_line(self, company_id, account_id, name,
                               debit, credit):
        return (0, 0, {
                'auto': True,
                'company_id': company_id,
                'account_id': account_id,
                'name': name[:64],
                'debit': debit,
                'credit': credit,
                'reconcile': False,
                })

    def create_account_move_lines(self, cr, uid, imp, context=None):
        lines = []
        company_id = context.get('task_company_id')
        imp_cfg = context.get('import_config')
        total_amount = 0.0
        for line in imp.line_ids:
            account_id = line.product_id.property_stock_account_output.id or \
                line.product_id.categ_id.property_stock_account_output_categ.id
            if not account_id:
                raise osv.except_osv(
                    _('Error!'),
                    _('No product account found, please check product and ' +
                      'category account settings (%s)') % line.product_id.name)
            total_amount += line.applied_cost
            lines.append(self._gen_account_move_line(
                company_id,
                account_id,
                _('Applied cost: %s') % (line.product_id.name),
                line.applied_cost,
                0.0))
        if total_amount and imp_cfg:
            account_id = imp_cfg.account_id.id
            lines.append(self._gen_account_move_line(
                company_id,
                account_id,
                _('Import expenses applied: %s') % (imp.ref),
                0.0,
                total_amount))
        return lines

    def create_account_move(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        obj_move = self.pool.get('account.move')
        obj_cfg = self.pool.get('tcv.import.config')
        company_id = self.pool.get('res.users').\
            browse(cr, uid, uid, context=context).company_id.id
        cfg_id = obj_cfg.search(cr, uid, [('company_id', '=', company_id)])
        if cfg_id:
            imp_cfg = obj_cfg.browse(cr, uid, cfg_id[0], context=context)
        else:
            raise osv.except_osv(
                _('Error!'),
                _('Please set a valid configuration '))
        date = time.strftime('%Y-%m-%d')
        context.update({'import_company_id': company_id,
                        'import_config': imp_cfg,
                        'import_date': date,
                        })
        so_brw = self.browse(cr, uid, ids, context={})
        move_ids = []
        for imp in so_brw:
            move = {
                'ref': imp.ref,
                'journal_id': imp_cfg.journal_id.id,
                'date': date,
                'company_id': company_id,
                'state': 'draft',
                'to_check': False,
                'narration': _('Import management (%s):\n\tBroker: %s\n\t' +
                               'Supplier: %s\n\tB.L.: %s') % (
                    imp.ref, imp.broker_id.name, imp.partner_id.name,
                    imp.bl or 'N/A'),
                }
            lines = self.create_account_move_lines(cr, uid, imp, context)
            if lines:
                move.update({'line_id': lines})
                move_id = obj_move.create(cr, uid, move, context)
                obj_move.post(cr, uid, [move_id], context=context)
                if move_id:
                    move_ids.append(move_id)
                    self.write(cr, uid, imp.id, {'move_id': move_id}, context)
        return move_ids
        return True

    ##------------------------------------------------------------ on_change...

    def on_change_days(self, cr, uid, ids, shipment_date,
                       arrival_date, reception_date):
        res = self._calc_days(shipment_date, arrival_date, reception_date)
        return {'value': res}

    ##----------------------------------------------------- create write unlink

    def create(self, cr, uid, vals, context=None):
        if vals.get('ref', '/') == '/':
            vals.update({'ref': self.pool.get('ir.sequence').
                         get(cr, uid, 'tcv.import.management')})
        if not vals.get('open_date'):
            vals.update({'open_date': time.strftime('%Y-%m-%d')})
        res = super(tcv_import_management, self).create(cr, uid, vals, context)
        return res

    ##---------------------------------------------------------------- Workflow

    def button_open(self, cr, uid, ids, context=None):
        vals = {'state': 'open'}
        return self.write(cr, uid, ids, vals, context)

    def button_done(self, cr, uid, ids, context=None):
        self.create_account_move(cr, uid, ids, context)
        vals = {'state': 'done', 'close_date': time.strftime('%Y-%m-%d')}
        return self.write(cr, uid, ids, vals, context)

    def button_cancel(self, cr, uid, ids, context=None):
        imp = self.browse(cr, uid, ids[0], context=context)
        imp_move_id = imp.move_id.id if imp and imp.move_id else False
        vals = {'state': 'cancel', 'move_id': 0}
        res = self.write(cr, uid, ids, vals, context)
        if imp_move_id:
            self.pool.get('account.move').unlink(
                cr, uid, [imp_move_id], context)
        return res

    def test_open(self, cr, uid, ids, *args):
        return True

    def test_done(self, cr, uid, ids, *args):
        for imp in self.browse(cr, uid, ids, context={}):
            if imp.status != 'arrived':
                raise osv.except_osv(
                    _('Warning!'),
                    _('You can\'t validate a Import while status <> "Arrived"')
                    )
            if not imp.shipment_date or not imp.arrival_date or \
                    not imp.reception_date:
                raise osv.except_osv(
                    _('Warning!'),
                    _('You must indicate a shipment, arrival and reception ' +
                      'dates'))
            for i in imp.invoice_ids:
                if i.state not in ('open', 'paid'):
                    raise osv.except_osv(
                        _('Warning!'),
                        _('You can\'t validate a Import while invoice\'s' +
                          'state not in Open or Paid (%s %s)') % (
                            i.supplier_invoice_number, i.partner_id.name)
                        )
            for t in imp.tax_ids:
                if t.state != 'done':
                    raise osv.except_osv(
                        _('Warning!'),
                        _('You can\'t validate a Import while Tax form\'s' +
                          'state <> "Done" (%s)') % t.name
                        )

        return True

    def test_cancel(self, cr, uid, ids, *args):
        if len(ids) != 1:
            raise osv.except_osv(
                _('Error!'),
                _('Multiple operations not allowed'))
        for imp in self.browse(cr, uid, ids, context=None):
            if imp.move_id and imp.move_id.state != 'draft':
                raise osv.except_osv(
                    _('Error!'),
                    _('Can\'t cancel a import while account move state ' +
                      '<> "Draft"'))
        return True

tcv_import_management()


##------------------------------------------------------------ tcv_import_notes


class tcv_import_notes(osv.osv):

    _name = 'tcv.import.notes'

    _description = 'Notes for imports in log format'

    ##-------------------------------------------------------------------------

    ##--------------------------------------------------------- function fields

    _order = 'date'

    _columns = {
        'import_id': fields.many2one(
            'tcv.import.management', 'Notes', required=True,
            ondelete='cascade'),
        'date': fields.datetime(
            'Date', required=True, select=True),
        'name': fields.char(
            'Note', size=64, required=True),
        'locked': fields.boolean(
            'locked', readonly=True),
        'user_id': fields.many2one(
            'res.users', 'User', readonly=True, select=True,
            ondelete='restrict'),
        }

    _defaults = {
        'date': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
        'locked': lambda *a: False,
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    def can_write_unlink(self, cr, uid, ids, context=None):
        for item in self.browse(cr, uid, ids, context=context):
            if not context.get('unlock_cost_distribution_data') and \
                    item.locked:
                return False
        return True

    def create(self, cr, uid, vals, context=None):
        if not vals.get('user_id'):
            vals.update({'user_id': uid})
        res = super(tcv_import_notes, self).create(cr, uid, vals, context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        res = False
        if self.can_write_unlink(cr, uid, ids, context):
            res = super(tcv_import_notes, self).write(
                cr, uid, ids, vals, context)
        return res

    def unlink(self, cr, uid, ids, context=None):
        res = False
        if self.can_write_unlink(cr, uid, ids, context):
            res = super(tcv_import_notes, self).unlink(cr, uid, ids, context)
        return res

    ##---------------------------------------------------------------- Workflow

tcv_import_notes()


##------------------------------------------------------- tcv_import_containers

class tcv_import_container(osv.osv):

    _name = 'tcv.import.container'

    _description = ''

    ##-------------------------------------------------------------------------

    ##--------------------------------------------------------- function fields

    _columns = {
        'import_id': fields.many2one(
            'tcv.import.management', 'Containers', required=True,
            ondelete='cascade'),
        'name': fields.char(
            'Name', size=32),
        'consolidated': fields.boolean(
            'Consolidated'),
        'arrived': fields.boolean(
            'Arrived'),
        }

    _defaults = {
        'consolidated': lambda *a: False,
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_import_container()


##------------------------------------------------- tcv_import_management_lines

class tcv_import_management_lines(osv.osv):

    _name = 'tcv.import.management.lines'

    _description = ''

    ##-------------------------------------------------------------------------

    ##--------------------------------------------------------- function fields

    _columns = {
        'import_id': fields.many2one(
            'tcv.import.management', 'Import document', required=True,
            ondelete='cascade'),
        'invoice_id': fields.many2one(
            'account.invoice', 'Invoice', ondelete='restrict', select=True,
            readonly=True),
        'name': fields.related(
            'invoice_id', 'reference', type='char', string='Invoice ref',
            size=32, store=False, readonly=True),
        'date': fields.date(
            'Date', readonly=True),
        'product_id': fields.many2one(
            'product.product', 'Product', readonly=True),
        'product_qty': fields.float(
            'Quantity', digits_compute=dp.get_precision('Product UoM'),
            readonly=True),
        'price_unit': fields.float(
            'Unit price', digits_compute=dp.get_precision('Account'),
            readonly=True),
        'total_amount': fields.float(
            'Total amount', digits_compute=dp.get_precision('Account'),
            readonly=True),
        'direct_cost': fields.float(
            'Direct cost', digits_compute=dp.get_precision('Account'),
            readonly=True),
        'cost_pct': fields.float(
            '% of cost', digits_compute=dp.get_precision('Account'),
            readonly=True),
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
            'Unit cost', digits_compute=dp.get_precision('Account'),
            readonly=True),
        }

    _defaults = {
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_import_management_lines()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
