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

class stock_move_split(osv.osv_memory):
    
    def create_line(cr,uid,ids,context=None):
        split_line = self.pool.get('stock.move.split.lines')
        split_line_exist = self.pool.get('stock.move.split.lines.exist')

    def default_get(self, cr, uid, fields, context=None):
        """ Get default values
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param fields: List of fields for default value
        @param context: A standard dictionary
        @return: Default values of fields
        """
        if context is None:
            context = {}
        res = super(stock_move_split, self).default_get(cr, uid, fields, context=context)
        if context.get('active_id',False):
            move = self.pool.get('stock.move').browse(cr, uid, context['active_id'], context=context)
            if 'product_id' in fields:
                res.update({'product_id': move.product_id and move.product_id.id})
            if 'product_uom' in fields:
                res.update({'product_uom': move.product_uom and move.product_uom.id})
            if 'qty' in fields:
                res.update({'qty': move.product_qty})
            if 'use_exist' in fields:
                res.update({'use_exist': (move.picking_id and move.picking_id.type=='out' and True) or False})
            if 'location_id' in fields:
                res.update({'location_id': move.location_id and move.location_id.id})
            res.update({'mov_id':context.get('active_id') })
            
            res.update({'type_picking':move.picking_id.type})
            res.update({'faclot':move and move.id })
            
        return res

    def split(self, cr, uid, ids, move_ids, context=None):
        """ To split stock moves into production lot
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param ids: the ID or list of IDs if we want more than one
        @param move_ids: the ID or list of IDs of stock move we want to split
        @param context: A standard dictionary
        @return:
        """
        if context is None:
            context = {}
        inventory_id = context.get('inventory_id', False)
        prodlot_obj = self.pool.get('stock.production.lot')
        inventory_obj = self.pool.get('stock.inventory')
        line_obj = self.pool.get('stock.move.split.lines')
        move_obj = self.pool.get('stock.move')
        new_move = []
        company_id = self.pool.get('res.company')._company_default_get(cr, uid, 'stock.move.split', context=context),
        for data in self.browse(cr, uid, ids, context=context):
            for move in move_obj.browse(cr, uid, move_ids, context=context):
                move_qty = move.product_qty
                quantity_rest = move.product_qty
                uos_qty_rest = move.product_uos_qty
                new_move = []
                if data.use_exist:
                    lines = [l for l in data.line_exist_ids if l]
                else:
                    lines = [l for l in data.line_ids if l]
                total_move_qty = 0.0
                for line in lines:
                    quantity = line.quantity1
                    total_move_qty += quantity
                    diff = round(total_move_qty - move_qty,4)
                    if diff > 0:
                        raise osv.except_osv(_('Processing Error'), _('Processing quantity %f for %s is larger than the available quantity %f!')\
                                     %(total_move_qty, move.product_id.name, move_qty))
                    if quantity <= 0 or move_qty == 0:
                        continue
                    
                    quantity_rest = round(quantity_rest-quantity,4)
                    uos_qty = quantity / move_qty * move.product_uos_qty
                    uos_qty_rest = quantity_rest / move_qty * move.product_uos_qty
                    if quantity_rest < 0:
                        quantity_rest = quantity
                        break
                    default_val = {
                        'product_qty': quantity,
                        'product_uos_qty': uos_qty,
                        'pieces_qty': line.pieces_qty,
                        'state': move.state
                    }
                      
                    if quantity_rest > 0:
                        current_move = move_obj.copy(cr, uid, move.id, default_val, context=context)
                        if inventory_id and current_move:
                            inventory_obj.write(cr, uid, inventory_id, {'move_ids': [(4, current_move)]}, context=context)
                        new_move.append(current_move)
                    if quantity_rest == 0:
                        current_move = move.id
                    prodlot_id = False
                    if data.use_exist:
                        prodlot_id = line.prodlot_id.id
                    if not prodlot_id:
                        
                        if line.length1 and line.heigth1:
                            
                            prodlot_id = prodlot_obj.create(cr, uid, {
                                'name': line.name,
                                'product_id': move.product_id and move.product_id.id,
                                'length':line.length1,
                                'width':line.width1,
                                'heigth':line.heigth1,
                                'company_id':company_id[0]
                                },
                            context=context)
                        
                        if line.length and line.heigth:
                            prodlot_id = prodlot_obj.create(cr, uid, {
                                'name': line.name,
                                'product_id': move.product_id and move.product_id.id,
                                'length':line.length,
                                'width':line.width,
                                'heigth':line.heigth,
                                'company_id':company_id[0]
                                },
                            context=context)
                    move_obj.write(cr, uid, [current_move], {'prodlot_id': prodlot_id, 'state':move.state})
                 
                    update_val = {}
                    if quantity_rest > 0:
                        update_val['product_qty'] = quantity_rest
                        update_val['product_uos_qty'] = uos_qty_rest
                        update_val['state'] = move.state
                        update_val['pieces_qty'] = line.pieces_qty
                        move_obj.write(cr, uid, [move.id], update_val)
        return new_move

    def  on_change_quantity_sum(self, cr, uid, ids,line_id,move_id, context=None):
        if context is None: context={}
        res ={'value':{}}
        move_obj = self.pool.get('stock.move')
        move_brw = move_obj.browse(cr, uid, move_id, context=context)
        total = 0
       
        for i in line_id:
            total = total + round(i[2]['quantity'],4)
            diff = round(move_brw.product_qty,4) - total
            res = {'value':{'total_quantity':total,'available': diff}}
            if diff < 0:
                 raise osv.except_osv(_('Processing Error'), _('Processing quantity is larger than the available quantity!'))
        return res 
            
    def split_lot(self, cr, uid, ids, context=None):
        """ To split a lot
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param ids: An ID or list of IDs if we want more than one
        @param context: A standard dictionary
        @return:
        """
        if context is None:
            context = {}
        self.split(cr, uid, ids, context.get('active_ids'), context=context)
        return {'type': 'ir.actions.act_window_close'}  
    
    _inherit = "stock.move.split"

    _columns = {
        'factor':fields.integer('Factor',help="This field define the field in readonly"),
        'lot':fields.integer('Integer'),
        'mov_id':fields.integer('mov_id'),
        'total_quantity':fields.float("Total Quantity", digits_compute=dp.get_precision('Product UoM'),help="Total of quantity selected"),
        'qty':fields.float("Quantity", digits_compute=dp.get_precision('Product UoM'),help=""),
        'available':fields.float("Available",digits_compute=dp.get_precision('Product UoM'), help="Total of quantity available"),
        'length': fields.float('Length (m)',digits_compute=dp.get_precision('Extra UOM data')),
        'heigth': fields.float('Heigth (m)',digits_compute=dp.get_precision('Extra UOM data')),
        'width': fields.float('Width (m)',digits_compute=dp.get_precision('Extra UOM data')),
        'pieces_qty': fields.integer('Pieces'),
        'faclot': fields.integer('Production Lot'),
        'type_picking':fields.selection([('out', 'Sending Goods'), ('in', 'Getting Goods'), ('internal', 'Internal')], 'Shipping Type', required=True, select=True),
}
    
