# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

from osv import fields, osv
import decimal_precision as dp
from tools.translate import _
import time

class transaction_sale_intercompany(osv.osv_memory):
    '''
    Wizard for add lots to  a sale order registred from a acropolis 
    meet the demand for the product requested, using the quantity of lots that are necessary
    and attach the line of each purchase order
    '''
    _name = 'transaction.sale.intercompany'
    _description = "Lines of a Purchase Order"
    
    def default_get(self, cr, uid, fields, context=None):
        """ Get default values
        @param fields: List of fields for default value
        """
        if context is None:
            context = {}
        res = super(transaction_sale_intercompany, self).default_get(cr, uid, fields, context=context)
        if context.get('active_id'):
            sale_line_brw = self.pool.get('sale.order.line').browse(cr, uid, context['active_id'], context=context)
            if context['active_model'] == 'sale.order.line':
                if 'product_id' in fields:
                    res.update({'product_id': sale_line_brw.purchase_order_line_id.product_id and sale_line_brw.purchase_order_line_id.product_id.id })
                if 'qty' in fields:
                    res.update({'qty': sale_line_brw.purchase_order_line_id.product_qty})
                    res.update({'vals': False})
                
            else:
                res.update({'vals': True})
            #~ if 'purchase_line_id' in fields:
                #~ name = sale_line_brw.purchase_order_line_id.order_id.name
                #~ res.update({'purchase_line_id': name})
            
        return res
    
    _columns = {
        'product_id':fields.many2one('product.product','Product'),
        'qty':fields.float('Quantity',digits_compute=dp.get_precision('Product UoM'),help="Quantity requiered for the Acropolis"),
        'qty_total':fields.float('Total Quantity',digits_compute=dp.get_precision('Product UoM'),help="Quantity sum of lots"),
        'qty_res':fields.float('Total Remaining ',digits_compute=dp.get_precision('Product UoM'),help="Quantity Remaining for fulfill the quantity"),
        'purchase_line_id':fields.many2one('purchase.order.line','Purchase Line'),
        'sale_order_line_id':fields.one2many('transaction.sale.description','sale_line_id','Sale Lines'),
        'vals':fields.integer('Invisible'),
   }
   
   
    def onchange_quantity_sum(self,cr,uid,ids,lines,qty,context=None):
        """ Get default values of the lot selected and compute quantity for the pieces number
        @param lines = lines get created in the m2o to calculate the sum of the amounts, to fulfill the purchase order
        """
        if context is None:
            context = {}
        total = 0
        res = {'value':{}}
        for line in lines:
            total = total + round(line[2]['quantity'],4)
            diff = round(qty - total,4)
            if diff < 0 :
                diff = 0 
            res = {'value':{'qty_total':total,'qty_res':diff}}
        return res 
    
    def create_transaction(self, cr, uid, ids, context=None):
        """ To transaction 
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param ids: An ID or list of IDs if we want more than one
        @param context: A standard dictionary
        @return:
        """
        if context is None:
            context = {}
        self.create_now(cr, uid, ids, context=context)
        return {'type': 'ir.actions.act_window_close'}  
    
    def generate_lot(self,cr,uid,ids,context=None):
        """ To transaction 
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param ids: An ID or list of IDs if we want more than one
        @param context: A standard dictionary
        @return:
        """
        if context is None:
            context = {}
        self.lot_assigned(cr, uid, ids, context=context)
        return {'type': 'ir.actions.act_window_close'}
    
    def lot_assigned(self,cr,uid,ids,context=None):
        """
        generate sale lines of lot selected
        """
        vals={}
        if context is None:
            context = {}
        trans_brw = self.browse(cr,uid,ids,context=context)
        so_l_obj = self.pool.get('sale.order.line')
        so_obj = self.pool.get('sale.order')
        product_obj = self.pool.get('product.uom')
        lot_obj = self.pool.get('stock.production.lot')
        so_line = []
        if context['active_ids']:
            so_brw = so_obj.browse(cr,uid,context['active_ids'][0],context=context)
            for i in trans_brw:
                for line in i.sale_order_line_id:
                    lot_brw = lot_obj.browse(cr,uid,line.lot_id.id,context=context)
                    res = so_l_obj.product_id_change( cr, uid, ids, so_brw.pricelist_id.id, lot_brw.product_id.id, qty=line.quantity1,
                    uom=False, qty_uos=0, uos=False, name='', partner_id=so_brw.partner_id.id,
                    lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False)
                    
                    so_line.append((0,0,{'product_id':lot_brw.product_id and lot_brw.product_id.id,
                                         'prod_lot_id':lot_brw and lot_brw.id,
                                         'pieces':line.pieces_qty,
                                         'product_uom_qty':line.quantity1,
                                         'product_uom':lot_brw.product_id.uom_id and lot_brw.product_id.uom_id.id,
                                         'name':lot_brw.product_id and lot_brw.product_id.name,
                                         'price_unit':res.values()[2]['price_unit'],
                                         'delay':res.values()[2]['delay'],
                                         'type':res.values()[2]['type'],
                    }))
            so_obj.write(cr,uid,context['active_ids'],{'order_line':so_line},context=context)
                
    def create_now(self,cr,uid,ids,context=None):
        """
        Create a transaction intercompany, confirm sale order from a purchase order
        """
        vals={}
        if context is None:
            context = {}
        trans_brw = self.browse(cr,uid,ids,context=context)
        so_l_obj = self.pool.get('sale.order.line')
        product_obj = self.pool.get('product.uom')
        if context['active_ids']:
            so_l_brw = so_l_obj.browse(cr,uid,context['active_ids'][0],context=context)
            sale_quantity = so_l_brw.product_uom_qty
            for i in trans_brw:
                for line in i.sale_order_line_id:
                    quantity = line.quantity1
                    diff = round(sale_quantity - quantity,4)
                    if diff > 0:
                        if line.length1 and line.heigth1:
                            vals = {
                            'prod_lot_id':line.lot_id and line.lot_id.id,
                            'pieces':line.pieces_qty,
                            'product_uom_qty':quantity,
                            }
                        
                        sale_quantity = diff
                        current_move = so_l_obj.copy(cr, uid,context['active_ids'][0] , vals, context=context)
                    
                    if diff == 0 or diff < 0:
                        vals = {
                        'prod_lot_id':line.lot_id and line.lot_id.id,
                        'pieces':line.pieces_qty,
                        'product_uom_qty':line.quantity1,
                        }
                        
                        so_l_obj.write(cr, uid,context['active_ids'][0],vals)
                if diff > 0:
                    if line.length1 and line.heigth1:
                        pieces = product_obj._compute_pieces2(cr, uid,so_l_brw.product_id.stock_driver, diff, line.length1, line.heigth1, line.width1)
                        vals = {
                        'prod_lot_id':False,
                        'pieces': pieces,
                        'product_uom_qty':diff,
                        }
                        so_l_obj.write(cr, uid,context['active_ids'][0],vals)
                  
        return True

