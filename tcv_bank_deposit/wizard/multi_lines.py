# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description:
#       Wizard to import multime account moves
#
##############################################################################

from datetime import datetime
from osv import fields,osv
from tools.translate import _
import pooler
import decimal_precision as dp
import time


class tcv_bank_deposit_multi_lines(osv.osv_memory):
    _name = "tcv.bank.deposit.multi.lines"
    _description = "Add multiple account moves in single step"

    _columns = {
        'name': fields.char('name', size=64, required=False, readonly=False ),
        'origin':fields.many2one('tcv.bank.config.detail', 'Origin', required=True),
        'rel_journal':fields.related('origin','journal_id', type='many2one', relation='account.journal', string='Journal name',store=False, readonly=True),
        'multi_move_ids':fields.one2many('tcv.bank.deposit.multi.lines.detail','multi_id','Details'),

    }

    def on_change_origin(self, cr, uid, ids, origin, context):
        if origin:
            org = self.pool.get('tcv.bank.config.detail').browse(cr,uid,origin,context=None)
            obj_move = self.pool.get('account.move.line')
            obj_multi = self.pool.get('tcv.bank.deposit.multi.lines')
            obj_dp = self.pool.get('tcv.bank.deposit')
            if context.get('active_id'):
                dp = obj_dp.browse(cr,uid,context['active_id'],context=context)
                lines_loaded = []
                for l in dp.line_ids:
                    lines_loaded.append(l.move_line.id)
            multi_move_ids = obj_move.search(cr,uid,[('journal_id','=',org.journal_id.id),('debit','>',0), ('reconcile_id','=', 0)],context=None)
            moves = obj_move.browse(cr,uid,multi_move_ids,context=None);
            lines = []
            for m in moves:
                if m.id not in lines_loaded:
                    new_det = {'selected':False,
                               #~ 'line_id':ids[0],
                               'move_id':m.id,
                               'move':m.ref,
                               'name':m.name,
                               #~ 'ref':m.ref,
                               'date':m.date,
                               #~ 'move':m.move_id.name,
                               'partner_id':m.partner_id.id,
                               'amount':m.debit,
                               }
                    lines.append(new_det)
            res= {'value':{'rel_journal':org.journal_id.id,
                           'multi_move_ids':lines,}}
        return res


    def move_assigned(self,cr,uid,ids,all_moves=False,context=None):
        """
        generate sale lines of lot selected
        """
        vals={}
        if context is None:
            context = {}
        multi_brw = self.browse(cr,uid,ids,context=context)[0]
        so_obj = self.pool.get('tcv.bank.deposit')
        so_l_obj = self.pool.get('tcv.bank.deposit.line')
        dp_line = []
        if context.get('active_id',False):
            dp_id = context['active_id']
            so_brw = so_obj.browse(cr,uid,dp_id,context=context)
            for line in multi_brw.multi_move_ids:
                if all_moves or line.selected:
                    dp_line.append((0,0,{'origin':multi_brw.origin.id,
                                         'move_line':line.move_id.id,
                                         'amount':line.move_id.debit,
                    }))
            upd_dp = {'line_ids':dp_line}
            so_obj.write(cr,uid,dp_id,upd_dp,context=context)


    def select_button_click(self, cr, uid, ids, context):
        if context is None:
            context = {}
        self.move_assigned(cr, uid, ids, all_moves=False, context=context)
        return {'type': 'ir.actions.act_window_close'}


    def all_button_click(self, cr, uid, ids, context):
        if context is None:
            context = {}
        self.move_assigned(cr, uid, ids, all_moves=True, context=context)
        return {'type': 'ir.actions.act_window_close'}

tcv_bank_deposit_multi_lines()


class tcv_bank_deposit_multi_lines_detail(osv.osv_memory):
    _name = "tcv.bank.deposit.multi.lines.detail"
    _description = "Add multiple account moves in single step"

    _columns = {
        'selected':fields.boolean('Select',required=True),
        'multi_id':fields.many2one('tcv.bank.deposit.multi.lines', 'Move lines'),
        'move_id':fields.many2one('account.move.line', 'Move_id', required=False),
        'move':fields.char('Move', size=64, required=False, readonly=True),
        'name':fields.char('name', size=64, required=False, readonly=True),
        #~ 'ref':fields.char('Reference', size=64, required=False, readonly=False, store=False ),
        'date': fields.date('Date', required=False, readonly=True),
        #~ 'move':fields.char('Move', size=64, required=False, readonly=False, store=False ),
        'partner_id': fields.many2one('res.partner', 'Partner', readonly=True),
        'amount': fields.float('Amount', digits_compute=dp.get_precision('Account'), required=False, readonly=True),
        'selected_total':fields.float('Sel amount', digits_compute=dp.get_precision('Account'), required=False),
        }

    def on_change_selected(self, cr, uid, ids, selected, amount):
        res= {'value':{'selected_total':not selected or amount}}
        return res

tcv_bank_deposit_multi_lines_detail()
