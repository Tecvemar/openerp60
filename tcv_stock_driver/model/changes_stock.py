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
from osv import fields,osv
import decimal_precision as dp
from tools.translate import _
import time

class descriptions_changes_production_lot_stock(osv.osv):
   
    def default_get(self,cr,uid,ids,fields,context=None):
        if context is None:
            context = {}
        res = {}
        name_change = self.pool.get('ir.sequence').get(cr, uid,'changes.stock.lot')
        res.update({'name_change':name_change})
        res.update({'date':time.strftime('%Y-%m-%d')})
        res.update({'state':'draft'})
        
        return res
    
    def action_confirm(self,cr,uid,ids,context=None):
        """
        Generate picking of IN/OUT for register the new changes in the lots  
        
        """
        print 'descriptions_changes_production_lot_stock.action_confirm'
        changes_brw = self.browse(cr,uid,ids[0],context=None)
        stock_lot_obj = self.pool.get('stock.production.lot')
        stock_move_obj = self.pool.get('stock.move')
        picking_id_in = 0
        picking_id_out = 0
        company_id = self.pool.get('res.company')._company_default_get(cr, uid, 'descriptions.changes.production.lot.stock', context=context),
        for lines in changes_brw.stock_descriptions_id:
            stock_lot_brw = stock_lot_obj.browse(cr,uid,lines.name.id,context=None)
            for move_lines in stock_lot_brw.move_ids:
                if move_lines.location_dest_id.usage == 'internal':
                    location_id = move_lines.location_id and move_lines.location_id.id
                    location_dest_id = move_lines.location_dest_id and move_lines.location_dest_id.id
                    price = move_lines.price_unit
                if move_lines.location_dest_id.usage == 'transit':
                    location_id = move_lines.location_dest_id and move_lines.location_dest_id.id
                    location_dest_id = move_lines.company_id and move_lines.company_id.id
                    price = move_lines.price_unit
            if location_id:
                if lines.name.product_id.stock_driver in ('slab','block'):
                    stock_lot_obj.write(cr,uid,lines.name.id,{'length':lines.new_length,'heigth':lines.new_heigth,'width':lines.new_width,'company_id':company_id[0]},context=None)
                if picking_id_in == 0 or picking_id_out == 0:
                    if lines.diff > 0:
                        pick_name = self.pool.get('ir.sequence').get(cr, uid, 'stock.picking.in')
                        picking_id_in = self.pool.get('stock.picking').create(cr, uid, {
                        'name': pick_name,
                        'type': 'in',
                        'address_id': lines.company_id.partner_id and lines.company_id.partner_id.id ,
                        'invoice_state': 'none',
                        'company_id': lines.company_id and lines.company_id.id,
                    })
                    if lines.diff < 0:
                        pick_name = self.pool.get('ir.sequence').get(cr, uid, 'stock.picking.out')
                        picking_id_out = self.pool.get('stock.picking').create(cr, uid, {
                        'name': pick_name,
                        'type': 'out',
                        'address_id': lines.company_id.partner_id and lines.company_id.partner_id.id ,
                        'invoice_state': 'none',
                        'company_id': lines.company_id and lines.company_id.id,
                    })
                
                if lines.diff > 0:
                    move_id = stock_move_obj.create(cr, uid, {
                    'name':lines.name ,
                    'product_id': lines.name.product_id and lines.name.product_id.id,
                    'product_qty': lines.diff,
                    'product_uos_qty': lines.new_quantity,
                    'product_uom': lines.name.product_id.uom_id and lines.name.product_id.uom_id.id,
                    'product_uos': lines.name.product_id.uos_id and lines.name.product_id.uos_id.id,
                    'date': time.strftime('%Y-%m-%d'),
                    'prodlot_id':lines.name and lines.name.id,
                    'pieces_qty':lines.new_pieces_qty,
                    'date_expected': time.strftime('%Y-%m-%d'),
                    'location_id': lines.name.product_id.property_stock_inventory and lines.name.product_id.property_stock_inventory.id,
                    'location_dest_id': location_dest_id,
                    'picking_id': picking_id_in,
                    'state': 'draft',
                    'company_id': lines.company_id and lines.company_id.id,
                    'price_unit': price
                })
                    self.write(cr,uid,ids[0],{'picking_id_in':picking_id_in},context=None)
                
                
                if lines.diff < 0:
                    res = []
                    diff = lines.diff * -1
                    
                    move_id = stock_move_obj.create(cr, uid, {
                    'name':lines.name ,
                    'product_id': lines.name.product_id and lines.name.product_id.id,
                    'product_qty': lines.diff,
                    'product_uos_qty': lines.new_quantity,
                    'product_uom': lines.name.product_id.uom_id and lines.name.product_id.uom_id.id,
                    'product_uos': lines.name.product_id.uos_id and lines.name.product_id.uos_id.id,
                    'date': time.strftime('%Y-%m-%d'),
                    'prodlot_id':lines.name and lines.name.id,
                    'pieces_qty':lines.new_pieces_qty,
                    'date_expected': time.strftime('%Y-%m-%d'),
                    'location_id': lines.name.product_id.property_stock_inventory and lines.name.product_id.property_stock_inventory.id,
                    'location_dest_id': location_dest_id,
                    'picking_id': picking_id_out,
                    'state': 'draft',
                    'company_id': lines.company_id and lines.company_id.id,
                    'price_unit': price
                })
                    
                    
                    stock_move_obj.write(cr,uid,move_id,{'product_qty':diff},context=context)
                    product_obj = self.pool.get('product.product')
                    stock_move_brw = stock_move_obj.browse(cr,uid,move_id,context=context)
                    move_qty = stock_move_brw.product_qty
                    uos_qty = stock_move_brw.product_qty / move_qty * stock_move_brw.product_uos_qty
                    default_val = {
                        'product_qty': stock_move_brw.product_qty,
                        'product_uos_qty': uos_qty,
                        'state': stock_move_brw.state,
                        'scrapped' : True,
                        'location_id': location_dest_id,
                        'location_dest_id': lines.name.product_id.property_stock_inventory and lines.name.product_id.property_stock_inventory.id, 
                        'tracking_id': stock_move_brw.tracking_id and stock_move_brw.tracking_id.id,
                        'prodlot_id': stock_move_brw.prodlot_id and stock_move_brw.prodlot_id.id,
                    }
                    if stock_move_brw.location_id.usage <> 'internal':
                        default_val.update({'location_id': stock_move_brw.location_dest_id.id})
                    new_move = stock_move_obj.write(cr, uid, stock_move_brw.id, default_val)

                    res += [new_move]

                    for (id, name) in product_obj.name_get(cr, uid, [stock_move_brw.product_id.id]):
                        stock_move_obj.log(cr, uid, stock_move_brw.id, "%s x %s %s" % (stock_move_brw.product_qty, name, _("were scrapped")))
                    self.write(cr,uid,ids[0],{'picking_id_out':picking_id_out},context=None)
                    
                self.write(cr,uid,ids[0],{'state':'confirmed'},context=None)
            else:
                raise osv.except_osv(_('Processing Error'), _('The target location is not internal'))                                     
            
        return True
   
    _name = 'descriptions.changes.production.lot.stock'

    _columns = {
        'name':fields.char('Name',128),
        'name_change':fields.char('Reference',128),
        'date':fields.date('Date'),
        'picking_id_in':fields.many2one('stock.picking','Picking IN'),
        'picking_id_out':fields.many2one('stock.picking','Picking OUT'),
        'state': fields.selection([('draft','Draft'), ('confirmed','Confirmed')], 'State', required=True, readonly=True),
        'stock_descriptions_id':fields.one2many('changes.production.lot.stock', 'description_stock_id', 'Production Lots'),
    }
    
    _defaults = {
    'date':  lambda *a: time.strftime('%Y-%m-%d'),
    'state':'draft'
    }
    
    def copy(self, cr, uid, id, default=None, context=None):
        """
       Modified to avoid doubling a change with other values
        
        """
        if not default:
            default = {}
        default.update({
            'name':False,
            'name_change':False,
            'state': 'draft',
            'date': time.strftime('%Y-%m-%d'),
            'picking_id_in': False,
            'picking_id_out': False,
            'stock_descriptions_id': False,
        })
        return super(descriptions_changes_production_lot_stock, self).copy(cr, uid, id, default, context=context)
    
    def unlink(self, cr, uid, ids, context=None):
        """
       Modified to avoid delete a change confirmed
        
        """
        
        changes_orders = self.browse(cr, uid, ids,context=context)
        unlink_ids = []
        for s in changes_orders:
            if s.state in ('draft'):
                unlink_ids.append(s.id)
            else:
                raise osv.except_osv(_('Invalid action !'), _('Cannot delete this changes which are already confirmed !'))
        return super(descriptions_changes_production_lot_stock, self).unlink(cr, uid, unlink_ids, context=context)
        