transaction_sale_intercompany()

class transaction_sale_description(osv.osv_memory):
    '''
    sale lines for a purchase line
    '''
    
    _name = 'transaction.sale.description'
    _description = "Lines of Sale Order"
    _columns = {
        'length': fields.float('Length (m)',digits_compute=dp.get_precision('Extra UOM data')),
        'length1': fields.float('Length (m)',digits_compute=dp.get_precision('Extra UOM data')),
        'sale_line_id':fields.many2one('transaction.sale.intercompany','Sale Line'),
        'lot_id':fields.many2one('stock.production.lot','Lot Number'),
        'lot_id1':fields.many2one('stock.production.lot','Lots'),
        'company_id':fields.many2one('res.company','Company'),
        'heigth': fields.float('Heigth (m)',digits_compute=dp.get_precision('Extra UOM data')),
        'heigth1': fields.float('Heigth (m)',digits_compute=dp.get_precision('Extra UOM data')),
        'width': fields.float('Width (m)',digits_compute=dp.get_precision('Extra UOM data')),
        'width1': fields.float('Width (m)',digits_compute=dp.get_precision('Extra UOM data')),
        'quantity': fields.float('Quantity',digits_compute=dp.get_precision('Product UoM')),
        'quantity1': fields.float('Quantity',digits_compute=dp.get_precision('Product UoM')),
        'pieces_qty': fields.integer('Pieces'),
        'pieces_qty1': fields.integer('Pieces'),
        'factor':fields.integer('Factor',help="This field define the field in readonly"),
    
    
    }
    
    _defaults = {
        'company_id': lambda s,cr,uid,c: s.pool.get('res.company')._company_default_get(cr, uid, 'transaction.sale.description', context=c),
    }
    
    def onchange_begin_transaction(self,cr,uid,ids,lot_id,pieces,length,heigth,width,context=None):
        """ Get default values of the lot selected and compute quantity for the pieces number
        @param lot_id lot ID with which the transaction takes place
        @param pieces Pieces quantity for compute m2 of the purchase order
        @param length along the specified lot for compute a new quantity in m2 required if the lot
        @param heigth along the specified lot for compute a new quantity in m2 required if the lot
        @param width along the specified lot for compute a new quantity in m2 required if the lot
        """
        if context is None:
            context = {}
        res = {'value':{}}
        
        if lot_id:
            
            lot_obj = self.pool.get('stock.production.lot')
            product_obj = self.pool.get('product.uom')
            lot_brw = lot_obj.browse(cr,uid,lot_id,context=context)
            area = lot_brw.virtual
            
            if lot_brw.product_id.stock_driver == 'normal' :
                res['value'].update({'factor': 3})
            if lot_brw.product_id.stock_driver == 'tile' :
                res['value'].update({'factor': 2})
            if lot_brw.product_id.stock_driver == 'slab' :
                res['value'].update({'factor': 1})
            if lot_brw.product_id.stock_driver == 'block' :
                res['value'].update({'factor': 0})
           
            res['value'].update({'length':lot_brw.length})
            res['value'].update({'length1':lot_brw.length})
            res['value'].update({'heigth':lot_brw.heigth})
            res['value'].update({'heigth1':lot_brw.heigth})
            res['value'].update({'width':lot_brw.width})
            res['value'].update({'width1':lot_brw.width})
            
            if lot_brw.product_id.stock_driver == 'tile' :
                if pieces == False:
                    pieces = product_obj._compute_pieces2(cr, uid,lot_brw.product_id.stock_driver, lot_brw.virtual, lot_brw.length, lot_brw.heigth, lot_brw.width)
                else:
                    area = product_obj._compute_area(cr, uid,lot_brw.product_id.stock_driver, pieces, lot_brw.length, lot_brw.heigth, lot_brw.width)
                res['value'].update({'length':lot_brw.length})
                res['value'].update({'length1':lot_brw.length})
                res['value'].update({'heigth':lot_brw.heigth})
                res['value'].update({'heigth1':lot_brw.heigth})
                res['value'].update({'width':lot_brw.width})
                res['value'].update({'width1':lot_brw.width})
                res['value'].update({'pieces_qty':pieces})
                res['value'].update({'pieces_qty1':pieces})
                res['value'].update({'quantity':area})
                res['value'].update({'quantity1':area})

            if lot_brw.product_id.stock_driver in ('slab','block'):
                pieces = 1
                area = product_obj._compute_area(cr, uid,lot_brw.product_id.stock_driver, pieces,length,heigth,width)
                res['value'].update({'quantity': area})
                res['value'].update({'quantity1': area})
            
            if lot_brw.virtual == 0:
                raise osv.except_osv(_('Processing Error'), _('The lot specified is not available in the stock')\
                                     )    
            return res
transaction_sale_description()
    
