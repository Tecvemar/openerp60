# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Gabriel Gamez
#    Creation Date: 
#    Version: 0.0.0.0
#
#    Description:
#
#
##############################################################################
from datetime import datetime
from osv import fields,osv
from tools.translate import _
import pooler
import decimal_precision as dp
import time


class tcv_calculator(osv.osv_memory):
    
    _name = 'tcv.calculator'
    
    _description = ''
    
    
    def on_change_tile_area(self, cr, uid, ids, pieces_qty, tile_format_id):
        #~ res = {'value':{'run_time':self._compute_run_time(cr,uid,ids,date_start, date_end)}}
        res={'value':{'lot_factor':0}}
        if tile_format_id:
            pieces_qty = pieces_qty or 0
            brw_obj = self.pool.get('product.product.tile.format')
            uom_obj = self.pool.get('product.uom')
            tile=brw_obj.browse(cr, uid, tile_format_id, context=None)
            area=uom_obj._compute_area_tile(cr, uid, pieces_qty, tile.length, tile.heigth, context=None)
            res = {'value':{'lot_factor':area,'area':area,'tile_format_id2':tile_format_id}}
        return res
        
    def on_change_tile_area2(self, cr, uid, ids, area, tile_format_id):
        res={'value':{'lot_factor':0}}
        if tile_format_id:
            area = area or 0
            brw_obj = self.pool.get('product.product.tile.format')
            uom_obj = self.pool.get('product.uom')
            tile=brw_obj.browse(cr, uid, tile_format_id, context=None)
            pieces=uom_obj._compute_pieces(cr, uid, 'tile', area, tile.factile, context=None)
            res = self.on_change_tile_area(cr, uid, ids, pieces, tile_format_id)
            res['value'].update({'pieces_qty2':pieces,'pieces_qty':pieces,'tile_format_id':tile_format_id})
            res['value'].pop('tile_format_id2')
            res['value'].pop('area')
        return res
    
    def on_change_slab(self, cr, uid, ids, length, heigth):
        res={}
        if length and heigth:
            uom_obj = self.pool.get('product.uom')
            area=uom_obj._compute_area_slab(cr, uid, 1, length, heigth, context=None)
            res = {'value':{'lot_factor':area}}
        return res
    
    
    def _calc_lot_factor(self, cr, uid, ids, name, arg, context=None):
        if context is None:
            context = {}
        if not len(ids):
            return []            
        res = {}
        for id in ids:
            # creates a UOM model to calculate lot factor
            r_brw = self.browse(cr, uid, id, context)    
            res[id] = self._calc_lot_area(r_brw.length, r_brw.heigth, r_brw.width)
#            obj_uom = self.pool.get('product.uom')
#            r = self.read(cr, uid, id, ['length','heigth','width'], context)    
#            res[id] = obj_uom._calc_area(r['length'],r['heigth'])
#            if r['width']:
#                res[id] = obj_uom._calc_area(res[id],r['width'])           
        return res
    
    
    _columns = {
        'length': fields.float('Length (m)', digits_compute=dp.get_precision('Extra UOM data')),
        'heigth': fields.float('Heigth (m)', digits_compute=dp.get_precision('Extra UOM data')),
        'pieces_qty': fields.integer('Pieces Quantity'),
        'tile_format_id': fields.many2one('product.product.tile.format', 'Tile format'),
        'pieces_qty2': fields.integer('Pieces Quantity'),
        'tile_format_id2': fields.many2one('product.product.tile.format', 'Tile format'),
        'lot_factor': fields.float('Total Area (m2)', digits_compute=dp.get_precision('Product UoM'), readonly=True),
        'area': fields.float('Area (m2)', digits_compute=dp.get_precision('Product UoM')),

    }
    
    _defaults = {
        'pieces_qty': 1,
    }
tcv_calculator()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
