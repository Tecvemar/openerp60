# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date: 14/08/2012
#    Version: 0.0.0.0
#
#    Description: Account voucher extension
#
#
##############################################################################
#~ from datetime import datetime
from osv import fields, osv
from tools.translate import _
#~ import pooler
#~ import decimal_precision as dp
#~ import time
#~ import netsvc

##------------------------------------------------------- class account_voucher


class account_voucher(osv. osv):

    _inherit = 'account.voucher'

    _columns = {
        'payment_doc': fields.selection(
            [('cash', 'Cash'), ('transfer', 'Transfer'), ('check', 'Check')],
            string='Payment document', readonly=True,
            states={'draft': [('readonly', False)]}, required=False),
        'check_id': fields.many2one(
            'tcv.bank.checks', 'Check #', ondelete='restrict', readonly=True,
            states={'draft': [('readonly', False)]},
            domain="[('journal_id', '=', journal_id), " +
            "('state', '=', 'available'), " +
            "('checkbook_state', '=', 'active')]"),
        'beneficiary': fields.related('check_id', 'beneficiary', type='char',
                                      size=64, string='Beneficiary',
                                      store=False, readonly=True,
                                      states={'draft': [('readonly', False)]}),
        'user_id': fields.many2one('res.users', 'User', readonly=True,
                                   select=True, ondelete='restrict'),
        }

    _sql_constraints = [
        ('check_id_unique', 'UNIQUE(check_id)',
         'This check is already used in other voucher'),
        ]

    ##------------------------------------------------------------ on_change...

    def on_change_payment_doc(self, cr, uid, ids, payment_doc, partner_id):
        if not partner_id or payment_doc != 'check':
            return {'value': {'check_id': 0, 'beneficiary': ''}}
        partner = self.pool.get('res.partner').\
            browse(cr, uid, partner_id, context=None)
        res = {'value': {'beneficiary': partner.name}}
        return res

    def on_change_check_id(self, cr, uid, ids, check_id,
                           beneficiary, partner_id):
        if not check_id or not partner_id:
            return {'value': {'beneficiary': ''}}
        if beneficiary:
            benef = beneficiary
        else:
            partner = self.pool.get('res.partner').\
                browse(cr, uid, partner_id, context=None)
            benef = partner.name
        res = {'value': {'beneficiary': benef}}
        if check_id:
            check = self.pool.get('tcv.bank.checks').\
                browse(cr, uid, check_id, context=None)
            res['value'].update({'reference': u'Ch Nº: %s' % check.full_name})
        return res

    def onchange_partner_id(self, cr, uid, ids, partner_id, journal_id,
                            amount, currency_id, type, date, context=None):
        res = super(account_voucher, self).onchange_partner_id(
            cr, uid, ids, partner_id, journal_id, amount, currency_id, type,
            date, context)
        if not res.get('value'):
            res.update({'value': {}})
        res['value'].update({
            'check_id': 0, 'beneficiary': None, 'payment_doc': ''})
        obj_abk = self.pool.get('tcv.bank.account')
        if journal_id and type == 'payment':
            jnl = self.pool.get('account.journal').browse(
                cr, uid, journal_id, context=context)
            if jnl.type == 'cash':
                res['value'].update({'payment_doc': 'cash'})
            elif jnl.type == 'bank':
                if obj_abk.account_use_check(cr, uid, jnl.id):
                    res['value'].update({'payment_doc': 'check'})
                else:
                    res['value'].update({'payment_doc': 'transfer'})
        return res

    ##-------------------------------------------------------------------------

    #~ def print_banck_check(self, cr, uid, ids, context=None):
        #~ return True

    ##----------------------------------------------------- create write unlink

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        obj_chk = self.pool.get('tcv.bank.checks')
        res = super(account_voucher, self).create(cr, uid, vals, context)
        if vals.get('payment_doc') == 'check':
            if vals.get('check_id') and vals.get('beneficiary'):
                obj_chk.write(cr, uid, [vals['check_id']], {
                    'beneficiary': vals['beneficiary'],
                    'voucher_id': res,
                    'user_id': uid}, context)
                obj_chk.send_workflow_signal(
                    cr, uid, vals['check_id'], 'button_draft')
            else:
                raise osv.except_osv(
                    _('Error!'),
                    _('You must indicate a check and beneficiary name'))
        return res

    def write(self, cr, uid, ids, vals, context=None):
        obj_chk = self.pool.get('tcv.bank.checks')
        old_benef = None
        for v in self.browse(cr, uid, ids, context={}):
            if v.check_id and (
                    vals.get('check_id') or
                    vals.get('payment_doc') in ('cash', 'transfer')) \
                    and v.check_id.state in ('available', 'draft'):
                old_benef = obj_chk.browse(
                    cr, uid, v.check_id.id, context=context). beneficiary
                obj_chk.send_workflow_signal(
                    cr, uid, v.check_id.id, 'button_available')
                if vals.get('payment_doc') in ('cash', 'transfer'):
                    vals.update({'check_id': 0})
            if vals.get('check_id'):
                if not vals.get('beneficiary') and old_benef:
                    vals.update({'beneficiary': old_benef})
                obj_chk.write(cr, uid, [vals['check_id']], {
                    'beneficiary': vals.get('beneficiary', None),
                    'voucher_id': v.id,
                    'user_id': uid,
                    }, context)
                obj_chk.send_workflow_signal(
                    cr, uid, vals['check_id'], 'button_draft')
        if vals.get('state') == 'posted':
            vals.update({'user_id': uid})
        res = super(account_voucher, self).write(cr, uid, ids, vals, context)
        return res

    def unlink(self, cr, uid, ids, context=None):
        obj_chk = self.pool.get('tcv.bank.checks')
        for v in self.browse(cr, uid, ids, context={}):
            if v.check_id and v.check_id.state == 'draft':
                obj_chk.send_workflow_signal(
                    cr, uid, v.check_id.id, 'button_available')
            elif v.check_id and v.check_id.cancel_bounce_id:
                raise osv.except_osv(
                    _('Error!'),
                    _('Can\t delete a voucher while check is bounced'))
        res = super(account_voucher, self).unlink(cr, uid, ids, context)
        return res

    ##---------------------------------------------------------------- Workflow

    def test_done(self, cr, uid, ids, *args):
        obj_abk = self.pool.get('tcv.bank.account')
        for v in self.browse(cr, uid, ids, context={}):
            lines_amount = 0
            for l in v.line_ids:
                if l.amount:
                    lines_amount += l.amount
            if lines_amount == 0 and v.amount == 0:
                raise osv.except_osv(
                    _('Error!'),
                    _('Can\'t validate a voucher with amount <= 0'))
            if v.type in ('payment'):
                if v.journal_id.type == 'bank':
                    if v.payment_doc == 'cash':
                        raise osv.except_osv(
                            _('Error!'),
                            _('Can\'t use "cash" as payment document for this journal'))
                    if v.payment_doc == 'check' and \
                            not obj_abk.account_use_check(
                                cr, uid, v.journal_id.id):
                        raise osv.except_osv(
                            _('Error!'),
                            _('Can\'t use "check" as payment document for this journal'))
                elif v.journal_id.type == 'cash':
                    if v.payment_doc != 'cash':
                        raise osv.except_osv(
                            _('Error!'),
                            _('Must use "cash" as payment document for this journal'))
                if v.check_id:
                    if v.check_id.state not in ('available', 'draft'):
                        raise osv.except_osv(
                            _('Error!'),
                            _('Can\'t use a check with state <> "available"'))
                    if v.check_id.voucher_id.id != v.id:
                        other = self.pool.get('account.voucher').browse(
                            cr, uid, v.check_id.voucher_id.id, context=None)
                        raise osv.except_osv(
                            _('Error!'),
                            _('Check is already used in other voucher (%s - %s)')
                            % (other.partner_id.name, other.name))
            # validata voucher amount vs lines amount
            if v.voucher_type == 'normal' and \
                    v.payment_option == 'without_writeoff':  # from tcv_advance
                lines_amount = 0.0  # v.writeoff_amount
                for l in v.line_ids:
                    amount = l.amount
                    if amount and (
                        (v.type in ('receipt') and l.type == 'dr') or
                            (v.type in ('payment') and l.type == 'cr')):
                        amount *= -1
                    lines_amount += amount
                if abs(v.amount - lines_amount) > 0.0001:
                    raise osv.except_osv(
                        _('Error!'),
                        _('The voucher\'s amount dosen\'t correspond with line\'s amount'))
        return super(account_voucher, self).test_done(cr, uid, ids, args)

    def proforma_voucher(self, cr, uid, ids, context=None):
        obj_chk = self.pool.get('tcv.bank.checks')
        for v in self.browse(cr, uid, ids, context={}):
            if v.check_id and v.check_id.state in ('draft'):
                obj_chk.send_workflow_signal(
                    cr, uid, v.check_id.id, 'button_issued')
            if v.check_id and v.check_id.state not in ('draft'):
                raise osv.except_osv(
                    _('Error!'),
                    _('Can\'t valitade voucher, check state invalid (%s)')
                    % v.check_id.state)
        return super(account_voucher, self).proforma_voucher(
            cr, uid, ids, context)

    def test_cancel(self, cr, uid, ids, *args):
        for v in self.browse(cr, uid, ids, context={}):
            if v.check_id:
                if v.check_id.state not in ('issued'):
                    raise osv.except_osv(
                        _('Error!'),
                        _('Can\'t cancel voucher when check\'s state <> issued'))
                elif v.check_id.cancel_bounce_id:
                    raise osv.except_osv(
                        _('Error!'),
                        _('Can\t cancel a voucher while check is bounced'))
        return super(account_voucher, self).test_cancel(cr, uid, ids, args)

    def cancel_voucher(self, cr, uid, ids, context=None):
        obj_chk = self.pool.get('tcv.bank.checks')
        for v in self.browse(cr, uid, ids, context={}):
            if v.check_id:
                if not self.pool.get('res.users').user_belongs_groups(
                        cr, uid, ('tcv_bank_checks / Manager', ), context):
                    raise osv.except_osv(
                        _('Error!'),
                        _('User must belong to "tcv_bank_checks / Manager" ' +
                          'security group to cancel issued check'))
                if v.check_id.state in ('draft', 'issued'):
                    obj_chk.send_workflow_signal(
                        cr, uid, v.check_id.id, 'button_cancel')
                else:
                    raise osv.except_osv(
                        _('Error!'),
                        _('Can\'t cancel this voucher when check\'s state <> "Issued"'))
        return super(account_voucher, self).cancel_voucher(
            cr, uid, ids, context)

    def cancel_to_draft(self, cr, uid, ids, context=None):
        obj_chk = self.pool.get('tcv.bank.checks')
        for v in self.browse(cr, uid, ids, context={}):
            if v.check_id:
                if v.check_id.state in ('cancel'):
                    obj_chk.send_workflow_signal(
                        cr, uid, v.check_id.id, 'button_available')
                    self.write(cr, uid, [v.id], {'check_id': 0,
                                                 'beneficiary': ''}, context)
        return super(account_voucher, self).cancel_to_draft(
            cr, uid, ids, context)


account_voucher()


##-------------------------------------------------------- account_voucher_line


class account_voucher_line(osv.osv):

    _inherit = 'account.voucher.line'

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    ##-----------------------------------------------------

    ##----------------------------------------------------- public methods

    ##----------------------------------------------------- buttons (object)

    ##----------------------------------------------------- on_change...

    ##----------------------------------------------------- create write unlink

    ##----------------------------------------------------- Workflow

account_voucher_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
