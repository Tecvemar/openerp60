# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date: 14/08/2012
#    Version: 0.0.0.0
#
#    Description: Account voucher extension
#
#
##############################################################################
from osv import fields,osv


class account_voucher(osv.osv):

    _inherit = 'account.voucher'

    ##------------------------------------------------------------------------------------ on_change...
        
    ##------------------------------------------------------------------------------------ 

    ##------------------------------------------------------------------------------------ create write unlink   
    
    ##------------------------------------------------------------------------------------ Workflow
    
    def proforma_voucher(self, cr, uid, ids, context=None):
        return super(account_voucher, self).proforma_voucher(cr, uid, ids, context)
    
    
    def cancel_voucher(self, cr, uid, ids, context=None):
        return super(account_voucher, self).cancel_voucher(cr, uid, ids, context)
        

    def cancel_to_draft(self, cr, uid, ids, context=None):
        return self.write(cr,uid,ids,{'state':'draft'},context)


    def test_draft(self, cr, uid, ids, *args):
        return True


    def test_done(self, cr, uid, ids, *args):
        return True


    def test_cancel(self, cr, uid, ids, *args):
        return True

account_voucher()
