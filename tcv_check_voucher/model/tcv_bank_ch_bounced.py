# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date: 14/08/2012
#    Version: 0.0.0.0
#
#    Description: Main models definitions
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

##--------------------------------------------------------- tcv_bank_ch_bounced

# this class is previusly defined a start of script tcv_bank_check
# Is defined to support cancel_bounce_id <-> check_id  bidirectional reference


class tcv_bank_ch_bounced(osv.osv):

    _inherit = 'tcv.bank.ch.bounced'

    _description = 'Data for bounced and (post data) canceled checks'

    ##-------------------------------------------------------------------------

    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        data = super(tcv_bank_ch_bounced, self).default_get(
            cr, uid, fields, context=context)
        obj_cfg = self.pool.get('tcv.bank.config')
        if obj_cfg:
            company_id = self.pool.get('res.users').browse(
                cr, uid, uid, context).company_id.id
            config = obj_cfg.browse(cr, uid, company_id, context=context)
            if config.acc_bank_comis:
                data.update({'fee_acc_id': config.acc_bank_comis.id})
        return data

    ##--------------------------------------------------------- function fields

    _columns = {
        'check_id': fields.many2one(
            'tcv.bank.checks', 'Check', ondelete='restrict', help="",
            readonly=True, required=True),
        'type': fields.selection(
            [('cancel', 'Canceled'), ('bounce', 'Bounced')],
            string='Type', required=True, readonly=True),
        'name': fields.char(
            'Ref', size=16, readonly=True,
            states={'draft': [('readonly', False)]}),
        'date': fields.date(
            'Date', required=True, readonly=True,
            states={'draft': [('readonly', False)]}, select=True),
        'move_id': fields.many2one(
            'account.move', 'Account move', ondelete='restrict',
            help="The move of this entry line. " +
            "(Only for bounded and canceled checks)",
            select=True, readonly=True),
        'motive_id': fields.many2one(
            'tcv.bounced.cheq.motive', 'Bounce motive',
            ondelete='restrict', readonly=True,
            states={'draft': [('readonly', False)]}),
        'note': fields.char(
            'Note', size=64, required=False, readonly=False),
        'use_fee': fields.boolean(
            'Fee applied', readonly=True,
            states={'draft': [('readonly', False)]}),
        'fee_ref': fields.char(
            'Fee ref', size=16, readonly=True,
            states={'draft': [('readonly', False)]}),
        'fee_amount': fields.float(
            'Amount', digits_compute=dp.get_precision('Account'),
            readonly=True, states={'draft': [('readonly', False)]}),
        'fee_acc_id': fields.many2one(
            'account.account', 'Fee account', required=True,
            ondelete='restrict'),
        'state': fields.selection(
            [('draft', 'Draft'), ('posted', 'Posted')], string='State',
            required=True, readonly=True),
        }

    _defaults = {
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        'state': 'draft',
        }

    _sql_constraints = [(
        'check_id_uniq', 'UNIQUE(check_id)',
        'This check is already canceled or bounced'),
        ]

    ##-------------------------------------------------------------------------

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

    def _unreconcile_account_voucher(self, cr, uid, unreconcile, move_id,
                                     context):
        '''
        Break old reconcile to release invoice payment and reconcile
        original move with check's revese move.
        '''
        if not unreconcile or not move_id:
            return False
        obj_aml = self.pool.get('account.move.line')
        for ur_line in unreconcile:
            #~ Find for id of reverse move line
            nr_line_id = obj_aml.search(
                cr, uid, [
                    ('move_id', '=', move_id),
                    ('account_id', '=', ur_line['account_id']),
                    ('name', '=', ur_line['name']),
                    ('debit', '=', ur_line['debit']),
                    ('credit', '=', ur_line['credit']),
                    ])
            if nr_line_id and len(nr_line_id) == 1:
                #~ Browse reverse move line
                nr_line = obj_aml.browse(
                    cr, uid, nr_line_id[0], context=context)
                #~ Browse original voucher reconciled line
                or_line = obj_aml.browse(
                    cr, uid, ur_line['move_line_id'], context=context)
                #~ compare lines amount debits==credits
                if nr_line.debit == or_line.credit and \
                        nr_line.credit == or_line.debit:
                    #~ Unreconcile original move
                    obj_aml._remove_move_reconcile(
                        cr, uid, [or_line.id], context=None)
                    #~ Reconcile orgiginal and reverse moves
                    obj_aml.reconcile(
                        cr, uid, [nr_line.id, or_line.id], context=context)
        return True

    def _gen_account_move(self, cr, uid, ids, context=None):
        #~ need_reconcile = False
        so_brw = self.browse(cr, uid, ids, context={})
        obj_move = self.pool.get('account.move')
        obj_per = self.pool.get('account.period')
        move_id = None
        for dev in so_brw:
            move = {
                'ref': u'Ch Nº %s [%s]' % (dev.check_id.name, _('Revert')),
                'journal_id': dev.check_id.journal_id.id,
                'period_id': obj_per.find(cr, uid, dev.date)[0],
                'date': dev.date,
                'company_id': dev.check_id.company_id.id,
                'state': 'draft',
                'to_check': False,
                'narration': _(
                    'Reversal of the issuance of the check, Ch: %s Date %s') %
                (dev.check_id.name, dev.check_id.voucher_id.date),
                }
            lines = []
            unreconcile = []
            if dev.check_id.voucher_id.move_ids:
                #~ Reverse actual move lines
                for m in dev.check_id.voucher_id.move_ids:
                    name = u'%s - Ch Nº %s [%s]' % (
                        m.name, dev.check_id.name, _('Revert'))
                    lines.append(self._gen_account_move_line(
                        m.company_id.id,
                        m.partner_id.id,
                        m.account_id.id,
                        name,
                        m.credit,
                        m.debit,
                        ))
                    if m.reconcile_id or m.reconcile_partial_id and \
                            m.account_id.type in ('receivable', 'payable'):
                        unreconcile.append({
                            'move_line_id': m.id,
                            'account_id': m.account_id.id,
                            'name': name,
                            'debit': m.credit,
                            'credit': m.debit,
                            })
            else:
                lines.append(
                    self._gen_account_move_line(
                        dev.check_id.company_id.id,
                        dev.check_id.voucher_id.partner_id.id,
                        dev.check_id.journal_id.default_debit_account_id.id,
                        u'Ch Nº %s [%s]' % (dev.check_id.name, _('Revert')),
                        dev.check_id.amount,
                        0))
                v_id = dev.check_id.voucher_id
                lines.append(
                    self._gen_account_move_line(
                        dev.check_id.company_id.id,
                        v_id.partner_id.id,
                        v_id.partner_id.property_account_payable.id,
                        u'Ch Nº %s [%s]' % (dev.check_id.name, _('Revert')),
                        0,
                        dev.check_id.amount))
            if dev.type == 'bounce' and dev.use_fee:
                    lines.append(
                        self._gen_account_move_line(
                            dev.check_id.company_id.id,
                            dev.check_id.voucher_id.partner_id.id,
                            dev.fee_acc_id.id,
                            u'N/D %s - Ch Nº %s [%s]' % (
                                dev.fee_ref, dev.check_id.name,
                                _('Bounced check fee')),
                            dev.fee_amount,
                            0))
                    ch_id = dev.check_id
                    lines.append(
                        self._gen_account_move_line(
                            ch_id.company_id.id,
                            ch_id.voucher_id.partner_id.id,
                            ch_id.journal_id.default_debit_account_id.id,
                            u'N/D %s - Ch Nº %s [%s]' % (
                                dev.fee_ref, dev.check_id.name,
                                _('Bounced check fee')),
                            0,
                            dev.fee_amount))
            move.update({'line_id': lines})
            move_id = obj_move.create(cr, uid, move, context)
            self._unreconcile_account_voucher(
                cr, uid, unreconcile, move_id, context=context)
            obj_move.post(cr, uid, [move_id], context=context)
        return move_id

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    def create(self, cr, uid, vals, context=None):
        res = super(tcv_bank_ch_bounced, self).create(cr, uid, vals, context)
        if not vals.get('check_id'):
            vals.update({'check_id': context.get('default_check_id')})
        if not vals.get('type'):
            vals.update({'type': context.get('default_type')})
        context.update({'unlock_check_data': True})
        self.pool.get('tcv.bank.checks').write(
            cr, uid, [vals.get('check_id')],
            {'cancel_bounce_id': res}, context)
        return res

    def unlink(self, cr, uid, ids, context=None):
        res = super(tcv_bank_ch_bounced, self).unlink(cr, uid, ids, context)
        for c in self.browse(cr, uid, ids, context=context):
            if c.cancel_bounce_id:
                context.update({'unlock_check_data': True})
                self.pool.get('tcv.bank.checks').write(
                    cr, uid, [c.cancel_bounce_id.id],
                    {'cancel_bounce_id': 0}, context)
        return res

    ##---------------------------------------------------------------- Workflow

    def button_post(self, cr, uid, ids, context=None):
        obj_chk = self.pool.get('tcv.bank.checks')
        for c in self.browse(cr, uid, ids, context=context):
            if c.type == 'cancel':
                obj_chk.send_workflow_signal(
                    cr, uid, c.check_id.id, 'button_post_cancel')
            elif c.type == 'bounce':
                obj_chk.send_workflow_signal(
                    cr, uid, c.check_id.id, 'button_bounced')
            else:
                raise osv.except_osv(
                    _('Error!'),
                    _('Unknown cancel type %s (tcv_bank_ch_bounced)') % c.type)
        data = {
            'state': 'posted',
            'move_id': self._gen_account_move(cr, uid, ids, context)}
        return self.write(cr, uid, ids, data, context)


tcv_bank_ch_bounced()
