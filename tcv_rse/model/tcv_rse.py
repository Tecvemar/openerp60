# -*- encoding: utf-8 -*-
##############################################################################
#    Company: TECVEMAR
#    Author: Gabriel
#    Creation Date: 2016-01-25
#    Version: 1.0
#
#    Description: Manejo de solicitudes de RSE
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


##--------------------------------------------------------------------- tcv_rse


class tcv_rse(osv.osv):

    _name = 'tcv.rse'

    _description = ''

    ##-------------------------------------------------------------------------

    STATE_SELECTION = [
        ('draft', 'Draft'),
        ('open', 'Opened'),
        ('close', 'Closed'),
        ]

    ##------------------------------------------------------- _internal methods

    def _compute_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for item in self.browse(cr, uid, ids, context=context):
            amount_total = 0
            for vou in item.voucher_ids:
                amount_total += vou.amount
            res[item.id] = {'amount_total': amount_total}
        return res

    ##--------------------------------------------------------- function fields

    _columns = {
        'ref': fields.char(
            'Ref', size=64, required=False, readonly=True),
        'name': fields.char(
            'Event name', size=64, required=True, readonly=True,
            states={'draft': [('readonly', False)]}),
        'event_date': fields.date(
            'Event date', required=True, readonly=True,
            states={'draft': [('readonly', False)]}, select=True),
        'date': fields.date(
            'Date', required=True, readonly=True,
            states={'draft': [('readonly', False)]}, select=True),
        'company_id': fields.many2one(
            'res.company', 'Company', required=True, readonly=True,
            ondelete='restrict'),
        'user_id': fields.many2one(
            'res.users', 'User', readonly=True, select=True,
            ondelete='restrict'),
        'partner_id': fields.many2one(
            'res.partner', 'Partner', change_default=True, readonly=True,
            required=True, states={'draft': [('readonly', False)]}),
        'address_id': fields.many2one(
            'res.partner.address', 'Contact Address', change_default=True,
            readonly=True, states={'draft': [('readonly', False)]}),
        'user_validator': fields.many2one(
            'res.users', 'User validator', readonly=True, required=True,
            select=True, ondelete='restrict',
            states={'draft': [('readonly', False)]}),
        'invoice_ids': fields.many2many(
            'account.invoice', 'rse_invoice_rel', 'rse_id',
            'invoice_id', 'Invoices', readonly=True,
            domain=[('type', 'in', ('in_invoice', 'in_refund'))],
            states={'open': [('readonly', False)]}),
        'external_ids': fields.one2many(
            'tcv.rse.ext.inv', 'line_id', 'External invoices', readonly=True,
            states={'open': [('readonly', False)]}),
        'voucher_ids': fields.many2many(
            'account.voucher', 'rse_voucher_rel', 'rse_id',
            'voucher_id', 'Voucher', readonly=True,
            domain=[('type', '=', 'payment')],
            states={'open': [('readonly', False)]}),
        'advance_ids': fields.many2many(
            'account.voucher', 'rse_advance_rel', 'rse_id',
            'advance_id', 'Advance', readonly=True,
            domain=[('voucher_type', '=', 'advance')],
            states={'open': [('readonly', False)]}),
        'move_ids': fields.many2many(
            'account.move', 'rse_move_rel', 'rse_id',
            'move_id', 'Accounting entries', readonly=True,
            domain=[('state', '=', 'posted')],
            states={'open': [('readonly', False)]}),
        'narration': fields.text(
            'Description', readonly=True,
            states={'draft': [('readonly', False)]}),
        'amount_total': fields.function(
            _compute_all, method=True, readonly=True, type='float',
            string='Total amount',
            digits_compute=dp.get_precision('Account'), multi='all'),
        'state': fields.selection(
            STATE_SELECTION, string='State', required=True, readonly=True),
        }

    _defaults = {
        'ref': lambda *a: '/',
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        'user_id': lambda s, c, u, ctx: u,
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company').
        _company_default_get(cr, uid, self._name, context=c),
        'state': lambda *a: 'draft',
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    def on_change_partner_id(self, cr, uid, ids, partner_id):
        res = {'partner_address_id': False}
        if partner_id:
            obj_prn = self.pool.get('res.partner')
            partner = obj_prn.browse(cr, uid, partner_id, context=None)
            address_id = [addr for addr in partner.address if
                          addr.type == 'invoice']
            if address_id:
                res.update({'address_id': address_id[0].id})
        return {'value': res}

    ##----------------------------------------------------- create write unlink

    def create(self, cr, uid, vals, context=None):
        if not vals.get('ref') or vals.get('ref') == '/':
            vals.update({'ref': self.pool.get('ir.sequence').
                         get(cr, uid, 'tcv.rse')})
        res = super(tcv_rse, self).create(cr, uid, vals, context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        obj_grp = self.pool.get('res.groups')
        grp_ids = obj_grp.search(
            cr, uid, [('name', '=', 'tcv_rse / Manager')])
        usr_ids = []
        #~ load all manager user
        for grp in obj_grp.browse(cr, uid, grp_ids, context=context):
            usr_ids.extend([x.id for x in grp.users])
        #~ add owner and validator
        for item in self.browse(cr, uid, ids, context={}):
            usr_ids.extend([item.user_id.id, item.user_validator.id])
        #~ check valid users
        if uid not in usr_ids:
            raise osv.except_osv(
                _('Error!'),
                _('Only user owner or admin can update data.'))
        res = super(tcv_rse, self).write(cr, uid, ids, vals, context)
        return res

    ##---------------------------------------------------------------- Workflow

    def button_draft(self, cr, uid, ids, context=None):
        vals = {'state': 'draft'}
        res = self.write(cr, uid, ids, vals, context)
        return res

    def button_open(self, cr, uid, ids, context=None):
        vals = {'state': 'open'}
        res = self.write(cr, uid, ids, vals, context)
        return res

    def button_close(self, cr, uid, ids, context=None):
        vals = {'state': 'close'}
        res = self.write(cr, uid, ids, vals, context)
        return res

    def test_draft(self, cr, uid, ids, *args):
        return True

    def test_open(self, cr, uid, ids, *args):
        return True

    def test_close(self, cr, uid, ids, *args):
        return True

tcv_rse()


class tcv_rse_ext_inv(osv.osv):

    _name = 'tcv.rse.ext.inv'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'line_id': fields.many2one(
            'tcv.rse', 'External invoices', ondelete='cascade'),
        'date': fields.date(
            'Date', select=True),
        'number': fields.char(
            'Number', size=64),
        'supplier': fields.char(
            'Supplier', size=64),
        'name': fields.text(
            'Description'),
        'amount': fields.float(
            'Amount', digits_compute=dp.get_precision('Account')),
        }

    _defaults = {
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow


tcv_rse_ext_inv()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
