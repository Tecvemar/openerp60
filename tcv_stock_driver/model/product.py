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
#~ from tools.translate import _
import math



class product_product_features(osv.osv):

    _name = 'product.product.features'

    _columns = {
        'name':fields.char('Name',128,required=True, translate=True),
        'type':fields.selection([('layout','Layout'),('quality','Quality'),('material','Material'),('color','Color'),('finish','Finish')],'Type',  invisible=True,required=True),

    }
    _defaults = {
        'name': lambda *a: None,
        'type': lambda *a: 'layout',
    }


product_product_features()

class product_product_tile_format(osv.osv):
    """
    OpenERP Model : product_product_finish
    """
    def _calc_tile_factor(self, cr, uid, ids, name, arg, context=None):
        if context is None:
            context = {}
        if not len(ids):
            return []
        res = {}
        lot_obj = self.pool.get('stock.production.lot')
        for id in ids:
            # creates a UOM model to calculate lot factor
            r_brw = self.browse(cr, uid, id, context)
            res[id] = lot_obj._calc_lot_area(r_brw.length, r_brw.heigth,False)
#            obj_uom = self.pool.get('product.uom')
#            r = self.read(cr, uid, id, ['length','heigth','width'], context)
#            res[id] = obj_uom._calc_area(r['length'],r['heigth'])
#            if r['width']:
#                res[id] = obj_uom._calc_area(res[id],r['width'])
        return res


    _name = 'product.product.tile.format'
    _description = __doc__

    #~ def get_name(self, cr, uid, ids, name, arg, context=None):
        #~ if context is None:
            #~ context = {}
        #~ if not len(ids):
            #~ return []
        #~ res = []
        #~ for id in ids:
            #~ r = self.read(cr, uid, id, [], context)
            #~ print r
            #~ name = '(%sx%s)' % (r['length']+100,r['heigth']*100)
            #~ res.append((r['id'], name))
        #~ return res
    #TODO el campo name no se necesita pero si no se pone da error
    #TODO probablemente la solucion sea crear name como campo function en lugar de usar el get_name

    _columns = {
        'name':fields.char('Tile format', size=24, required=False),
        'length': fields.float('Length (m)', digits_compute=dp.get_precision('Extra UOM data')),
        'heigth': fields.float('Heigth (m)', digits_compute=dp.get_precision('Extra UOM data')),
        'factile': fields.function(_calc_tile_factor, method=True, type="float", string='Tile Factor', digits_compute=dp.get_precision('Product UoM')),
        #~ 'factile': fields.float('Factor Tile (m)', digits_compute=dp.get_precision('Extra UOM data')),
        'kit':fields.boolean('Is kit')
    }

    _defaults = {
        'length': lambda *a: 0,
        'heigth': lambda *a: 0,
        'kit': lambda *a: False,
    }

    _sql_constraints = [
        ('length_gt_zero', 'CHECK (length>0)', 'The length must be > 0!'),
        ('length_gt_heigth', 'CHECK (length>=heigth)', 'The length must be >= heigth!'),
        ('heigth_gt_zero', 'CHECK (heigth>0)', 'The heigth must be > 0!'),
        ('name', 'UNIQUE(name)', 'The tile format must be unique!'),
    ]


    def on_change_name(self,cr, uid, ids,length, heigth, context=None):
        if context is None: context = {}

        #~ reads = self.read(cr, uid, ids, [], context)
        res = {'value':{}}

        name = '(%s x %s) cm' % ((length*100),(heigth*100))
        factile = self.pool.get('product.uom')._calc_area(length,heigth)
        res['value'].update({'name':name})
        res['value'].update({'factile':factile})
        return res


    def create(self,cr,uid,vals,context=None):
        """
        Assign 'name' field
        """
        if vals.get('length',False) and vals.get('heigth',False):
            data = self.on_change_name(cr, uid, [],vals['length'],vals['heigth'], context)
            vals.update(data['value'])
        return  super(product_product_tile_format, self).create(cr, uid, vals, context)


    def write(self, cr, uid, ids, vals, context=None):
        if vals.get('length') or vals.get('heigth'):
            length = vals.get('length')
            heigth = vals.get('heigth')
            so_brw = self.browse(cr,uid,ids,context={})
            if not length and so_brw:
                length = so_brw[0].length
            if not heigth and so_brw:
                heigth = so_brw[0].heigth
            if length and heigth:
                data = self.on_change_name(cr, uid, [],length, heigth, context)
                vals.update(data['value'])
        res = super(product_product_tile_format, self).write(cr, uid, ids, vals, context)
        return res