stock_move_split()

class stock_move_split_lines(osv.osv_memory):
   
    def default_get(self,cr,uid,fields,context=None):
        if context is None:
            context = {}
        res = super(stock_move_split_lines, self).default_get(cr, uid, fields, context=context)
        if context.get('line_ids',False):
            for i in context['line_ids']:
                if i[2]['name'].isdigit():
                    res.update({'name':int(i[2]['name'])+1,'length':i[2]['length'],'heigth':i[2]['heigth'],'width':i[2]['width'],'location_id':i[2]['location_id']})
                else:
                    if len(i[2]['name'].split("-")) == 2:
                        if i[2]['name'].split("-")[1].isdigit():
                            name = "%s-%d" %(i[2]['name'].split("-")[0],int(i[2]['name'].split("-")[1])+1)
                            res.update({'name':name,'length':i[2]['length'],'heigth':i[2]['heigth'],'width':i[2]['width'],'location_id':i[2]['location_id']})
                        else: 
                            raise osv.except_osv(_('Processing Error'), _('The name only have string'))
                    else:
                        raise osv.except_osv(_('Processing Error'), _('The name must have only one dash(-)'))
        else:
            return res
        return res
        
    def on_change_compute(self,cr,uid,ids,product_id,available,type_picking,faclot,name,quantity,pieces, length, heigth, width,context=None):
        res = {'value': {}}
        if context is None:
            context = {}
        if name:
            prodlot_obj = self.pool.get('stock.production.lot')
            lots_ids = prodlot_obj.search(cr,uid,[('name','=',name)],context=context)
            if len(lots_ids) > 0 :
                raise osv.except_osv(_('Processing Error'), _('The lot number %s existing')\
                                 %(name))
        if product_id:
            product_obj = self.pool.get('product.product')
            product_brw = product_obj.browse(cr,uid,product_id,context=context)
            if product_brw.stock_driver == 'normal' :
                res['value'].update({'factor': 3})
            if product_brw.stock_driver == 'tile' :
                res['value'].update({'factor': 2})
            if product_brw.stock_driver == 'slab' :
                res['value'].update({'factor': 1})
            if product_brw.stock_driver == 'block' :
                res['value'].update({'factor': 0})
            
            product_obj = self.pool.get('product.uom')
            driver = product_brw.stock_driver
            if pieces == 0:
                if product_brw.stock_driver == 'tile':
                    pieces = product_obj._compute_pieces2(cr, uid,driver, available, length, heigth, width)
                else:
                    pieces = 1
                res['value'].update({'pieces_qty':pieces })
                res['value'].update({'pieces_qty1':pieces })
            area = product_obj._compute_area(cr, uid,driver, pieces, length, heigth, width)
            if type_picking == 'in':
                
                if product_brw.tile_format_id:
                
                    if product_brw.stock_driver == 'tile':
                        res['value'].update({'quantity': area})
                        res['value'].update({'quantity1': area})
                        res['value'].update({'length': product_brw.tile_format_id.length})
                        res['value'].update({'length1': product_brw.tile_format_id.length})
                        res['value'].update({'heigth': product_brw.tile_format_id.heigth})
                        res['value'].update({'heigth1': product_brw.tile_format_id.heigth})
                  
                if product_brw.stock_driver == 'slab':
                    res['value'].update({'quantity': area})
                    res['value'].update({'quantity1': area})
                  
                if product_brw.stock_driver == 'block':
                    
                    res['value'].update({'quantity': area})
                    res['value'].update({'quantity1': area})
                    res['value'].update({'stock_driver': True})
        return res

    _inherit = "stock.move.split.lines"

    _columns = {
        'lote':fields.integer('Lot Number'),
         'stock_driver':fields.boolean('Driver'),
        'factor':fields.integer('Factor',help="This field define the field in readonly"),
        'location_id': fields.many2one('stock.location', 'Source Location'),
        'length': fields.float('Length (m)',digits_compute=dp.get_precision('Extra UOM data')),
        'length1': fields.float('Length (m)',digits_compute=dp.get_precision('Extra UOM data')),
        'heigth': fields.float('Heigth (m)',digits_compute=dp.get_precision('Extra UOM data')),
        'heigth1': fields.float('Heigth (m)',digits_compute=dp.get_precision('Extra UOM data')),
        'width': fields.float('Width (m)',digits_compute=dp.get_precision('Extra UOM data')),
        'width1': fields.float('Width (m)',digits_compute=dp.get_precision('Extra UOM data')),
        'quantity': fields.float('Quantity',digits_compute=dp.get_precision('Product UoM')),
        'quantity1': fields.float('Quantity',digits_compute=dp.get_precision('Product UoM')),
        'pieces_qty': fields.integer('Pieces'),
        'pieces_qty1': fields.integer('Pieces'),
}
  
   
stock_move_split_lines()