descriptions_changes_production_lot_stock()

class changes_production_lot_stock(osv.osv):
    
    def default_get(self,cr,uid,ids,fields,context=None):
        if context is None:
            context = {}
        res = {}
        company_id = self.pool.get('res.company')._company_default_get(cr, uid, 'changes.production.lot.stock', context=context),
        print "company_id",company_id
        res.update({'company_id':company_id[0]})
        
        return res
    
    
    _name = 'changes.production.lot.stock'
    
    _columns = {
        'name':fields.many2one('stock.production.lot','Lot number'),
        'stock_driver':fields.boolean('Driver'),
        'product_id':fields.many2one('product.product','Product'),
        'company_id': fields.many2one('res.company', 'Company', required=True),
        'factor':fields.integer('Factor',help="This field define the field in readonly"),
        'location_id': fields.char('Location',128),
        'length': fields.float('Length (m)',digits_compute=dp.get_precision('Extra UOM data')),
        'heigth': fields.float('Heigth (m)',digits_compute=dp.get_precision('Extra UOM data')),
        'diff': fields.float('Diff',digits_compute=dp.get_precision('Product UoM')),
        'width': fields.float('Width (m)',digits_compute=dp.get_precision('Extra UOM data')),
        'quantity': fields.float('Quantity',digits_compute=dp.get_precision('Product UoM')),
        'pieces_qty': fields.integer('Pieces'),
        'new_location_id': fields.char('New Location',128),
        'new_length': fields.float('New Length (m)',digits_compute=dp.get_precision('Extra UOM data')),
        'new_heigth': fields.float('New Heigth (m)',digits_compute=dp.get_precision('Extra UOM data')),
        'new_width': fields.float(' New Width (m)',digits_compute=dp.get_precision('Extra UOM data')),
        'new_quantity': fields.float('New Quantity',digits_compute=dp.get_precision('Product UoM')),
        'new_pieces_qty': fields.integer('New Pieces'),
        'description_stock_id':fields.many2one('descriptions.changes.production.lot.stock', 'Time Descriptions'),
    }
    _defaults = {
        'company_id': lambda s,cr,uid,c: s.pool.get('res.company')._company_default_get(cr, uid, 'changes.production.lot.stock', context=c),
    }

    def create(self,cr,uid,vals,context=None):
        """
        Create a new register with thes fields reandonly that dot save in the data base
        """
        company_id = self.pool.get('res.company')._company_default_get(cr, uid, 'purchase.order.line', context=context),
        print "valssss",vals
        if vals.get('name',False):
            lot_obj = self.pool.get('stock.production.lot')
            product_obj = self.pool.get('product.uom')
            lot_brw = lot_obj.browse(cr,uid,vals['name'],context=None)
            pieces = product_obj._compute_pieces2(cr,uid,lot_brw.product_id.stock_driver,lot_brw.virtual,lot_brw.length,lot_brw.heigth,lot_brw.width)
            area_old = lot_brw.virtual
            if lot_brw.product_id.stock_driver == 'tile':
                area_new = product_obj._compute_area(cr, uid,lot_brw.product_id.stock_driver, vals['new_pieces_qty'], lot_brw.product_id.tile_format_id.length, lot_brw.product_id.tile_format_id.heigth,lot_brw.width)
                diff = area_new - area_old
                vals.update({'diff':diff,'new_quantity':area_new,'length':lot_brw.product_id.tile_format_id.length,'new_length':lot_brw.product_id.tile_format_id.length,'heigth':lot_brw.product_id.tile_format_id.heigth,'new_heigth':lot_brw.product_id.tile_format_id.heigth,'width':lot_brw.width,'pieces_qty':pieces,'quantity':lot_brw.virtual,'company_id':company_id[0]})

            if lot_brw.product_id.stock_driver == 'slab':
                area_new = product_obj._compute_area(cr, uid,lot_brw.product_id.stock_driver, vals['new_pieces_qty'], vals['new_length'], vals['new_heigth'], lot_brw.width)
                diff = area_new - area_old
                vals.update({'diff':diff,'new_quantity':area_new,'length': vals['new_length'],'heigth':vals['new_heigth'],'width':lot_brw.width,'pieces_qty':pieces,'quantity':lot_brw.virtual,'company_id':company_id[0]})
            
            if lot_brw.product_id.stock_driver == 'block':
                area_new = product_obj._compute_area(cr, uid,lot_brw.product_id.stock_driver, vals['new_pieces_qty'], vals['new_length'], vals['new_heigth'], lot_brw.width)
                diff = area_new - area_old
                vals.update({'diff':diff,'new_quantity':area_new,'length': vals['new_length'],'heigth':vals['new_heigth'],'width':vals['new_width'],'pieces_qty':pieces,'quantity':lot_brw.virtual,'company_id':company_id[0]})
            
        return  super(changes_production_lot_stock, self).create(cr, uid, vals, context)
    
    
    def write(self, cr, uid, ids, vals, context=None):
        """
        Chages for save changes in the field readonly
        """
        if context is None:
            context = {}
        if 'name' in vals:
            lot_obj = self.pool.get('stock.production.lot')
            product_obj = self.pool.get('product.uom')
            lot_brw = lot_obj.browse(cr,uid,vals['name'],context=None)
            pieces = product_obj._compute_pieces2(cr,uid,lot_brw.product_id.stock_driver,lot_brw.virtual,lot_brw.length,lot_brw.heigth,lot_brw.width)
            area_old = lot_brw.virtual
            if lot_brw.product_id.stock_driver == 'tile':
                area_new = product_obj._compute_area(cr, uid,lot_brw.product_id.stock_driver, vals['new_pieces_qty'], lot_brw.product_id.tile_format_id.length, lot_brw.product_id.tile_format_id.heigth,lot_brw.width)
                diff = area_new - area_old
                vals.update({'diff':diff,'new_quantity':area_new,'length':lot_brw.product_id.tile_format_id.length,'new_length':lot_brw.product_id.tile_format_id.length,'heigth':lot_brw.product_id.tile_format_id.heigth,'new_heigth':lot_brw.product_id.tile_format_id.heigth,'width':lot_brw.width,'pieces_qty':pieces,'quantity':lot_brw.virtual,'company_id':company_id[0]})

            if lot_brw.product_id.stock_driver == 'slab':
                area_new = product_obj._compute_area(cr, uid,lot_brw.product_id.stock_driver, vals['new_pieces_qty'], vals['new_length'], vals['new_heigth'], lot_brw.width)
                diff = area_new - area_old
                vals.update({'diff':diff,'new_quantity':area_new,'length': vals['new_length'],'heigth':vals['new_heigth'],'width':lot_brw.width,'pieces_qty':pieces,'quantity':lot_brw.virtual,'company_id':company_id[0]})
            
            if lot_brw.product_id.stock_driver == 'block':
                area_new = product_obj._compute_area(cr, uid,lot_brw.product_id.stock_driver, vals['new_pieces_qty'], vals['new_length'], vals['new_heigth'], lot_brw.width)
                diff = area_new - area_old
                vals.update({'diff':diff,'new_quantity':area_new,'length': vals['new_length'],'heigth':vals['new_heigth'],'width':vals['new_width'],'pieces_qty':pieces,'quantity':lot_brw.virtual,'company_id':company_id[0]})
            
        return super(changes_production_lot_stock, self).write(cr, uid, ids, vals, context=context)
    
    def unlink(self, cr, uid, ids, context=None):
        """
         Modified to avoid delete a line of change confirmed
        
        """
        
        changes_orders = self.browse(cr, uid, ids,context=context)
        unlink_ids = []
        for s in changes_orders:
            if s.description_stock_id.state in ('draft'):
                unlink_ids.append(s.id)
            else:
                raise osv.except_osv(_('Invalid action !'), _('Cannot delete this changes which are already confirmed !'))
        return super(changes_production_lot_stock, self).unink(cr, uid, unlink_ids, context=context)
    
    def onchange_changes_stock(self,cr,uid,ids,name,length,heigth,width,quantity,new_length,new_heigth,new_width,new_pieces_qty,context=None):
        print "ids",ids
        if context is None:
            context = {}
        res = {'value':{}}
        lot_obj = self.pool.get('stock.production.lot')
        stock_move_obj = self.pool.get('stock.move')
        product_obj = self.pool.get('product.uom')
        if name:
            lot_brw = lot_obj.browse(cr,uid,name,context=None)
            area_org =  quantity
            if lot_brw.product_id.stock_driver in ('slab','block'):
                new_pieces_qty = 1
                res['value'].update({'new_pieces_qty':new_pieces_qty})
            area_new = product_obj._compute_area(cr, uid,lot_brw.product_id.stock_driver, new_pieces_qty, new_length, new_heigth, new_width)
            diff =  area_new - area_org
            res['value'].update({'new_quantity':area_new})
            res['value'].update({'diff':diff})
        
        return res
    
    def onchage_default(self,cr,uid,ids,lot_number,context=None):
        """
        @param lot_number id of the lot for add the values by fefault
        """
        if context is None:
            context = {}
        res = {'value':{}}
        lot_obj = self.pool.get('stock.production.lot')
        stock_move_obj = self.pool.get('stock.move')
        product_obj = self.pool.get('product.uom')
        if lot_number:
            lot_brw = lot_obj.browse(cr,uid,lot_number,context=None)
            res['value'].update({'length':lot_brw.length})
            res['value'].update({'heigth':lot_brw.heigth})
            res['value'].update({'width':lot_brw.width})
            res['value'].update({'quantity':lot_brw.virtual})
            res['value'].update({'pieces_qty': product_obj._compute_pieces2(cr,uid,lot_brw.product_id.stock_driver,lot_brw.virtual,lot_brw.length,lot_brw.heigth,lot_brw.width)})
            
            if lot_brw.product_id.stock_driver == 'normal':
                res['value'].update({'factor': 3})
                res['value'].update({'new_length': lot_brw.length})
                res['value'].update({'new_heigth': lot_brw.heigth})
                res['value'].update({'new_width': lot_brw.width})
            
            if lot_brw.product_id.stock_driver == 'tile':
                res['value'].update({'factor': 2})
                res['value'].update({'new_length': lot_brw.product_id.tile_format_id.length})
                res['value'].update({'new_heigth': lot_brw.product_id.tile_format_id.heigth})
                
            if lot_brw.product_id.stock_driver == 'slab':
                res['value'].update({'factor': 1})
                res['value'].update({'new_length': lot_brw.length})
                res['value'].update({'new_heigth': lot_brw.heigth})
                res['value'].update({'new_width': lot_brw.width})
                
            if lot_brw.product_id.stock_driver == 'block':
                res['value'].update({'factor': 0})
                res['value'].update({'new_length': lot_brw.length})
                res['value'].update({'new_heigth': lot_brw.heigth})
                res['value'].update({'new_width': lot_brw.width})
        
       
        
        return res
changes_production_lot_stock()
