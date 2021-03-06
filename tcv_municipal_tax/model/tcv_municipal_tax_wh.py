# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2016-11-09
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

##-------------------------------------------------------- tcv_municipal_tax_wh


class tcv_municipal_tax_wh(osv.osv):

    _name = 'tcv.municipal.tax.wh'

    _description = ''

    _order = 'name desc'

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def _get_type(self, cr, uid, context=None):
        context = context or {}
        return context.get('wh_muni_type', 'in_invoice')

    def _get_journal(self, cr, uid, context):
        context = context or {}
        type_inv = context.get('type', 'in_invoice')
        type2journal = {'out_invoice': 'mun_sale',
                        'in_invoice': 'mun_purchase'}
        journal_obj = self.pool.get('account.journal')
        res = journal_obj.search(
            cr, uid,
            [('type', '=', type2journal.get(type_inv, 'mun_purchase'))],
            limit=1)
        if res:
            return res[0]
        else:
            return False

    def _validate_date_ret(self, cr, uid, ids, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        whm = self.browse(cr, uid, ids[0], context=context)
        data = {
            'date': whm.date if whm and whm.date else
            time.strftime('%Y-%m-%d'),
            'date_ret': whm.date_ret if whm and whm.date_ret else
            time.strftime('%Y-%m-%d'),
            }
        if not whm.name:
            last_id = self.search(cr, uid, [('state', '=', 'done'),
                                            ('date', '>', '2016-01-01'),
                                            ('type', 'in', ('in_invoice',
                                                            'in_refund'))],
                                  order="number desc", limit=1)
            last = self.browse(
                cr, uid, last_id, context=context)[0] if last_id else {}
            if last and (last.date_ret > data['date_ret'] or
                         last.date > data['date']):
                raise osv.except_osv(
                    _('Error!'),
                    _('The accounting date must be >= %s and ' +
                      'whithholding date must be >= %s') % (last.date_ret,
                                                            last.date))
        if not whm.period_id:
            obj_per = self.pool.get('account.period')
            data.update({'period_id': obj_per.find(cr, uid, data['date'])[0]})
        self.write(
            cr, uid, ids, data, context=context)
        return False

    def _clear_wh_lines(self, cr, uid, ids, context=None):
        """ Clear lines of current withholding document and delete wh document
        information from the invoice.
        """
        return True

    ##--------------------------------------------------------- function fields

    _columns = {
        'name': fields.char(
            'Number', size=32, readonly=True, help="Withholding number"),
        'type': fields.selection(
            [('out_invoice', 'Customer Invoice'),
             ('in_invoice', 'Supplier Invoice'),
             ], 'Type', readonly=True, help="Withholding type"),
        'state': fields.selection(
            [('draft', 'Draft'),
             ('confirmed', 'Confirmed'),
             ('done', 'Done'),
             ('cancel', 'Cancelled')
             ], 'Estado', readonly=True, help="Estado del Comprobante"),
        'date_ret': fields.date(
            'Withholding date', readonly=True,
            states={'draft': [('readonly', False)]},
            help="Keep empty to use the current date"),
        'date': fields.date(
            'Acc date', readonly=True, states={'draft': [('readonly', False)]},
            help="Accounting date"),
        'period_id': fields.many2one(
            'account.period', 'Force Period', readonly=True,
            states={'draft': [('readonly', False)]},
            help="Keep empty to use the period of the validation " +
            "(Withholding date) date."),
        'partner_id': fields.many2one(
            'res.partner', 'Partner', readonly=True, required=True,
            states={'draft': [('readonly', False)]},
            help="Withholding customer/supplier"),
        'account_id': fields.many2one(
            'account.account', 'Account', required=True, ondelete='restrict',
            readonly=True, states={'draft': [('readonly', False)]}),
        'currency_id': fields.many2one(
            'res.currency', 'Currency', required=True, readonly=True,
            states={'draft': [('readonly', False)]}, help="Currency"),
        'journal_id': fields.many2one(
            'account.journal', 'Journal', required=True, readonly=True,
            states={'draft': [('readonly', False)]}, help="Journal entry"),
        'company_id': fields.many2one(
            'res.company', 'Company', required=True, readonly=True,
            ondelete='restrict'),
        'munici_line_ids': fields.one2many(
            'tcv.municipal.tax.wh.lines', 'line_id',
            'Local withholding lines', readonly=True,
            states={'draft': [('readonly', False)]},
            help="Invoices to will be made local withholdings"),
        'amount_base': fields.float(
            'Amount base', required=False, readonly=True,
            digits_compute=dp.get_precision('Withhold'),
            help="Amount base withheld"),
        'amount_tax': fields.float(
            'Amount tax', required=False, readonly=True,
            digits_compute=dp.get_precision('Withhold'),
            help="Amount tax withheld"),
        }

    _defaults = {
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company').
        _company_default_get(cr, uid, self._name, context=c),
        'currency_id': lambda self, cr, uid, c: self.pool.get('res.users').
        browse(cr, uid, uid, c).company_id.currency_id.id,
        'type': _get_type,
        'state': lambda *a: 'draft',
        'journal_id': _get_journal,
        }

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', 'The Number must be unique!'),
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    def _gen_account_move(self, cr, uid, ids, context=None):
        obj_move = self.pool.get('account.move')
        obj_per = self.pool.get('account.period')
        obj_mtl = self.pool.get('tcv.municipal.tax.wh.lines')
        move_id = None
        types = {'out_invoice': -1, 'in_invoice': 1,
                 'out_refund': 1, 'in_refund': -1}
        for item in self.browse(cr, uid, ids, context={}):
            lines = []
            for line in item.munici_line_ids:  # move line for deposit lines
                move = {
                    'ref': item.name,
                    'journal_id': item.journal_id.id,
                    'date': item.date,
                    'period_id': obj_per.find(cr, uid, item.date)[0],
                    'company_id': item.company_id.id,
                    'state': 'draft',
                    'to_check': False,
                    'narration': _(
                        'Municipal tax withholding: %s') % item.name,
                    }
                direction = types[line.invoice_id.type]
                invoice = line.invoice_id
                journal = item.journal_id
                if invoice.type in ['in_invoice', 'in_refund']:
                    name = 'COMP. RET. MUNI. %s  FCT. %s' % (
                        item.name,
                        invoice.supplier_invoice_number or '')
                else:
                    name = 'COMP. RET. MUNI. %s  FCT. %s' % (
                        item.name,
                        invoice.number or '')
                # Get move account from journal
                acc2 = journal.default_credit_account_id and \
                    journal.default_credit_account_id.id \
                    if direction == 1 else \
                    journal.default_debit_account_id and \
                    journal.default_debit_account_id.id
                if not acc2:
                    raise osv.except_osv(
                        _('Error!'),
                        _('No account selected, please check journal\'s ' +
                          'accounts (%s)') % journal.name)
                lines.append({
                    'name': name,
                    'account_id': acc2,
                    'partner_id': item.partner_id.id,
                    'ref': item.name,
                    'date': item.date,
                    'currency_id': False,
                    'debit': line.amount_ret if direction == -1 else 0,
                    'credit': line.amount_ret if direction != -1 else 0,
                    })
                lines.append({
                    'name': name,
                    'account_id': invoice.account_id.id,
                    'partner_id': item.partner_id.id,
                    'ref': item.name,
                    'date': item.date,
                    'currency_id': False,
                    'debit': line.amount_ret if direction == 1 else 0,
                    'credit': line.amount_ret if direction != 1 else 0,
                    })
                move.update({'line_id': [(0, 0, l) for l in lines]})
                move_id = obj_move.create(cr, uid, move, context)
                if move_id:
                    obj_move.post(cr, uid, [move_id], context=context)
                    obj_mtl.write(
                        cr, uid, [line.id], {'move_id': move_id},
                        context=context)
                    self.do_reconcile(cr, uid, line, move_id, context)
        return move_id

    def do_reconcile(self, cr, uid, mwl, move_id, context):
        obj_move = self.pool.get('account.move')
        obj_aml = self.pool.get('account.move.line')
        move = obj_move.browse(cr, uid, move_id, context)
        rec_ids = []
        # Get "payable" move line from invoice
        account_id = mwl.invoice_id.account_id.id
        # Add invoice's move payable line
        rec_amount = 0
        for line in mwl.invoice_id.move_id.line_id:
            if line.account_id.id == account_id:
                rec_ids.append(line.id)
                if line.reconcile_partial_id:
                    for m in line.reconcile_partial_id.line_partial_ids:
                        rec_amount += m.debit or 0.0 - m.credit or 0.0
                    rp_id = line.reconcile_partial_id.id
                    rec_ids.extend(obj_aml.search(cr, uid, [
                        ('reconcile_partial_id', '=', rp_id),
                        ('id', '!=', line.id)]))
        # Add new move pay line
        for line in move.line_id:
            if line.account_id.id == account_id:
                rec_ids.append(line.id)
        if rec_ids:
            # reconcile if wh muni = balance else reconcile_partial
            if abs(mwl.amount_ret + rec_amount) < 0.001:
                obj_aml.reconcile(cr, uid, rec_ids, context=context)
            else:
                obj_aml.reconcile_partial(cr, uid, rec_ids, context=context)
        return True

    ##-------------------------------------------------------- buttons (object)

    def compute_amount_wh(self, cr, uid, ids, context=None):
        """ Calculate withholding amount each line
        """
        if context is None:
            context = {}
        mtwl_obj = self.pool.get('tcv.municipal.tax.wh.lines')
        for retention in self.browse(cr, uid, ids, context):
            data = {'amount_base': 0, 'amount_tax': 0}
            for line in retention.munici_line_ids:
                value = mtwl_obj.on_change_invoice_id(
                    cr, uid, [line.id],
                    line.invoice_id and line.invoice_id.id or 0,
                    line.muni_tax_id and line.muni_tax_id.id or 0,
                    line.amount_untaxed
                    ).get('value', {})
                if value:
                    mtwl_obj.write(
                        cr, uid, line.id, value, context=context)
                    data['amount_base'] += value.get('amount_untaxed', 0)
                    data['amount_tax'] += value.get('amount_ret', 0)
            self.write(cr, uid, [retention.id], data, context=context)
        return True

    ##------------------------------------------------------------ on_change...

    def onchange_partner_id(self, cr, uid, ids, type, partner_id):
        res = {}
        if not partner_id:
            return res
        obj_pnr = self.pool.get('res.partner')
        partner = obj_pnr.browse(cr, uid, partner_id, context=None)
        account_id = partner.property_account_payable and \
            partner.property_account_payable.id if type == 'in_invoice' \
            else partner.property_account_receivable and \
            partner.property_account_receivable.id
        res.update({'account_id': account_id or 0})
        return {'value': res}

    def on_change_date(self, cr, uid, ids, date, date_ret):
        res = {}
        if date and not date_ret:
            res.update({'date_ret': date})
        return {'value': res}

    ##----------------------------------------------------- create write unlink

    def unlink(self, cr, uid, ids, context=None):
        unlink_ids = []
        for wh_doc in self.browse(cr, uid, ids, context=context):
            if wh_doc.state != 'cancel':
                raise osv.except_osv(
                    _("Invalid Procedure!!"),
                    _("The withholding document needs to be in cancel " +
                      "state to be deleted."))
            else:
                unlink_ids.append(wh_doc.id)
        if unlink_ids:
            self._clear_wh_lines(cr, uid, unlink_ids, context)
            return super(tcv_municipal_tax_wh, self).unlink(
                cr, uid, unlink_ids, context)

    ##---------------------------------------------------------------- Workflow

    def button_draft(self, cr, uid, ids, context=None):
        vals = {'state': 'draft'}
        return self.write(cr, uid, ids, vals, context)

    def button_confirmed(self, cr, uid, ids, context=None):
        self.compute_amount_wh(cr, uid, ids, context=None)
        vals = {'state': 'confirmed'}
        return self.write(cr, uid, ids, vals, context)

    def button_done(self, cr, uid, ids, context=None):
        for item in self.browse(cr, uid, ids, context={}):
            if not item.name:
                number = self.pool.get('ir.sequence').get(
                    cr, uid, 'tcv.municipal.tax.wh.%s' % item.type)
                if item.date_ret:
                    date = time.strptime(item.date_ret, '%Y-%m-%d')
                    name = 'DHMAP-%04d%02d%s' % (date.tm_year,
                                                 date.tm_mon,
                                                 number)
                cr.execute('UPDATE tcv_municipal_tax_wh SET ' +
                           'name=%(name)s ' +
                           'WHERE id=%(id)s', {'name': name, 'id': item.id})
            self._gen_account_move(
                cr, uid, [item.id], context=context)
        vals = {'state': 'done'}
        return self.write(cr, uid, ids, vals, context)

    def button_cancel(self, cr, uid, ids, context=None):
        unlink_move_ids = []
        obj_move = self.pool.get('account.move')
        obj_mwl = self.pool.get('tcv.municipal.tax.wh.lines')
        for item in self.browse(cr, uid, ids, context={}):
            for line in item.munici_line_ids:
                if line.move_id and line.move_id.state != 'posted':
                    unlink_move_ids.append(line.move_id.id)
                    obj_mwl.write(
                        cr, uid, [line.id], {'move_id': 0},
                        context=context)
        obj_move.unlink(cr, uid, unlink_move_ids, context=context)
        vals = {'state': 'cancel'}
        return self.write(cr, uid, ids, vals, context)

    def test_draft(self, cr, uid, ids, *args):
        return True

    def test_confirmed(self, cr, uid, ids, *args):
        return True

    def test_done(self, cr, uid, ids, *args):
        self._validate_date_ret(cr, uid, ids, context=None)
        return True

    def test_cancel(self, cr, uid, ids, *args):
        for item in self.browse(cr, uid, ids, context={}):
            for line in item.munici_line_ids:
                if line.move_id and line.move_id.state == 'posted':
                    raise osv.except_osv(
                        _('Error!'),
                        _('You can not cancel a deposit while the account ' +
                          'move is posted.'))
        return True

tcv_municipal_tax_wh()


##-------------------------------------------------- tcv_municipal_tax_wh_lines


class tcv_municipal_tax_wh_lines(osv.osv):

    _name = 'tcv.municipal.tax.wh.lines'

    _description = ''

    ##-------------------------------------------------------------------------

    def default_get(self, cr, uid, fields, context=None):
        context = context or {}
        data = super(tcv_municipal_tax_wh_lines, self).default_get(
            cr, uid, fields, context)
        if context.get('lines'):
            for line_record in context['lines']:
                if not isinstance(line_record, (tuple, list)):
                    line_record_detail = self.browse(
                        cr, uid, line_record, context=context)
                else:
                    line_record_detail = line_record[2]
                if line_record_detail:
                    data.update(
                        {'muni_tax_id': line_record_detail['muni_tax_id']})
        return data

    ##------------------------------------------------------- _internal methods

    def _get_invoice(self, cr, uid, invoice_id, context=None):
        res = {}
        if not invoice_id:
            return res
        obj_inv = self.pool.get('account.invoice')
        invoice = obj_inv.browse(cr, uid, invoice_id, context=context)
        res.update({
            'number': invoice.number,
            'inv_name': invoice.name,
            'supplier_invoice_number': invoice.supplier_invoice_number,
            'nro_ctrl': invoice.nro_ctrl,
            'date_invoice': invoice.date_invoice,
            'date_document': invoice.date_document,
            'amount_total': invoice.amount_total,
            'amount_untaxed': invoice.amount_untaxed,
            'residual': invoice.residual,
            })
        return res

    def _get_muni_tax(self, cr, uid, muni_tax_id, amount_untaxed, residual,
                      context=None):
        res = {}
        if not muni_tax_id:
            return res
        obj_mtx = self.pool.get('tcv.municipal.taxes.config')
        muni_tax = obj_mtx.browse(cr, uid, muni_tax_id, context=context)
        wh_rate = muni_tax and muni_tax.wh_rate or 0
        amount_ret = round((amount_untaxed * wh_rate) / 100, 2)
        res.update({
            'amount_untaxed': amount_untaxed,
            'wh_rate': wh_rate,
            'amount_ret': amount_ret,
            'amount_pay': residual - amount_ret,
            })
        return res

    ##--------------------------------------------------------- function fields

    _columns = {
        'line_id': fields.many2one(
            'tcv.municipal.tax.wh', 'String', required=True,
            ondelete='cascade'),
        'invoice_id': fields.many2one(
            'account.invoice', 'Invoice Reference', ondelete='restrict',
            select=True, domain=[('state', 'in', ('open', 'paid'))]),
        'inv_name': fields.related(
            'invoice_id', 'name', type='char',
            string='Description', size=64, store=False,
            readonly=True),
        'number': fields.related(
            'invoice_id', 'number', type='char',
            string='Number', size=64, store=False,
            readonly=True),
        'supplier_invoice_number': fields.related(
            'invoice_id', 'supplier_invoice_number', type='char',
            string='Supplier Invoice Number', size=64, store=False,
            readonly=True),
        'nro_ctrl': fields.related(
            'invoice_id', 'nro_ctrl', type='char',
            string='Control Number', size=64, store=False,
            readonly=True),
        'date_invoice': fields.related(
            'invoice_id', 'date_invoice', type='date', string='Invoice Date',
            store=False, readonly=True),
        'date_document': fields.related(
            'invoice_id', 'date_document', type='date',
            string='Document\'s Date', store=False, readonly=True),
        'amount_total': fields.float(
            'Total', required=False, readonly=True,
            digits_compute=dp.get_precision('Withhold'),
            help="Amount total withheld"),
        'muni_tax_id': fields.many2one(
            'tcv.municipal.taxes.config', 'Municipal tax',
            ondelete='restrict', required=True),
        'amount_untaxed': fields.float(
            'Untaxed', required=False, readonly=False,
            digits_compute=dp.get_precision('Withhold'),
            help="Amount base for withholding"),
        'wh_rate': fields.float(
            'Wh rate', digits_compute=dp.get_precision('Account'),
            readonly=True, required=True,
            help="Tax rate for supplier withholding"),
        'amount_pay': fields.float(
            'Payed', required=False, readonly=True,
            digits_compute=dp.get_precision('Withhold')),
        'amount_ret': fields.float(
            'Withhold', required=False, readonly=True,
            digits_compute=dp.get_precision('Withhold')),
        'residual': fields.float(
            'Residual', required=False, readonly=True,
            digits_compute=dp.get_precision('Withhold')),
        'move_id': fields.many2one(
            'account.move', 'Accounting entries', ondelete='restrict',
            help="The move of this entry line.", select=True, readonly=True),
        }

    _defaults = {
        }

    _sql_constraints = [
        ('invoice_uniq', 'UNIQUE(invoice_id)', 'The invoice must be unique!'),
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    def on_change_invoice_id(self, cr, uid, ids, invoice_id,
                             muni_tax_id, amount_untaxed):
        res = {}
        if invoice_id:
            res.update(self._get_invoice(cr, uid, invoice_id, context=None))
            if muni_tax_id:
                res.update(self._get_muni_tax(
                    cr, uid, muni_tax_id,
                    amount_untaxed or res['amount_untaxed'],
                    res['residual'], context=None))
        return {'value': res}

    def on_change_muni_tax_id(self, cr, uid, ids,
                              muni_tax_id, amount_untaxed, residual):
        res = {}
        if muni_tax_id:
            res.update(self._get_muni_tax(
                cr, uid, muni_tax_id, amount_untaxed, residual, context=None))
        return {'value': res}

    ##----------------------------------------------------- create write unlink

    def create(self, cr, uid, vals, context=None):
        #autoref
        amount_untaxed = vals.get('amount_untaxed', 0)
        if vals.get('invoice_id'):
            vals.update(
                self._get_invoice(cr, uid, vals['invoice_id'], context))
            if amount_untaxed:
                vals.update({'amount_untaxed': amount_untaxed})
        if vals.get('muni_tax_id') and vals.get('amount_untaxed'):
            vals.update(
                self._get_muni_tax(
                    cr, uid, vals['muni_tax_id'],
                    vals['amount_untaxed'],
                    vals['residual'], context))
        res = super(tcv_municipal_tax_wh_lines, self).create(
            cr, uid, vals, context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        amount_untaxed = vals.get('amount_untaxed', 0)
        if vals.get('invoice_id'):
            vals.update(
                self._get_invoice(cr, uid, vals['invoice_id'], context))
            if amount_untaxed:
                vals.update({'amount_untaxed': amount_untaxed})
        if vals.get('muni_tax_id') and vals.get('amount_untaxed'):
            vals.update(
                self._get_muni_tax(
                    cr, uid, vals['muni_tax_id'],
                    vals['amount_untaxed'],
                    vals['residual'], context))
        res = super(tcv_municipal_tax_wh_lines, self).write(
            cr, uid, ids, vals, context)
        return res

    ##---------------------------------------------------------------- Workflow

tcv_municipal_tax_wh_lines()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
