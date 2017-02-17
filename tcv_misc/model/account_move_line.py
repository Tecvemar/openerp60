# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date: 11/09/2012
#    Version: 0.0.0.0
#
#    Description: Soluciona problemas de redondeo
#
#
##############################################################################
from osv import fields,osv
from tools.translate import _

class account_move_line(osv.osv):
    _inherit = "account.move.line"
    
    #~ _columns = {
        #~ 'reconcile_id': fields.many2one('account.move.reconcile', 'Reconcile', readonly=True, ondelete='set_null', select=2),
        #~ 'reconcile_partial_id': fields.many2one('account.move.reconcile', 'Partial Reconcile', readonly=True, ondelete='set_null', select=2),
        #~ }
    #~ 
    #~ def _amount_residual(self, cr, uid, ids, field_names, args, context=None):
        #~ res = super(account_move_line, self)._amount_residual(cr, uid, ids, field_names, args, context)
        #~ for r in res:
            #~ if abs(r[amount_residual]) < 0.0001: 
                #~ r[amount_residual] = 0.0
            #~ if abs(r[amount_residual_currency]) < 0.0001: 
                #~ r[amount_residual_currency] = 0.0
        #~ return res
        
    def unlink(self, cr, uid, ids, context=None):
        obj_vou = self.pool.get('account.voucher.line')
        move_line_ids = obj_vou.search(cr, uid, [('move_line_id', 'in', ids)])
        if move_line_ids:
            vou_lines = obj_vou.browse(cr,uid,move_line_ids,context=context)
            lst_vous = []
            for v in vou_lines:
                lst_vous.append(v.voucher_id.reference or v.voucher_id.name or v.voucher_id.date)
            vous = ', '.join(lst_vous)
            raise osv.except_osv(_('Error!'),_('Can\'t cancel an invoice while is referenced in payments: %s'%vous))
        res = super(account_move_line, self).unlink(cr, uid, ids, context)
        return res
    

account_move_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