product_product_tile_format()


class product_product_pricelist_group(osv.osv):
    """
    OpenERP Model : product_product_pricelist_group
    """

    _name = 'product.product.pricelist.group'
    _description = __doc__


    def name_get(self,cr, uid, ids, context):
        if not len(ids):
            return []
        reads = self.browse(cr, uid, ids, context)
        #~ l = self.pool.get('product.product.pricelist.group').browse(cr,uid,ids)
        res = []
        for r in reads:
            name = '[%s] %s)' % (r.code.strip(),r.name.strip())
            res.append((r.id, name))
        return res


    _columns = {
        'code': fields.char('Code', size=16, help="Unique code for this group."),
        'name':fields.char('Pricelist group', size=64, required=False, readonly=False),
        'order_id':fields.integer('Order',help="Order for this group (for lists and reports)."),
    }


    _defaults = {
        'name': lambda *a: None,
    }


    _sql_constraints = [
                 ('code_uniq', 'UNIQUE(code)', 'The group code must be unique!'),
                 ('order_uniq', 'UNIQUE(order_id)', 'Order must be unique!'),
                 ]


    _order = 'order_id'

product_product_pricelist_group()


class product_product(osv.osv):
    # TODO product.procudt or product.template
    _inherit = 'product.product'

    _columns = {
        'stock_driver' : fields.selection([('normal','Normal'),('tile','Tile'),('slab', 'Slab'), ('block', 'Block')], 'Stock driver', required=True,
            help='This field set the internal metod to handle stock'),
        'material_id': fields.many2one('product.product.features', 'Material', domain=[('type','=','material')], ondelete='restrict'),
        'layout_id': fields.many2one('product.product.features', 'Layout', domain=[('type','=','layout')], ondelete='restrict'),
        'color_id': fields.many2one('product.product.features', 'Color', domain=[('type','=','color')], ondelete='restrict'),
        'lot_prefix':fields.char('Lot prefix', size=3, required=False, help='Indicates first 3 chars for production\'s lots. Only for referal proposals'),
        'quality_id': fields.many2one('product.product.features', 'Quality', domain=[('type','=','quality')], ondelete='restrict'),
        'finish_id': fields.many2one('product.product.features', 'Finish', domain=[('type','=','finish')], ondelete='restrict'),
        'tile_format_id': fields.many2one('product.product.tile.format', 'Tile format', ondelete='restrict'),
        'thickness':fields.integer('Thickness (mm)'),
        'pricelist_group_id': fields.many2one('product.product.pricelist.group', 'Pricelist group', ondelete='restrict'),
        'origin_country_id': fields.many2one('res.country', 'Country of Origin', ondelete='restrict'),
        'similarity_ids': fields.many2many('product.product', 'rel_product_product_similarity', 'product_id1', 'product_id2', 'Similar products'),
        'hs_code': fields.char('HS Code', size=32),
        'tech_specs': fields.text('Tech specs'),
        'hardness': fields.integer(
            'Hardness', help="1=Soft, 3=Medium, 5=Hard"),
        }

    _defaults = {
        'stock_driver' : lambda *a : 'normal',
        'thickness': lambda *a : 0,
        'hardness': lambda *a : 1,
    }

    _sql_constraints = [
        ('thickness_gt_zero', 'CHECK (thickness>=0)', 'The thickness must be >= 0!'),
        ('hardness_range', 'CHECK(hardness between 1 and 5)',
         'The hardness_range must be in 1-5 range!'),
    ]


product_product()


class product_uom(osv.osv):
    _inherit = 'product.uom'

#    def _compute_qty(self, cr, uid, from_uom_id, qty, to_uom_id=False):
##        print '_compute_qty: %s' % (qty)
##TODO: Sentencia IF que verifica si debo usar el estandard o el personalizado.
#        return super(product_uom,self)._compute_qty(cr, uid, from_uom_id, qty, to_uom_id)