class stock_move_split_lines_exist(osv.osv_memory):
    
    def on_change_compute(self,cr,uid,ids,product_id,type_picking,prodlot,quantity,pieces,length, heigth, width,context=None):
        res = {'value': {}}
        if not context:
            context = {}
        if product_id:
            product_obj = self.pool.get('product.product')
            product_brw = product_obj.browse(cr,uid,product_id,context=context)
            lot_obj = self.pool.get('stock.production.lot')
            if prodlot:
                lot_brw = lot_obj.browse(cr,uid,prodlot,context=context)
            if product_brw.stock_driver == 'normal' :
                res['value'].update({'factor': 3})
            if product_brw.stock_driver == 'tile' :
                res['value'].update({'factor': 2})
            if product_brw.stock_driver == 'slab' :
                res['value'].update({'factor': 1})
            if product_brw.stock_driver == 'block' :
                res['value'].update({'factor': 0})
            
            driver = product_brw.stock_driver
            product_obj = self.pool.get('product.uom')
            area = product_obj._compute_area(cr, uid,driver, pieces, length, heigth,width)
            if prodlot:
                lot_brw = lot_obj.browse(cr,uid,prodlot,context=context)
                if type_picking == 'out':
                    if product_brw.stock_driver == 'tile':
                        res['value'].update({'quantity': product_brw.virtual_available})
                        res['value'].update({'quantity1': product_brw.virtual_available})
                        res['value'].update({'pieces_qty': ((product_brw.virtual_available)/(lot_brw.lot_factor))})
                        res['value'].update({'pieces_qty1': ((product_brw.virtual_available)/(lot_brw.lot_factor))})
                        res['value'].update({'length': (lot_brw.length)})
                        res['value'].update({'length1': (lot_brw.length)})
                        res['value'].update({'heigth': (lot_brw.heigth)})
                        res['value'].update({'heigth1': (lot_brw.heigth)})
                    
                    if product_brw.stock_driver == 'slab':
                        res['value'].update({'quantity': product_brw.virtual_available})
                        res['value'].update({'quantity1': product_brw.virtual_available})
                        res['value'].update({'length': (lot_brw.length)})
                        res['value'].update({'length1': (lot_brw.length)})
                        res['value'].update({'heigth': (lot_brw.heigth)})
                        res['value'].update({'heigth1': (lot_brw.heigth)})
                
                    if product_brw.stock_driver == 'block':
                        res['value'].update({'quantity': product_brw.virtual_available})
                        res['value'].update({'length': lot_brw.length})
                        res['value'].update({'length1': lot_brw.length})
                        res['value'].update({'heigth': lot_brw.heigth})
                        res['value'].update({'heigth1': lot_brw.heigth})
                        res['value'].update({'width': lot_brw.width})
                        res['value'].update({'width1': lot_brw.width})
        return res
    
    _inherit = "stock.move.split.lines.exist"
    
    _columns = {
        'factor':fields.integer('Factor',help="This field define the field in readonly"),
        'length': fields.float('Length (m)',digits_compute=dp.get_precision('Extra UOM data')),
        'length1': fields.float('Length (m)',digits_compute=dp.get_precision('Extra UOM data')),
        'heigth': fields.float('Heigth (m)',digits_compute=dp.get_precision('Extra UOM data')),
        'heigth1': fields.float('Heigth (m)',digits_compute=dp.get_precision('Extra UOM data')),
        'width': fields.float('Width (m)',digits_compute=dp.get_precision('Extra UOM data')),
        'width1': fields.float('Width (m)',digits_compute=dp.get_precision('Extra UOM data')),
        'quantity': fields.float('Quantity'),
        'quantity1': fields.float('Quantity'),
        'pieces_qty': fields.integer('Pieces'),
        'pieces_qty1': fields.integer('Pieces'),
        'location_id': fields.many2one('stock.location', 'Source Location'),
        'lote':fields.integer('Lot Number'),
}
stock_move_split_lines_exist()   

