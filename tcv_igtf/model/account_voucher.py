# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2014-02-04
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

##------------------------------------------------------------- account_voucher


class account_voucher(osv.osv):

    _inherit = 'account.voucher'

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

    def proforma_voucher(self, cr, uid, ids, context=None):
        res = super(account_voucher, self).proforma_voucher(
            cr, uid, ids, context)
        obj_igtf = self.pool.get('tcv.igtf')
        obj_mov = self.pool.get('account.move')
        for item in self.browse(cr, uid, ids, context={}):
            if item.type == 'payment':
                igtf_ids = obj_igtf.search(
                    cr, uid, [('date_start', '<=', item.date),
                              ('date_end', '>=', item.date)])
                igtfs = obj_igtf.browse(cr, uid, igtf_ids, context=context)
                for igtf in igtfs:
                    for acc_move_line in item.move_ids:
                        if obj_igtf.apply_igtf(cr, uid, ids, acc_move_line,
                                               igtf, context):
                            move_lines = obj_igtf.gen_account_move_line(
                                cr, uid, ids, acc_move_line, igtf, context)
                            data = [(0, 0, x) for x in move_lines]
                            obj_mov.button_cancel(
                                cr, uid, [item.move_id.id], context)
                            obj_mov.write(
                                cr, uid, [item.move_id.id], {'line_id': data},
                                context=context)
                            obj_mov.button_validate(
                                cr, uid, [item.move_id.id], context)
        return res

account_voucher()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
