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
from datetime import datetime
from osv import fields,osv
from tools.translate import _
import pooler
import decimal_precision as dp
import time

##------------------------------------------------------------------------------------ class tcv_bank_checkbook(osv.osv):

class tcv_bank_checkbook(osv.osv):

    _name = 'tcv.bank.checkbook'

    _description = 'Handle checkbook\'s data'


    def _check_qty(self,first, last):
        res = (last - first) + 1
        return res if res > 0 else 0


    def _calc_check_qty(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for chbk in self.browse(cr, uid, ids, context=context):
            res[chbk.id] = {'check_qty':self._check_qty(chbk.first_check,chbk.last_check),'available_qty':0,'used_qty':0}
            if not chbk.check_ids:
                res[chbk.id]['available_qty'] = res[chbk.id]['check_qty']
            else:
                availables = self.pool.get('tcv.bank.checks').search(cr, uid, [('checkbook_id', '=', chbk.id),('state', '=', 'available')])
                res[chbk.id]['available_qty'] = len(availables)
                res[chbk.id]['used_qty'] = res[chbk.id]['check_qty'] - len(availables)
        return res


    _columns = {
        'bank_acc_id':fields.many2one('tcv.bank.account', 'Bank account', required=True, ondelete='restrict', domain="[('use_check', '=', True)]" ),
        'name': fields.char('Ref', size=16, required=True, readonly=True),
        'number': fields.char('Checkbook #', size=16, required=False, readonly=False),
        'state': fields.selection([('inactive', 'Inactive'),('active', 'Active'),('drained', 'Drained'),('cancel','Canceled')], string='State', required=True, readonly=True),
        'check_qty': fields.function(_calc_check_qty, method=True, type='integer', string='Check qty', multi='all'),
        'first_check': fields.integer('First check', required=True),
        'last_check': fields.integer('Last check', required=True),
        'company_id':fields.related('bank_acc_id','company_id', type='many2one', relation='res.company', string='Company', store=False, readonly=True),
        'currency_id':fields.related('bank_acc_id','currency_id', type='many2one', relation='res.currency', string='Currency', store=False, readonly=True),
        'journal_id':fields.related('bank_acc_id','journal_id', type='many2one', relation='account.journal', string='Bank journal', store=False, readonly=True),
        'check_ids':fields.one2many('tcv.bank.checks','checkbook_id','Checks'),
        'available_qty':fields.function(_calc_check_qty, method=True, type='integer', string='Available', multi='all'),
        'used_qty':fields.function(_calc_check_qty, method=True, type='integer', string='Used', multi='all'),
        }


    _defaults = {
        'name': '/',
        'state': lambda *a: 'inactive',
        }

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', 'The checkbook reference must be unique!'),
        ('number_uniq', 'UNIQUE(number)', 'The checkbook number must be unique!'),
        ('check_number', 'CHECK(first_check<last_check)', 'The fisrt check must be < last check!'),
        ('check_qty', 'CHECK(last_check-first_check < 101)', 'The maximun check quantity allowed is 100!'),
        ]

    ##------------------------------------------------------------------------------------

    def _gen_checkbook_checks(self,cr,uid,ids,context):
        if context is None:
            context = {}
        if not ids:
            return []

        if len(ids) != 1:
            raise osv.except_osv(_('Error!'),_('Multiple operations not allowed (create checks)'))
        so_brw = self.browse(cr,uid,ids,context={})
        res = []
        for chbk in so_brw:
            if not chbk.check_ids:
                checks = map(lambda x: (0,0,{'name':x}),range(chbk.first_check,chbk.last_check+1))
                context.update({'unlock_check_data':True})
                self.write(cr,uid,ids,{'check_ids':checks},context)


    def on_change_check_range(self, cr, uid, ids, first, last):
        res= {'value':{'check_qty':self._check_qty(first, last)}}
        return res


    ##------------------------------------------------------------------------------------ create write unlink


    def create(self, cr, uid, vals, context=None):
        if vals.get('name','/') == '/':
            vals.update({'name':self.pool.get('ir.sequence').get(cr, uid, 'bank.checkbook')})
        return super(tcv_bank_checkbook, self).create(cr, uid, vals, context)


    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        context.update({'delete_form_ckeckbook':True})
        so_brw = self.browse(cr,uid,ids,context={})
        delete_ch_ids = []
        for chbk in so_brw:
            if chbk.state != 'cancel':
                raise osv.except_osv(_('Error!'),_('Can\'t detete a checkbook when state <> "Cancel"'))
            for ch in chbk.check_ids:
                if ch.state != 'available':
                    raise osv.except_osv(_('Error!'),_('Cant\'t delete a checkbook with checks in state <> "available" (%s)')%(chbk.name))
                delete_ch_ids.append(ch.id)
        if delete_ch_ids:
            context.update({'unlock_check_data':True})
            self.pool.get('tcv.bank.checks').unlink(cr,uid,delete_ch_ids,context)
        return super(tcv_bank_checkbook, self).unlink(cr, uid, ids, context)


    ##------------------------------------------------------------------------------------ Workflow

    def button_activate(self, cr, uid, ids, context=None):
        self.write(cr,uid,ids,{'state':'active'},context)
        self._gen_checkbook_checks(cr, uid, ids, context)


tcv_bank_checkbook()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