class change_stock_move(osv.osv_memory):
   
    def default_get(self, cr, uid, fields, context=None):
        """ Get default values
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param fields: List of fields for default value
        @param context: A standard dictionary
        @return: Default values of fields
        """
        if context is None:
            context = {}
        res = super(change_stock_move, self).default_get(cr, uid, fields, context=context)
        if context.get('active_id'):
            move = self.pool.get('stock.move').browse(cr, uid, context['active_id'], context=context)
            
        if 'quantity' in fields:
            res.update({'quantity':move.product_qty })
        if 'mov_id' in fields:
            res.update({'mov_id': move.id})
            
        return res
    
    def new_quantity(self, cr, uid, ids, context=None):
        """ To split a lot
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param ids: An ID or list of IDs if we want more than one
        @param context: A standard dictionary
        @return:
        """
        if context is None:
            context = {}
        self.new(cr, uid, ids, context=context)
        return {'type': 'ir.actions.act_window_close'}  
    
    def new(self,cr,uid,ids,context=None):
        if context is None:
            context={}
      
        new_brw = self.browse(cr,uid,ids,context)[0]
        stock_obj = self.pool.get('stock.move')
        stock_obj.write(cr,uid,new_brw.mov_id,{'product_qty':new_brw.newquantity},context=None)
        
        context.update({'qty':new_brw.newquantity})
  
    _name ='change.stock.move'
    
    _columns = {
    'quantity': fields.float('Quantity',digits_compute=dp.get_precision('Product UoM')),
    'newquantity': fields.float('New Quantity',digits_compute=dp.get_precision('Product UoM')),
    'mov_id': fields.integer('mov_id'),
    
    }
change_stock_move() 
