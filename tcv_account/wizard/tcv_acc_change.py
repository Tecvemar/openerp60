# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description: Report parser for: tcv_acc_change
#
#
##############################################################################

#~ from datetime import datetime
from osv import fields, osv
from tools.translate import _
#~ import pooler
import decimal_precision as dp
#~ import time
#~ import netsvc

##-------------------------------------------------------------- tcv_acc_change


class tcv_acc_change(osv.osv_memory):

    _name = 'tcv.acc.change'

    _description = ''

    ##-------------------------------------------------------------------------

    def default_get(self, cr, uid, fields, context=None):
        context = context or {}
        obj_mov = self.pool.get('account.move')
        data = super(tcv_acc_change, self).default_get(
            cr, uid, fields, context)
        if context.get('active_model') == u'account.move' and \
                context.get('active_id'):
            move_id = context['active_id']
            move_brw = obj_mov.browse(cr, uid, move_id, context=context)
            if move_brw.state != 'draft' or \
                    move_brw.period_id.state != 'draft':
                raise osv.except_osv(
                    _('Error!'),
                    _('Only moves in draft for open periods must be fixed'))
            acc_ids = []
            acc_data = {}
            for line in move_brw.line_id:
                acc_id = line.account_id.id
                if acc_id not in acc_ids:
                    acc_ids.append(acc_id)
                    acc_data[acc_id] = {
                        'code': line.account_id.code,
                        'account_id': acc_id,
                        'account_id2': acc_id,
                        'new_account_id': acc_id,
                        'qty': 0,
                        'qty2': 0,
                        'debit': 0,
                        'debit2': 0,
                        'credit': 0,
                        'credit2': 0,
                        }
                acc_data[acc_id]['qty'] += 1
                acc_data[acc_id]['qty2'] += 1
                acc_data[acc_id]['debit'] += line.debit
                acc_data[acc_id]['debit2'] += line.debit
                acc_data[acc_id]['credit'] += line.credit
                acc_data[acc_id]['credit2'] += line.credit
            lines = sorted(acc_data.values(), key=lambda k: k['code'])
            data.update({
                'move_id': move_id,
                'reference': move_brw.ref,
                'journal_id': move_brw.journal_id.id,
                'date': move_brw.date,
                'line_ids': lines
                })
        return data

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'move_id': fields.many2one(
            'account.move', 'Accounting entries', ondelete='restrict',
            help="The move of this entry line.", select=True, readonly=True),
        'reference': fields.related(
            'move_id', 'ref', type='char', string='Reference', size=128,
            store=False, readonly=True),
        'journal_id': fields.related(
            'move_id', 'journal_id', type='many2one',
            relation='account.journal', string='Journal', store=False,
            readonly=True),
        'date': fields.related(
            'move_id', 'date', type='date', string='Date', store=False,
            readonly=True),
        'line_ids': fields.one2many(
            'tcv.acc.change.lines', 'line_id', 'String'),
        }

    _defaults = {
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    def button_done(self, cr, uid, ids, context=None):
        obj_aml = self.pool.get('account.move.line')
        obj_mov = self.pool.get('account.move')
        for item in self.browse(cr, uid, ids, context={}):
            mov_brw = obj_mov.browse(cr, uid, item.move_id.id, context=context)
            narration = _('Reclassified:')
            replaced = False
            for line in item.line_ids:
                if line.account_id and \
                        line.account_id.id != line.new_account_id.id:
                    replaced = True
                    line_ids = obj_aml.search(
                        cr, uid, [('move_id', '=', item.move_id.id),
                                  ('account_id', '=', line.account_id.id)])
                    obj_aml.write(cr, uid, line_ids, {
                        'account_id': line.new_account_id.id}, context=context)
                    accounts = '\t%s -> %s' % (
                        line.account_id.code, line.new_account_id.code)
                    narration = '%s\n%s' % (narration, accounts)
            if not replaced:
                raise osv.except_osv(
                    _('Error!'),
                    _('No accounts to reclassify'))
            obj_mov.write(cr, uid, [mov_brw.id], {
                'narration': '\n%s\n%s' % (
                    mov_brw.narration or '', narration)},
                context=context)
        return {'type': 'ir.actions.act_window_close'}

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_acc_change()


class tcv_acc_change_lines(osv.osv_memory):

    _name = 'tcv.acc.change.lines'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'line_id': fields.many2one(
            'tcv.acc.change', 'line_ids', required=True, ondelete='cascade'),
        'account_id': fields.many2one(
            'account.account', 'Account', required=True, readonly=True,
            ondelete='restrict'),
        'account_id2': fields.many2one(
            'account.account', 'Account', required=True, readonly=False,
            ondelete='restrict'),
        'new_account_id': fields.many2one(
            'account.account', 'New account', required=True,
            ondelete='restrict', domain=[('type', '!=', 'view')]),
        'qty': fields.integer(
            'Lin qty', readonly=True),
        'qty2': fields.integer(
            'Lin qty', readonly=False),
        'debit': fields.float(
            'Debit', digits_compute=dp.get_precision('Account'),
            readonly=True),
        'debit2': fields.float(
            'Debit', digits_compute=dp.get_precision('Account'),
            readonly=False),
        'credit': fields.float(
            'Credit', digits_compute=dp.get_precision('Account'),
            readonly=True),
        'credit2': fields.float(
            'Credit', digits_compute=dp.get_precision('Account'),
            readonly=False),
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

    def create(self, cr, uid, vals, context=None):
        #autoref
        vals.update({
            'account_id': vals.get('account_id2', None),
            'qty': vals.get('qty2', 0),
            'debit': vals.get('debit2', 0),
            'credit': vals.get('credit2', 0),
            })
        res = super(tcv_acc_change_lines, self).create(
            cr, uid, vals, context)
        return res

    ##---------------------------------------------------------------- Workflow

tcv_acc_change_lines()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
