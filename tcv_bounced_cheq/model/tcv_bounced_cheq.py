# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Gabriel Gamez
#    Creation Date: Gabriel Damez
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
import netsvc


class tcv_bounced_cheq(osv.osv):

    _name = 'tcv.bounced.cheq'

    _description = 'Modulo de cheque devuelto'

    STATE_SELECTION = [
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('paid', 'Paid'),
        ('cancel', 'Canceled'),
        ]

    def send_workflow_signal(self, cr, uid, ids, signal):
        wf_service = netsvc.LocalService("workflow")
        wf_service.trg_validate(uid, self._name, ids, signal, cr)

    def _amount_residual(self, cr, uid, ids, name, args, context=None):
        """
        revisar si no tiene nada que ver con la conciliacion
        """
        result = {}
        obj_bou = self.pool.get('tcv.bounced.cheq')
        for bounced in obj_bou.browse(cr, uid, ids, context=context):
            result[bounced.id] = bounced.amount
            if bounced.payment_ids:
                for p in bounced.payment_ids:
                    result[bounced.id] -= (p.credit - p.debit)
            if bounced.state == 'open' and abs(result[bounced.id]) <= 0.0001:
                obj_bou.send_workflow_signal(
                    cr, uid, bounced.id, 'button_paid')
            elif bounced.state == 'paid' and abs(result[bounced.id]) > 0.0001:
                obj_bou.send_workflow_signal(
                    cr, uid, bounced.id, 'button_reopen')
        return result

    def _get_bounced_from_line(self, cr, uid, ids, context=None):
        """
        Get a ids of account.move.line and return a list of
        tcv_bounced_cheq.ids - need to be recalculated
        """
        obj_bou = self.pool.get('tcv.bounced.cheq')
        bou_ids = obj_bou.search(cr, uid, [])
        res = []
        for item in obj_bou.browse(cr, uid, bou_ids, context={}):
            pay_ids = [x.id for x in item.payment_ids]
            if set(pay_ids) & set(ids):
                res.append(item.id)
        return res

    def _get_bounced_from_reconcile(self, cr, uid, ids, context=None):
        """
        Get a ids of account.move.reconcile and return a
        list of tcv_bounced_cheq.ids - need to be recalculated
        """
        obj_bou = self.pool.get('tcv.bounced.cheq')
        bou_ids = obj_bou.search(cr, uid, [])
        res = []
        aml_ids = []
        obj_rec = self.pool.get('account.move.reconcile')
        for rec_brw in obj_rec.browse(cr, uid, ids, context=context):
            aml_ids += [y.id for y in rec_brw.line_id]
            aml_ids += [z.id for z in rec_brw.line_partial_ids]
        for item in obj_bou.browse(cr, uid, bou_ids, context={}):
            pay_ids = [x.id for x in item.payment_ids
                       if x.reconcile_id or x.reconcile_partial_id]
            if set(pay_ids) & set(aml_ids):
                res.append(item.id)
        return res

    def _get_use_fee_from_motive(self, cr, uid, ids, context=None):
        '''
        Returns a list of tcv.bounced.cheq ids that need to
        recalculate the value of the field: button_fee
        '''
        bounced_ids = self.pool.get('tcv.bounced.cheq').search(
            cr, uid, [('motive_id', 'in', ids)], context=context)
        return bounced_ids

    def _get_use_fee_from_config(self, cr, uid, ids, context=None):
        bounced_ids = self.pool.get('tcv.bounced.cheq').search(
            cr, uid, [('id', '!=', 0)], context=context)
        return bounced_ids

    def _get_use_fee_from_invoice(self, cr, uid, ids, context=None):
        bounced_ids = self.pool.get('tcv.bounced.cheq').search(
            cr, uid, [('fee_document_id', 'in', ids)], context=context)
        return bounced_ids

    def _compute_lines(self, cr, uid, ids, name, args, context=None):
        result = {}
        for bounced in self.browse(cr, uid, ids, context=context):
            src = []
            lines = []
            if bounced.move_id:
                for m in bounced.move_id.line_id:
                    temp_lines = []
                    if m.reconcile_id:
                        temp_lines = map(
                            lambda x: x.id, m.reconcile_id.line_id)
                    elif m.reconcile_partial_id:
                        temp_lines = map(
                            lambda x: x.id,
                            m.reconcile_partial_id.line_partial_ids)
                    lines += [x for x in temp_lines if x not in lines]
                    src.append(m.id)

            lines = filter(lambda x: x not in src, lines)
            result[bounced.id] = lines
        return result

    def _get_fee_data(self, cr, uid, ids, name, args, context=None):
        result = {}
        obj_cfg = self.pool.get('tcv.bounced.cheq.config')
        comp_id = self.pool.get('res.users').browse(cr, uid, uid).company_id.id
        config = obj_cfg.company_config_get(cr, uid, comp_id, context)
        for bou in self.browse(cr, uid, ids, context=context):
            result[bou.id] = config.use_fee and bou.motive_id.use_fee \
                and not bou.fee_document_id
        return result

    _columns = {
        'ref': fields.char(
            'Reference', size=32, readonly=True),
        'date': fields.date(
            'Date', required=True, readonly=True,
            states={'draft': [('readonly', False)]}, select=True),
        'name': fields.char(
            'Cheq number', size=32, required=True, readonly=True,
            states={'draft': [('readonly', False)]}),
        'deposit_line_id': fields.many2one(
            'tcv.bank.deposit.line', 'Deposit line', readonly=True,
            states={'draft': [('readonly', False)]},
            ondelete='restrict',
            help="You can select a registered cheq from bank deposit."),
        'bank_journal_id': fields.many2one(
            'account.journal', 'Bank journal', required=True, readonly=True,
            states={'draft': [('readonly', False)]}, ondelete='restrict'),
        'motive_id': fields.many2one(
            'tcv.bounced.cheq.motive', 'Bounce motive', required=True,
            readonly=True, states={'draft': [('readonly', False)]},
            ondelete='restrict'),
        'partner_id': fields.many2one(
            'res.partner', 'Partner', required=True, readonly=True,
            states={'draft': [('readonly', False)]}, ondelete='restrict'),
        'amount': fields.float(
            'Amount', digits_compute=dp.get_precision('Account'),
            required=True, readonly=True,
            states={'draft': [('readonly', False)]}),
        'company_id': fields.many2one(
            'res.company', 'Company', required=True, readonly=True,
            states={'draft': [('readonly', False)]}, ondelete='restrict'),
        'currency_id': fields.many2one(
            'res.currency', 'Currency', required=True, readonly=True,
            states={'draft': [('readonly', False)]}, ondelete='restrict'),
        'move_id': fields.many2one(
            'account.move', 'Account move', ondelete='restrict',
            help="The move of this entry line.", select=2, readonly=True),
        'invoice_id': fields.many2one(
            'account.invoice', 'Related invoice', ondelete='restrict',
            readonly=True, states={'draft': [('readonly', False)]}),
        'button_fee': fields.function(
            _get_fee_data, method=True, string='charge fee', type='boolean',
            store={
                'tcv.bounced.cheq': (lambda self, cr, uid, ids, c={}: ids,
                                     ['motive_id', 'fee_document_id'], 10),
                'tcv.bounced.cheq.motive': (
                    _get_use_fee_from_motive, None, 50),
                'tcv.bounced.cheq.config': (
                    _get_use_fee_from_config, None, 50),
                'account.invoice': (_get_use_fee_from_invoice, None, 50),
            },),
        'fee_document_id': fields.many2one(
            'account.invoice', 'Fee document', ondelete='set null',
            readonly=True),
        'state': fields.selection(
            STATE_SELECTION, string='State', required=True, readonly=True),
        'narration': fields.text(
            'Notes', readonly=False),
        'residual': fields.function(
            _amount_residual, method=True,
            digits_compute=dp.get_precision('Account'), string='Residual',
            store={
                _name: (lambda self, cr, uid, ids, c={}: ids,
                        ['amount', 'move_id', 'payment_ids', 'chq_location'],
                        10),
                'account.move.line': (
                    _get_bounced_from_line,
                    ['reconcile_id', 'reconcile_partial_id'], 20),
                'account.move.reconcile': (
                    _get_bounced_from_reconcile, None, 50),
            }, help="Remaining amount due."),
        'payment_ids': fields.function(
            _compute_lines, method=True, relation='account.move.line',
            type="many2many", string='Payments'),
        'user_id': fields.many2one(
            'res.users', 'Notify user', readonly=True,
            states={'draft': [('readonly', False)]}, select=True,
            ondelete='restrict',
            help='Send a message to this user with bounced check\'s '
            'information'),
        'chq_location': fields.selection(
            [('bank', 'Bank'), ('coordination', 'Coordination'),
             ('company', 'Company'), ('customer', 'Customer')],
            string='Physical location', required=True,
            help='The physical location of the check', select=True),
        'date_in_coordination': fields.datetime(
            'Date in (Coordination)', required=False, select=True,
            help='Date of receipt of the check'),
        'date_in_company': fields.datetime(
            'Date in (company)', required=False, select=True,
            help='Date of receipt of the check'),
        'date_out_partner': fields.datetime(
            'Date out (to customer)', required=False, select=True,
            help='Customer delivery date'),
        'partner_received_by': fields.char(
            'Received by (customer)', size=64, required=False,
            help='Name of the receiver of the check (by customer)'),
        }

    _defaults = {
        'ref': '/',
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        'amount': lambda *a: 0.0,
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company').
        _company_default_get(cr, uid, 'tcv_bounced_cheq', context=c),
        'currency_id': lambda self, cr, uid, c: self.pool.get('res.users').
        browse(cr, uid, uid, c).company_id.currency_id.id,
        'state': 'draft',
        'chq_location': 'bank',
        }

    _sql_constraints = [
        ('deposit_line_id_uniq', 'UNIQUE(deposit_line_id)',
         'The cheq is already bounced !'),
        ('residual_range', 'CHECK(residual >= 0)',
         'The residual amount must be >= 0.'),
        ('amount_range', 'CHECK(amount > 0)', 'The amount must be > 0.'),
        ]

    def _get_deposit_line_data(self, cr, uid, deposit_line_id):
        org = self.pool.get('tcv.bank.deposit.line').browse(
            cr, uid, deposit_line_id, context=None)
        res = {
            'bank_journal_id': org.line_id.bank_journal_id.id,
            'partner_id': org.partner_id.id,
            'amount': org.amount,
            'name': org.move_line.ref}
        return res

    def on_change_deposit_line_id(self, cr, uid, ids, deposit_line_id):
        res = {}
        if deposit_line_id:
            res = {'value': self._get_deposit_line_data(
                cr, uid, deposit_line_id)}
        else:
            res = {'value': {'bank_journal_id': 0,
                             'partner_id': 0,
                             'amount': 0,
                             'name': ''}}
        return res

    def on_change_motive_id(self, cr, uid, ids, motive_id):
        context = {}
        res = {}
        if motive_id and ids:
            if type(ids) == int:
                ids = [ids]
            bou = self.browse(cr, uid, ids, context=context)[0]
            config = self.pool.get('tcv.bounced.cheq.config').\
                company_config_get(cr, uid, bou.company_id.id, context)
            motive = self.pool.get('tcv.bounced.cheq.motive').\
                browse(cr, uid, motive_id, context=context)
            res = {'value': {
                'button_fee': config.use_fee and motive.use_fee and
                not bou.fee_document_id}}
        return res

    def _gen_account_move_line(self, company_id, partner_id, account_id,
                               name, debit, credit):
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
        obj_per = self.pool.get('account.period')
        move_id = None
        for bou in self.browse(cr, uid, ids, context={}):
            obj_cfg = self.pool.get('tcv.bounced.cheq.config')
            config = obj_cfg.company_config_get(
                cr, uid, bou.company_id.id, context)
            period_id = obj_per.find(cr, uid, bou.date)[0]
            move = {
                'ref': '%s - Nro %s' % (context.get('bounced_cheq_ref', 'bch'),
                                        bou.name),
                'journal_id': config.journal_id.id,
                'date': bou.date,
                'period_id': period_id,
                'company_id': bou.company_id.id,
                'state': 'draft',
                'to_check': False,
                'narration': '',
                }
            lines = []
            lines.append(self._gen_account_move_line(
                bou.company_id.id,
                bou.partner_id.id,
                bou.partner_id.property_account_receivable.id,
                _('Bounced cheq #%s') % bou.name,
                bou.amount,
                0))
            lines.append(self._gen_account_move_line(
                bou.company_id.id,
                bou.partner_id.id,
                bou.bank_journal_id.default_credit_account_id.id,
                _('Bounced cheq #%s') % bou.name,
                0,
                bou.amount))
            lines.reverse()
            move.update({'line_id': lines})
            move_id = obj_move.create(cr, uid, move, context)
            obj_move = self.pool.get('account.move')
            obj_move.post(cr, uid, [move_id], context=context)
        return move_id

    def bounced_cheq_pay(self, cr, uid, ids, context=None):
        if not ids:
            return []
        bou = self.browse(cr, uid, ids[0], context=context)
        bounced_ids = []
        for m in bou.move_id.line_id:
            if m.account_id.type in ('receivable', 'payable'):
                bounced_ids.append(m.id)
        return {
            'name': _("Pay bounced cheq"),
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'account.voucher',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'domain': '[]',
            'context': {
                'default_partner_id': bou.partner_id.id,
                'default_amount': bou.residual,
                'default_name': _('Replacement %s') % bou.name,
                'close_after_process': True,
                'invoice_type': 'out_invoice',
                'move_line_ids': bounced_ids,
                'default_type': 'receipt',
                'default_narration': _(
                    'Bounced cheq payment\n\tRef: %s\n\tAmount: %.2f\n\t'
                    'Date: %s\n\tMotive: %s') % (
                        bou.name, bou.amount, bou.date, bou.motive_id.name),
                }
        }

    def _notify_users(self, cr, uid, ids, notify_list, context=None):
        if not notify_list:
            return True
        request = self.pool.get('res.request')
        bounced = self.pool.get('tcv.bounced.cheq')
        for n in notify_list:
            bou = bounced.browse(cr, uid, n['bounced_id'], context=context)
            rq_id = request.create(cr, uid, {
                'name': _("Bounced cheq"),
                'act_from': uid,
                'act_to': n['user_id'],
                'body': n['message'],
                'ref_partner_id': bou.partner_id.id,
                #~ 'ref_doc1': 'purchase.order,%d' % (po.id,),
                'trigger_date': time.strftime(_('%Y-%m-%d %H:%M:%S'))
            })
            request.request_send(cr, uid, [rq_id])
        return True

    def _get_period(self, cr, uid, context={}):
        """
        Return  default account period value
        """
        account_period_obj = self.pool.get('account.period')
        ids = account_period_obj.find(cr, uid, context=context)
        period_id = False
        if ids:
            period_id = ids[0]
        return period_id

    def _gen_fee_document(self, cr, uid, ids, context=None):
        obj_bou = self.pool.get('tcv.bounced.cheq')
        bou = obj_bou.browse(cr, uid, ids, context=context)
        obj_cfg = self.pool.get('tcv.bounced.cheq.config')
        cfg = obj_cfg.company_config_get(cr, uid, bou.company_id.id, context)
        taxes = map(lambda x: x.id, cfg.fee_product_id.taxes_id)
        line = {'product_id': cfg.fee_product_id.id,
                'concept_id': cfg.fee_product_id.concept_id.id,
                'uos_id': cfg.fee_product_id.uom_id.id,
                'quantity': 1,
                'price_unit': cfg.fee_amount,
                'discount': 0.0,
                'name': _('%s [check: %s amount:%.2f]') %
                (cfg.fee_product_id.name, bou.name, bou.amount),
                'account_id': cfg.fee_product_id.property_account_income.id,
                'invoice_line_tax_id': [(6, 0, taxes)],
                }
        inv = {'journal_id': cfg.fee_journal_id.id,
               'currency_id': bou.currency_id.id,
               'partner_id': bou.partner_id.id,
               'address_invoice_id': self.pool.get('res.partner').
               address_get(
                   cr, uid, [bou.partner_id.id], ['invoice'])['invoice'],
               'date': time.strftime('%Y-%m-%d'),
               'date_document': time.strftime('%Y-%m-%d'),
               'type': 'out_invoice',
               'account_id': bou.partner_id.property_account_receivable.id,
               'company_id': bou.company_id.id,
               'user_id': uid,
               'name': _('Bounced check fee [%s]') % (bou.ref),
               'origin': _('Bounced check fee: %s (Invoice #: %s)') %
               (bou.ref, bou.invoice_id.number if bou.invoice_id else 'N/A'),
               'state': 'draft',
               'invoice_line': [(0, 0, line)],
               }
        context.update({'fee_document_type': cfg.document_type})
        if cfg.document_type == 'refund':
            inv.update({'parent_id': bou.invoice_id.id})

        obj_inv = self.pool.get('account.invoice')
        res = obj_inv.create(cr, uid, inv, context)
        obj_inv.button_reset_taxes(cr, uid, [res], context)

        obj_bou.write(cr, uid, ids, {'fee_document_id': res}, context)

        return res

    def manual_fee_document(self, cr, uid, ids, context=None):
        context = context or {}
        bou = self.browse(cr, uid, ids[0], context=context)
        if not bou.invoice_id:
            raise osv.except_osv(
                _('Error!'),
                _("You must indicate a related invoice !"))

        mod_obj = self.pool.get('ir.model.data')
        res = mod_obj.get_object_reference(cr, uid, 'account', 'invoice_form')
        res_id = res and res[1] or False,

        doc_id = self._gen_fee_document(cr, uid, ids[0], context)
        name = _(
            'Debit Note (bounced check fee)') \
            if context.get('fee_document_type') == 'refund' \
            else _('Customer Invoices (bounced check fee)')

        return {
            'name': name,
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': [res_id],
            'res_model': 'account.invoice',
            'context': "{'type':'out_invoice'}",
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'res_id': doc_id or False,
        }

    def create(self, cr, uid, vals, context=None):
        if vals.get('deposit_line_id'):
            vals.update(self._get_deposit_line_data(
                cr, uid, vals['deposit_line_id']))
        return super(tcv_bounced_cheq, self).create(cr, uid, vals, context)

    def write(self, cr, uid, ids, vals, context=None):
        if vals.get('deposit_line_id'):
            vals.update(self._get_deposit_line_data(
                cr, uid, vals['deposit_line_id']))
        return super(tcv_bounced_cheq, self).write(cr, uid, ids, vals, context)

    def unlink(self, cr, uid, ids, context=None):
        unlink_ids = []
        for bou in self.browse(cr, uid, ids, context={}):
            if bou.state in ('draft', 'cancel'):
                unlink_ids.append(bou.id)
            else:
                raise osv.except_osv(
                    _('Invalid action !'),
                    _('Cannot delete Bounced that are already Validated!'))
        return super(tcv_bounced_cheq, self).unlink(
            cr, uid, unlink_ids, context)

    ##---------------------------------------------------------------- Workflow

    def test_open(self, cr, uid, ids, *args):
        so_brw = self.browse(cr, uid, ids, context={})
        for bou in so_brw:
            if bou.deposit_line_id and \
                    not bou.deposit_line_id.origin.use_bounced_cheq:
                raise osv.except_osv(
                    _('Error!'),
                    _("Can't generate a bounced cheq form this deposit's " +
                      "origin (%s)") % (bou.deposit_line_id.origin.name))
            if bou.motive_id.need_note and not bou.narration:
                raise osv.except_osv(
                    _('Error!'),
                    _("This bounce motive requires a note"))
            if bou.invoice_id and \
                    bou.partner_id.id != bou.invoice_id.partner_id.id:
                raise osv.except_osv(
                    _('Error!'),
                    _("The related invoice's partner must be the same of " +
                      "bounced check's partner"))
        return True

    def test_cancel(self, cr, uid, ids, *args):
        so_brw = self.browse(cr, uid, ids, context={})
        #~ obj_inv = self.pool.get('account.invoice')
        for bou in so_brw:
            if bou.move_id.id:
                move = self.pool.get('account.move').browse(
                    cr, uid, bou.move_id.id, context=None)
                for l in bou.move_id.line_id:
                    if l.reconcile_id or l.reconcile_partial_id:
                        raise osv.except_osv(
                            _('Error!'),
                            _('You can not cancel a bounced cheq while the ' +
                              'account move is reconciled.'))
                if move.state == 'posted':
                    raise osv.except_osv(
                        _('Error!'),
                        _('You can not cancel a bounced cheq while the ' +
                          'account move is posted.'))
            if bou.fee_document_id:
                raise osv.except_osv(
                    _('Error!'),
                    _('You can not cancel a bounced with fee document ' +
                      'asigned (You must delete the fee document).'))
        return True

    def button_cancel(self, cr, uid, ids, context=None):
        obj_bou = self.pool.get('tcv.bounced.cheq')
        obj_mov = self.pool.get('account.move')
        res = {}
        vals = {'state': 'cancel'}
        for bou in self.browse(cr, uid, ids, context=context):
            if bou.state == 'open':
                if bou.move_id.id:
                    move = obj_mov.browse(
                        cr, uid, bou.move_id.id, context=None)
                    if move.state == 'draft':
                        vals.update({'move_id': 0})
        if vals:
            res = obj_bou.write(cr, uid, ids, vals, context)
        if vals.get('move_id'):
            obj_mov.unlink(cr, uid, [move.id])
        return res

    def button_draft(self, cr, uid, ids, context=None):
        vals = {'state': 'draft'}
        return self.write(cr, uid, ids, vals, context)

    def button_reopen(self, cr, uid, ids, context=None):
        context = context or {}
        if len(ids) != 1:
            raise osv.except_osv(
                _('Error!'),
                _('Multiplies validations not allowed.'))
        return self.write(cr, uid, ids, {'state': 'open'}, context)

    def button_open(self, cr, uid, ids, context=None):
        context = context or {}
        if len(ids) != 1:
            raise osv.except_osv(
                _('Error!'),
                _('Multiplies validations not allowed.'))
        notify_list = []
        vals = {}
        cfg = False
        for bou in self.browse(cr, uid, ids, context={}):
            if not cfg:
                obj_cfg = self.pool.get('tcv.bounced.cheq.config')
                cfg = obj_cfg.company_config_get(
                    cr, uid, bou.company_id.id, context)
            ref = bou.ref if bou.ref != '/' else self.pool.get(
                'ir.sequence').get(cr, uid, 'bounced.cheq')
            context.update({'bounced_cheq_ref': ref})
            if bou.user_id or (cfg.notify_salesman and bou.invoice_id):
                message = _(
                    'The check number: %s (%s), has been returned\n\t' +
                    'Motive: %s.\n\tRef: %s\n\tDate: %s\n\tAmount: %.2f') % (
                        bou.name, bou.partner_id.name, bou.motive_id.name,
                        bou.ref, bou.date, bou.amount)
                if bou.user_id:
                    notify_list.append({
                        'user_id': bou.user_id.id,
                        'bounced_id': bou.id,
                        'message': message})
                if cfg.notify_salesman and bou.invoice_id and \
                        bou.user_id.id != bou.invoice_id.user_id.id:
                    notify_list.append({
                        'user_id': bou.invoice_id.user_id.id,
                        'bounced_id': bou.id,
                        'message': message})
            move_id = self._gen_account_move(
                cr, uid, ids, context) if not bou.move_id else bou.move_id.id
        obj = self.pool.get('tcv.bounced.cheq')
        vals.update({'state': 'open', 'ref': ref, 'move_id': move_id})
        self._notify_users(cr, uid, ids, notify_list, context)
        return obj.write(cr, uid, ids, vals, context)

    def button_paid(self, cr, uid, ids, context=None):
        #~ print 'button_paid', button_paid
        vals = {'state': 'paid'}
        res = self.write(cr, uid, ids, vals, context)
        notify_list = []
        for id in ids:
            bou = self.browse(cr, uid, id, context=context)
            if bou.user_id:
                message = _(
                    'The bounced check %s (%s), has been payed.\n\t' +
                    'Date: %s\n\tAmount: %.2f') % (
                        bou.ref, bou.partner_id.name,
                        time.strftime(_("%Y-%m-%d")), bou.amount)
                notify_list.append({
                    'user_id': bou.user_id.id,
                    'bounced_id': bou.id,
                    'message': message})
        self._notify_users(cr, uid, ids, notify_list, context)
        return res


tcv_bounced_cheq()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