#    def _compute_qty_obj(self, cr, uid, from_unit, qty, to_unit, context=None):
##        print '_compute_qty_obj: %s % s' % (from_unit.name, to_unit.name)
#        return super(product_uom,self)._compute_qty_obj(cr, uid, from_unit, qty, to_unit, context)

#    def _compute_price(self, cr, uid, from_uom_id, price, to_uom_id=False):
##        print '_compute_price: %s' % (price)
#        return super(product_uom,self)._compute_price(cr, uid, from_uom_id, price, to_uom_id)

                        #Tabla de Readonly

##############################################################
#          #  Qty    #  Pieces #  Length #  Heigth  #  Width #
#          #         #         #         #          #        #
# Normal   #         #    R    #    R    #    R     #    R   #
#          #         #         #         #          #        #
# Tile     #   R     #         #    R    #    R     #    R   #
#          #         #         #         #          #        #
# Slab     #   R     #         #         #          #    R   #
#          #         #         #         #          #        #
# Block    #   R     #         #         #          #        #
#          #         #         #         #          #        #
##############################################################
# R = Reanonly


    # New metods for area calculation
    #~ def _calc_area(self,f1,f2):
        #~ '''Calculates an truncate f1*f2, set 4 decimal places
           #~ No error check'''
        #~ if f1 and f2:
            #~ print "f1, f2", f1,f2
            #~ return round(int(f1*f2*10000)/10000.0,4)
        #~ else:
            #~ return 0
    def _calc_area(self,f1,f2,f3=0.0):
        '''Calculates an truncate f1*f2, set 4 decimal places
           No error check
'''
        r = 0.0
        fct = 10000
        if f1 and f2 and f3:
            r = self._calc_area(f1, self._calc_area(f2,f3))
        elif f1 and f2:
            #~ This unreal calculation is required to correct some results 3.0 * 1.52 != 4.56 (4.5599)
            if type(f1) is str:
                f1 = float(f1)
            r = math.trunc(int(round(f1*fct))*int(round(f2*fct))/fct)/float(fct) + 0.000000000000004
        return r

    def _compute_area_tile(self, cr, uid, pieces, length, heigth, context=None):
        return self._calc_area(pieces,length,heigth)


    def _compute_area_slab(self, cr, uid, pieces, length, heigth, context=None):
        return self._calc_area(pieces,length,heigth)


    def _compute_area_block(self, cr, uid, length, heigth, width, context=None):
        return self._calc_area(width,length,heigth)


    def _compute_area(self, cr, uid, driver, pieces, length, heigth, width, context=None):
        #TODO check all values for inconsistencies f.ex length=None
        if driver in ('tile','slab'):
            r = self._compute_area_tile(cr, uid, pieces, length, heigth)
        elif driver == 'block':
            r = self._compute_area_block(cr, uid, length, heigth, width)
        else:
            r = 0 # Ver si se podria determinar un valor mejor
        return r
        #~ else:
            #~ raise osv.except_osv(_('Error'), _('Unkoun stock driver (%s): %s')%('product_uom._compute_area',driver,))

    # New metods for pieces calculation
    def _compute_pieces(self, cr, uid, driver, area, lot_factor, context=None):
        if driver in ('tile','slab'):
            return lot_factor and int(round((area /lot_factor),0))
        elif driver == 'block':
            return 1 # In block allways pieces = 1
        #~ else:
            #~ raise osv.except_osv(_('Error'), _('Unkoun stock driver (%s): %s')%('product_uom._compute_pieces',driver,))

    def _compute_pieces2(self, cr, uid, driver, area, length, heigth, width, context=None):
        lot_factor = self._compute_area(cr, uid, driver, 1, length, heigth, width, context=None)
        return self._compute_pieces(cr, uid, driver, area, lot_factor, context=None)

    def adjust_sizes(self, *args):
        '''
        measures = length, heigth, width
        Get length, heigth or width values and div by 100 id necessary
            300 -> 3.0, 270 -> 2.70, 90 -> 0.90
        makes cm to m conversion
        Sample:
        obj_uom = self.pool.get('product.uom')
        length, heigth, width = obj_uom.adjust_sizes(length, heigth, width)
        '''
        res = []
        for measure in args:
            res.append(measure if measure < 50 else measure / 100)
        return res

product_uom()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
