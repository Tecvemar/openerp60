# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date: 
#    Version: 0.0.0.0
#
#    Description:
#        Se redefine el campo code de account_journal para darle una longitud 
#        de 8 caracteres. Principalmente por los diarios de Tarjeta de débito 
#        y crédito
#
##############################################################################
from osv import fields,osv

class account_journal(osv.osv):
    _inherit = "account.journal"
    _columns = {
        'code': fields.char('Code', size=8, required=True, help="The code will be used to generate the numbers of the journal entries of this journal."),
        'active' : fields.boolean('Active', help="If Active field is set to true, it will allow you to hide the jopurnal without removing it."),
        }
        
    _defaults = {
        'active': True,
    }        
        
account_journal()  


class account_move_reconcile(osv.osv):
    _inherit = "account.move.reconcile"

    def unlink(self, cr, uid, ids, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        obj_move = self.pool.get('account.move.line')
        fld_list = ('reconcile_id','reconcile_partial_id')
        ### Added to "FORCE" set null in reconcile_id and reconcile_partial_id fields of account.move.line model
        ### The ondelete="set null" setting isn't working for this fields
        for f in fld_list:
            rec_ids = obj_move.search(cr, uid, [(f, 'in', ids)])
            if rec_ids:
                obj_move.write(cr, uid, rec_ids, {f:None}, context=context)
        res = super(account_move_reconcile, self).unlink(cr, uid, ids, context)
        return res

account_move_reconcile()      

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
