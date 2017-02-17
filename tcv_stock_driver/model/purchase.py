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
#~ from osv import fields,osv
#~ import decimal_precision as dp
#~ import netsvc
#~ from tools.translate import _
#~ 
#~ 
    #~ 
#~ class purchase_order(osv.osv):
    #~ 
    #~ _inherit = 'purchase.order'
    #~ 
    #~ _columns = {
        #~ 'sale_order_ids':fields.many2many('sale.order','intercompany_rel','purchase_order_id','sales_order_id','Transactions')
    #~ 
    #~ 
    #~ }
    #~ def inv_line_create(self, cr, uid, a, ol):
        #~ data = super(purchase_order, self).inv_line_create(cr, uid, a, ol)
        #~ data[2]['prod_lot_id'] = ol.prod_lot_id and ol.prod_lot_id.id
        #~ data[2]['pieces'] = ol.pieces
        #~ data[2]['track_incoming'] = ol.track_incoming
        #~ return data
        #~ 
        #~ 
    #~ def action_picking_create(self,cr, uid, ids, *args):
        #~ '''
        #~ Added to transfer order_line.prod_lot_id.id to stock_move.prodlot_id
        #~ '''
        #~ picking_id = super(purchase_order, self).action_picking_create(cr, uid, ids, args)
        #~ obj_mov = self.pool.get('stock.move')
        #~ for order in self.browse(cr, uid, ids):
            #~ for order_line in order.order_line: 
                #~ if order_line.prod_lot_id:
                    #~ move_id = obj_mov.search(cr, uid, [('purchase_line_id', '=', order_line.id)])
                    #~ if move_id:
                        #~ updated_data = {'prodlot_id':order_line.prod_lot_id.id,'pieces_qty':order_line.pieces}
                        #~ obj_mov.write(cr,uid,move_id,updated_data)
                #~ 
        #~ return picking_id        
#~ 
        #~ 
#~ purchase_order()     
    
