# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from osv import osv, fields
import netsvc
import pooler
from tools.translate import _
import decimal_precision as dp
from osv.orm import browse_record, browse_null

class stock_picking(osv.osv):
    
  
    _inherit = 'stock.picking'
    _columns = {
        'state_rw':fields.integer('State'),
        'picking_origin_ids':fields.many2many('stock.picking','picking_intercompany_rel','picking_origin_id','picking_sale_id','Picking'),
        'picking_sale_ids':fields.many2many('stock.picking','picking_intercompany_rel','picking_sale_id','picking_origin_id','Picking'),
    
    }
    
    _defaults = {
        'state_rw':0,
    }
    
    def draft_validate(self, cr, uid, ids, context=None):
        '''
        Added the state chage to can do changes in the picking(INVOICE)
        '''
        if context is None:
            context = {}
        self.write(cr,uid,ids,{'state_rw':0},context=context)
        res = super(stock_picking, self).draft_validate(cr, uid, ids, context)
        
        
        return res
    
    def action_invoice_create(self, cr, uid, ids, journal_id=False,group=False, type='out_invoice', context=None):
        '''
        Method that generate invoices in the companies related with this transaction
        '''
        #~ TODO: Revisar los impuestos en las facturas generadas
        if context is None: 
            context = {}
        stock_partial_picking_obj = self.pool.get('stock.partial.picking')
        stock_invoice_onshiping_obj = self.pool.get('stock.invoice.onshipping')
        self.write(cr,uid,ids,{'state_rw':0},context=context)
        pickng_brw = self.browse(cr,uid,ids,context=context)
        res = super(stock_picking, self).action_invoice_create(cr, uid, ids,journal_id=journal_id,
            group=group, type=type, context=context)


        if context.get('inter',False):
            pass
        else:
            for i in pickng_brw[0].picking_sale_ids:
                if i.id == ids[0]:
                    continue
                else:
                    self.draft_validate(cr,i.company_id.user_in_id.id,[i.id],context)
                    context.update({'inter':True})
                    journal_ids = self.pool.get('account.journal').search(cr,uid,[('company_id','=',i.company_id.id),('type','=','purchase')],context=context)
                    pickng_brw = self.browse(cr,uid,i.id,context=context)
                    if pickng_brw.type == 'in':
                        type = 'in_invoice' 
                    else:
                        type = 'out_invoice' 
                    self.action_invoice_create(cr, i.company_id.user_in_id.id, [i.id],journal_id=journal_ids[0],group=False, type=type, context=context)
        return res


    def write(self, cr, uid, ids, vals, context=None):
        """
        Chages for not write in a picking intercompany
        """
        if context is None:
            context = {}
        ids = isinstance(ids, (int, long)) and [ids] or ids
        picking_brw = self.browse(cr,uid,ids,context=context)
        for val in vals.keys():
            if val == 'state_rw':
                True
            else:
                for i in picking_brw:
                    if i.state_rw !=0 and i.state == 'done':
                        raise osv.except_osv(_('Invalid action !'),_('Cannot write this picking because they are a transactions intercompany !'))
        
        return super(stock_picking, self).write(cr, uid, ids, vals, context=context)
    
    def unlink(self, cr, uid, ids, context=None):
        """
         Modified to avoid delete a line of a picking intercompany
        """
        
        picking_brw = self.browse(cr, uid, ids,context=context)
        unlink_ids = []
        for s in picking_brw:
            if s.state_rw !=0: ## or s.state == 'done' :
                raise osv.except_osv(_('Invalid action !'),_('Cannot delete this picking because they are a transactions intercompany !'))
            else:
                unlink_ids.append((s.id))   
        return super(stock_picking, self).unlink(cr, uid, unlink_ids, context=context)

        
    def copy(self, cr, uid, id, default=None, context=None):
        """
       Modified to avoid doubling a picking intercompany
        
        """
        if not default:
            default = {}
        
        picking_brw = self.browse(cr,uid,id,context=context)
        if picking_brw.state_rw != 0:
            default.update({
                'ref': [],
                'move_ids': [],
                'revisions': [],
                
            })

        return super(stock_picking, self).copy(cr, uid, id, default, context=context)
    
stock_picking()

class stock_move(osv.osv):
    _inherit = 'stock.move'
    
    def action_cancel(self, cr, uid, ids, context=None):
        """ Cancels a stock move generated in the principal company.
        @return: Result: This is a copy of original method
        """
        if not len(ids):
            return True
        if context is None:
            context = {}
        result = super(stock_move, self).action_cancel(cr, uid, ids, context=context)
        
        if context.get('dont cancel',False):
            pass
        else:
            
            move_brw = self.browse(cr,uid,ids[0],context=context)
            if move_brw.prodlot_id.stock_move_id:
                context.update({'dont cancel':1})
                self.action_cancel(cr, uid, [move_brw.prodlot_id.stock_move_id.id], context=context)
            
        return result
        
   
stock_move()
