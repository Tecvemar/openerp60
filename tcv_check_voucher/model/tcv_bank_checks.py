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
#~ import decimal_precision as dp
#~ import time
import netsvc


##-----------------------------------------------------------------------------

# Is defined to support  cancel_bounce_id<-->check_id  bidirectional reference

class tcv_bank_ch_bounced(osv.osv):

    _name = 'tcv.bank.ch.bounced'

tcv_bank_ch_bounced()


##------------------------------------------ class tcv_bank_checkbook(osv.osv):


class tcv_bank_checks(osv.osv):

    _name = 'tcv.bank.checks'

    _description = 'Handle check\'s data'

    _states = [('available', 'Available'),
               ('draft', 'Draft'),
               ('issued', 'Issued'),
               ('delivered', 'Delivered'),
               ('charged', 'Charged'),
               ('bounced', 'Bounced'),
               ('cancel', 'Canceled'),
               ('post_cancel', 'Canceled')
               ]

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        res = []
        for record in self.browse(cr, uid, ids, context={}):
            st = ''
            for s in self._states:
                if s[0] == record.state:
                    st = s[1]
            if record.state not in ('cancel', 'post_cancel', 'bounced'):
                name = u'Ch Nº: %s (%s - %s) [%s]' % (
                    record.full_name, record.checkbook_id.name,
                    record.checkbook_id.bank_acc_id.bank_id.name, st)
            else:
                name = u'Ch Nº: %s [%s]' % (record.full_name, st)
            res.append((record.id, name))
        return res

    def _compute_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for item in self.browse(cr, uid, ids, context=context):
            fn = item.bank_acc_id.format_ch_name % item
            res[item.id] = {
                'full_name': fn}
        return res

    _columns = {
        'checkbook_id': fields.many2one(
            'tcv.bank.checkbook', 'Checkbook', required=True,
            ondelete='restrict', readonly=True),
        'bank_acc_id': fields.related(
            'checkbook_id', 'bank_acc_id', type='many2one',
            relation='tcv.bank.account', string='Bank account',
            store=True, readonly=True),
        'use_prefix': fields.related(
            'bank_acc_id', 'use_prefix', type='char', size=16,
            string='Use prefix', store=False, readonly=True),
        'journal_id': fields.related(
            'checkbook_id', 'journal_id', type='many2one',
            relation='account.journal', string='Bank journal',
            store=True, readonly=True),
        'company_id': fields.related(
            'checkbook_id', 'company_id', type='many2one',
            relation='res.company', string='company', store=True,
            readonly=True),
        'checkbook_state': fields.related(
            'checkbook_id', 'state', type='char', size=16,
            relation='tcv.bank.checkbook', string='Checkbook state',
            readonly=True),
        'prefix': fields.integer(
            'Prefix', readonly=False),
        'name': fields.integer(
            'Number', readonly=True),
        'full_name': fields.function(
            _compute_all, method=True, type='char', size=16,
            string='Number', multi='all'),
        'sufix': fields.integer(
            'Sufix', readonly=False),
        'beneficiary': fields.char(
            'Beneficiary', size=64, readonly=True),
        'voucher_id': fields.many2one(
            'account.voucher', 'Voucher', required=False,
            ondelete='restrict', readonly=True),
        'partner_id': fields.related(
            'voucher_id', 'partner_id', type='many2one',
            relation='res.partner', string='Partner', readonly=True),
        'date': fields.related(
            'voucher_id', 'date', type='date', relation='account.voucher',
            string='Date', store=True, readonly=True),
        'amount': fields.related(
            'voucher_id', 'amount', type='float', relation='account.voucher',
            string='Amount', store=True, readonly=True),
        'state': fields.selection(
            _states, string='State', required=True, readonly=True),
        'user_id': fields.many2one(
            'res.users', 'User', readonly=True, select=True,
            ondelete='restrict'),
        'cancel_bounce_id': fields.many2one(
            'tcv.bank.ch.bounced', 'Cancel/Bounce ref', ondelete='restrict',
            help="", select=True, readonly=True),
        }

    _defaults = {
        'state': lambda *a: 'available',
        }

    ##-------------------------------------------------------------------------

    def on_change_partner_id(self, cr, uid, ids, partner_id):
        if not partner_id:
            return []
        partner = self.pool.get('res.partner').\
            browse(cr, uid, partner_id, context=None)
        res = {'value': {'beneficiary': partner.name}}
        return res

    def cancel_bounce_check(self, cr, uid, ids, context):
        if not ids:
            return []
        ch = self.browse(cr, uid, ids[0], context=context)
        if ch.voucher_id and ch.voucher_id.voucher_type == 'advance':
            for ml in ch.voucher_id.move_ids:
                if ml.reconcile_id or ml.reconcile_partial_id:
                    recon_name = \
                        ml.reconcile_id and ml.reconcile_id.name or \
                        ml.reconcile_partial_id and \
                        ml.reconcile_partial_id.name
                    raise osv.except_osv(
                        _('Error!'),
                        _('Can\'t cancel an advance check while is applied ' +
                          'to payment (Reconcile: %s)') % recon_name)

        return {
            'name': context.get('cancel_bounce_name', 'Check'),
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'tcv.bank.ch.bounced',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': {
                'default_check_id': ch.id,
                'default_type': context.get('cancel_bounce_type'),
                'default_name': '%s' % (ch.name),
                }
        }

    ##----------------------------------------------------- create write unlink

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        if not context.get('unlock_check_data'):
            raise osv.except_osv(
                _('Error!'), _('Manual data insertion not allowed'))
        res = super(tcv_bank_checks, self).create(cr, uid, vals, context)
        self.send_workflow_signal(cr, uid, res, 'button_available')
        return res

    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}

        for c in self.browse(cr, uid, ids, context={}):
            if vals.get('voucher_id'):
                ch_id = self.pool.get('tcv.bank.checks').\
                    browse(cr, uid, c.id, context=context)
                if ch_id.voucher_id and vals.get('voucher_id') and \
                        ch_id.voucher_id.id != vals.get('voucher_id'):
                    raise osv.except_osv(
                        _('Error!'),
                        _('This check (%s) is already used in ' +
                          'other voucher (%s - %s)') %
                        (ch_id.name, ch_id.voucher_id.partner_id.name,
                         ch_id.voucher_id.name))
            if not context.get('unlock_check_data'):
                if c.checkbook_state != 'active':
                    raise osv.except_osv(
                        _('Error!'),
                        _('Changes not allowed when checkbook\'s ' +
                          'state <> "Active"'))
        res = super(tcv_bank_checks, self).write(cr, uid, ids, vals, context)
        return res

    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if not context.get('unlock_check_data'):
            raise osv.except_osv(
                _('Error!'), _('Manual deletion not allowed'))
        return super(tcv_bank_checks, self).unlink(cr, uid, ids, context)

    ##---------------------------------------------------------------- Workflow

    def send_workflow_signal(self, cr, uid, ids, signal):
        wf_service = netsvc.LocalService("workflow")
        wf_service.trg_validate(uid, self._name, ids, signal, cr)

    def button_available(self, cr, uid, ids, context=None):
        data = {'beneficiary': None,
                'voucher_id': 0,
                'user_id': 0,
                'state': 'available'}
        return self.write(cr, uid, ids, data, context)

    def test_cancel(self, cr, uid, ids, *args):
        for item in self.browse(cr, uid, ids, context={}):
            if item.checkbook_id.state != 'active':
                raise osv.except_osv(
                    _('Error!'),
                    _('Changes not allowed when checkbook\'s state ' +
                      '<> "Active"'))
        return True

    def test_available(self, cr, uid, ids, *args):
        for item in self.browse(cr, uid, ids, context={}):
            if item.checkbook_id.state != 'active':
                raise osv.except_osv(
                    _('Error!'),
                    _('Changes not allowed when checkbook\'s state <> ' +
                      '"Active"'))
        return True

tcv_bank_checks()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
