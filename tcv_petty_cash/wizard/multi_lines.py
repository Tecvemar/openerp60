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

#~ from datetime import datetime
from osv import fields, osv
#~ from tools.translate import _
#~ import pooler
import decimal_precision as dp
#~ import time


class tcv_petty_cash_refund_multi_lines(osv.osv_memory):
    _name = "tcv.petty.cash.refund.multi.lines"
    _description = "Add multiple account moves in single step"

    def default_get(self, cr, uid, fields, context=None):

        data = super(tcv_petty_cash_refund_multi_lines, self).\
            default_get(cr, uid, fields, context)
        if context.get('default_petty_cash_id'):
            r = self.on_change_petty_cash_id(cr, uid, [],
                                             context['default_petty_cash_id'],
                                             context)
        return data

    _columns = {
        'name': fields.char('name', size=64, required=False, readonly=False ),
        'petty_cash_id':fields.many2one('tcv.petty.cash.config.detail', 'Petty cash', required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'rel_journal':fields.related('petty_cash_id','journal_id', type='many2one', relation='account.journal', string='Journal name',store=False, readonly=True),
        'multi_move_ids':fields.one2many('tcv.petty.cash.refund.multi.lines.detail','multi_id','Details'),

    }

    def on_change_petty_cash_id(self, cr, uid, ids, petty_cash_id, context):
        res = {}
        if petty_cash_id:
            org = self.pool.get('tcv.petty.cash.config.detail').browse(cr,uid,petty_cash_id,context=None)
            obj_move = self.pool.get('account.move.line')
            #~ obj_multi = self.pool.get('tcv.petty.cash.refund.multi.lines')
            obj_rfd = self.pool.get('tcv.petty.cash.refund')
            if context.get('active_id'):
                rfd = obj_rfd.browse(cr,uid,context['active_id'],context=context)
                lines_loaded = []
                for l in rfd.line_ids:
                    lines_loaded.append(l.move_line.id)
            multi_move_ids = obj_move.search(
                cr, uid,
                [('journal_id', '=', org.journal_id.id),
                 ('credit', '>', 0),
                 ('reconcile_id', '=', 0),
                 ('account_id', '=', org.journal_id.default_credit_account_id.id)],
                context=None)
            moves = obj_move.browse(cr, uid, multi_move_ids, context=None);
            lines = []
            for m in moves:
                if m.id not in lines_loaded and m.move_id.state == 'posted':
                    new_det = {'selected': False,
                               'move_id': m.id,
                               'move': m.ref,
                               'name': m.name,
                               'date': m.date,
                               'partner_id': m.partner_id.id,
                               'amount': m.credit,
                               }
                    lines.append(new_det)
            res = {'value': {'rel_journal': org.journal_id.id,
                             'multi_move_ids': lines,
                             }}
        return res


    def move_assigned(self,cr,uid,ids,all_moves=False,context=None):
        """
        generate sale lines of lot selected
        """
        #~ vals={}
        if context is None:
            context = {}
        multi_brw = self.browse(cr,uid,ids,context=context)[0]
        so_obj = self.pool.get('tcv.petty.cash.refund')
        #~ so_l_obj = self.pool.get('tcv.petty.cash.refund.line')
        rfd_line = []
        if context.get('active_id',False):
            rfd_id = context['active_id']
            #~ so_brw = so_obj.browse(cr,uid,rfd_id,context=context)
            for line in multi_brw.multi_move_ids:
                if all_moves or line.selected:
                    rfd_line.append((0,0,{'petty_cash_id':multi_brw.petty_cash_id.id,
                                         'move_line':line.move_id.id,
                                         'amount':line.move_id.credit,
                    }))
            upd_rfd = {'line_ids':rfd_line}
            so_obj.write(cr,uid,rfd_id,upd_rfd,context=context)
        return True


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


tcv_petty_cash_refund_multi_lines()


class tcv_petty_cash_refund_multi_lines_detail(osv.osv_memory):
    _name = "tcv.petty.cash.refund.multi.lines.detail"
    _description = "Add multiple account moves in single step"

    _columns = {
        'selected': fields.boolean('Select',required=True),
        'multi_id':fields.many2one('tcv.petty.cash.refund.multi.lines', 'Move lines', required=True),
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

tcv_petty_cash_refund_multi_lines_detail()
