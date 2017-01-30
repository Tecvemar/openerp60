# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2014-05-09
#    Version: 0.0.0.1
#
#    Description:
#
#
##############################################################################

#~ from datetime import datetime
from osv import osv
#~ from tools.translate import _
#~ import pooler
#~ import decimal_precision as dp
#~ import time
#~ import netsvc

##-------------------------------------------------------------- tcv_bank_moves


class tcv_bank_moves(osv.osv):

    _inherit = 'tcv.bank.moves'

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def _gen_account_move(self, cr, uid, ids, context=None):
        move_id = super(tcv_bank_moves, self)._gen_account_move(
            cr, uid, ids, context)
        obj_igtf = self.pool.get('tcv.igtf')
        obj_mov = self.pool.get('account.move')
        mov_brw = obj_mov.browse(cr, uid, move_id, context=context)
        for item in self.browse(cr, uid, ids, context={}):
            if item.type in ('transfer', 'dbn'):
                if not (item.type == 'transfer' and
                        item.partner_id.id == item.company_id.partner_id.id):
                    igtf_ids = obj_igtf.search(
                        cr, uid, [('date_start', '<=', item.date),
                                  ('date_end', '>=', item.date)])
                    igtfs = obj_igtf.browse(cr, uid, igtf_ids, context=context)
                    for igtf in igtfs:
                        for acc_move_line in mov_brw.line_id:
                            if obj_igtf.apply_igtf(cr, uid, ids, acc_move_line,
                                                   igtf, context):
                                move_lines = obj_igtf.gen_account_move_line(
                                    cr, uid, ids, acc_move_line, igtf, context)
                                data = [(0, 0, x) for x in move_lines]
                                obj_mov.button_cancel(
                                    cr, uid, [move_id], context)
                                obj_mov.write(
                                    cr, uid, [move_id], {'line_id': data},
                                    context=context)
                                obj_mov.button_validate(
                                    cr, uid, [move_id], context)
        return move_id

    ##--------------------------------------------------------- function fields

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow


tcv_bank_moves()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
