# -*- encoding: utf-8 -*-
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

from datetime import datetime
from osv import fields,osv
from tools.translate import _
import pooler
import decimal_precision as dp
import time

# ---------------------------------------------------  Base class

class mrp_ctrl_tcv_base(osv.osv):
    '''
OpenERP Model : mrp_ctrl_tcv_base
    '''

    _name = 'mrp.ctrl.tcv.base'
    _description = __doc__
    _order = 'name desc'


    def _compute_run_time(self, cr, uid, ids, date_start, date_end, context=None):
        '''Must return date_end - date_start in hours'''
        if date_start and date_end:
            ts = time.mktime(time.strptime(date_start,'%Y-%m-%d %H:%M:%S')) #TODO usar: tools.DEFAULT_SERVER_DATE_FORMAT
            te = time.mktime(time.strptime(date_end,'%Y-%m-%d %H:%M:%S'))
            rt = (te-ts) #Result in seconds
            h = (rt)//3600
            m = ((rt)%3600.0)/60.0/60.0 # decimales (0.10 = 6 seg) usa regla de 3: 1 -> 60 | m -> s
            res = h+m
            return res


    STATE_SELECTION = [
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
        ]        


    _columns = {
        'name':fields.char('Reference', size=64, required=True, select=True, 
               help="unique number of the process, computed automatically when is created"),
        'mrp_production_id': fields.many2one('mrp.production', 'P/Order Nº', readonly=True),
        'routing_id': fields.many2one('mrp.routing', string='Routing', on_delete='set null', 
                      help="The list of operations (list of work centers) to produce the finished product. The routing is mainly used to compute work center costs during operations and to plan future loads on work centers based on production plannification."),
        'date_start':fields.datetime('Date started', required=True, states={'confirmed':[('readonly',True)], 'done':[('readonly',True)]}, select=True, 
                     help="Date on which this process has been started."),
        'date_end':fields.datetime('Date finished', required=True, states={'confirmed':[('readonly',True)], 'done':[('readonly',True)]}, select=True, 
                   help="Date on which this process has been finished."),
        # run_time is in seconds
        'run_time':fields.function(_compute_run_time, method=True, type='float', string='Production run time'),
        'author_id': fields.many2one('res.users', 'Author'),
        'note':fields.text('Description'),
        'company_id':fields.many2one('res.company','Company',required=True),
        'state':fields.selection(STATE_SELECTION, string='State', required=True, readonly=True),
        }


    _defaults = {
        'name': lambda *a: None,
        'date_start':lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
        'date_end':lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
        'author_id': lambda x, y, z, c: z,
        'company_id':lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr,uid,'mrp_ctrl_tcv_base',context=c),
        'state':'draft',
        }


    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Reference must be unique !'),
        ('run_time_gt_zero', 'CHECK (date_start<date_end)', 'The run_time must be > 0 !'),
        ]

        
    #~ TODO Add validation for run_time > 0.0 
        
        
    def on_change_run_time(self, cr, uid, ids, date_start, date_end):
        res = {'value':{'run_time':self._compute_run_time(cr,uid,ids,date_start, date_end)}}
        return res
        
        
    def confirm(self, cr, uid, ids, context=None):
        return self.write(cr,uid,ids,{'state':'confirm'})
    
    
    def done(self, cr, uid, ids, context=None):
        return self.write(cr,uid,ids,{'state':'done'})
    
    
    def draft(self, cr, uid, ids, context=None):
        return self.write(cr,uid,ids,{'state':'draft'})
    
mrp_ctrl_tcv_base()


# ---------------------------------------------------  Telares

class mrp_ctrl_telar(osv.osv):
    '''
OpenERP Model : mrp_ctrl_telar
    '''

    _name = 'mrp.ctrl.telar'
    _description = __doc__
    _inherit = 'mrp.ctrl.tcv.base'

    
    def _compute_total_m2(self, cr, uid, ids, name, args, context=None):
        #~ print "context",context
        #~ print "args",args
        return {}


    _columns = {
        'supplies_ids':fields.one2many('mrp.ctrl.telar.supplies','ctrl_telar_id','Details'),
        'total_m2':fields.function(_compute_total_m2, method=True, type='float', string='Total M2', store=False,
                                   digits_compute=dp.get_precision('Product UoM')),
        'viscocity_avg':fields.float('Avg. viscocity'),
        'supplies_ids':fields.one2many('mrp.ctrl.telar.supplies','ctrl_telar_id','Details'),
        'lines_ids':fields.one2many('mrp.ctrl.telar.lines','ctrl_telar_id','Details'),
        }
    
    
    _defaults = {
        'name': lambda obj, cr, uid, context: obj.pool.get('ir.sequence').get(cr, uid, 'control.telar'),  
        }


    def confirm(self, cr, uid, ids, context=None):
        return self.write(cr,uid,ids,{'state':'confirm'})
    
    
    def done(self, cr, uid, ids, context=None):
        return self.write(cr,uid,ids,{'state':'done'})
    
    
    def draft(self, cr, uid, ids, context=None):
        return self.write(cr,uid,ids,{'state':'draft'})
        
        
    def on_change_lines_ids(self, cr, uid, ids, lines_ids):    
        tm2 = 0
        res = {}
        for l in lines_ids:
            tm2 += l[2]['area']
        res = {'value':{'total_m2':tm2}}              
        return res    

mrp_ctrl_telar()


# ---------------------------------------------------  Telares.line

class mrp_ctrl_telar_supplies(osv.osv):
    '''
    OpenERP Model : mrp_ctrl_telar_supplies
    '''
    
    
    _name = 'mrp.ctrl.telar.supplies'
    _description = __doc__
    
    
    def product_id_change(self, cr, uid, ids, product, qty, uom, context=None):
        #~ print "product_id_change"
        product_uom_obj = self.pool.get('product.uom')
        product_obj = self.pool.get('product.product')
        result = {}
        if not product:
            return {'value': result}
        product_obj = product_obj.browse(cr, uid, product, context=context)
        uom2 = False
        if uom:
            uom2 = product_uom_obj.browse(cr, uid, uom)
            if product_obj.uom_id.category_id.id != uom2.category_id.id:
                uom = False
        if not uom:
            result['product_uom'] = product_obj.uom_id.id    
        return {'value': result}
    
    
    _columns = {
        'ctrl_telar_id':fields.many2one('mrp.ctrl.telar', 'Corte',required=True),
        'type': fields.selection([('granalla','Granalla'), ('cal','Cal'),('other','Other')], 'Supplies type', required=True, 
                help='Inticates the type of the supplies'),
        'product_id':fields.many2one('product.product', 'Supplies product', help='Supplies product', required=True),     
        'product_qty':fields.float('Product qty', required=True, digits_compute=dp.get_precision('Product UoM')),
        'product_uom': fields.many2one('product.uom', 'UoM', required=True, 
                       help='The Unit of Measure used for stock operation.'),
        }


    _sql_constraints = [
        ('qty_gt_zero', 'CHECK (product_qty>0)', 'The product qty must be > 0!'),
        ]          

mrp_ctrl_telar_supplies()    


class mrp_ctrl_telar_lines(osv.osv):
    '''
    OpenERP Model : mrp_ctrl_telar_lines
    '''
    
    _name = 'mrp.ctrl.telar.lines'
    _description = __doc__
    
    
    def default_get(self, cr, uid, fields, context=None):
        if context==None:
            context = {}
        res = super(mrp_ctrl_telar_lines,self).default_get(cr, uid, fields, context=context)
        if context.get('lines_ids',False):
            for i in context['lines_ids']:
                res.update({'cuchilla_prod_id':i[2]['cuchilla_prod_id'],
                            'cuchilla_heigth_start':i[2]['cuchilla_heigth_start'],
                            'cuchilla_heigth_end':i[2]['cuchilla_heigth_end']})
        return res   

    
    def _compute_area(self, cr, uid, ids, product_pcs, length, heigth, context=None):
        #~ print context
        obj_uom = self.pool.get('product.uom')
        return obj_uom._compute_area_slab(cr, uid, ids, product_pcs, length, heigth, context=None)
        

    _columns = {
        'ctrl_telar_id':fields.many2one('mrp.ctrl.telar', 'Corte',required=True),
        'prod_lot_id':fields.many2one('stock.production.lot','Block (lot Nº)',required=True),
        'product_name_lot':fields.related('prod_lot_id','product_id', type='many2one', relation='product.product', 
                           string='Product name',store=False, readonly=True),  
        #~ 'product_stock_driver':fields.related('prod_lot_id','stock_driver', type='many2one', relation='product.product', 
                               #~ string='Stock driver',store=False, readonly=True),  
        'cuchilla_prod_id':fields.many2one('product.product', 'Cuchilla', required=True),
        'cuchillas_qty':fields.integer('Cuchillas qty', required=True),
        'cuchilla_heigth_start':fields.float('Cch init h(cm)'),
        'cuchilla_heigth_end':fields.float('Cch end h(cm)'),
        'product_id':fields.many2one('product.product', 'Rslt. Product', help='The resulting product', required=True), 
        'product_pcs':fields.integer('Slabs'),
        'length': fields.float('Length(m)', digits_compute=dp.get_precision('Extra UOM data')),
        'heigth': fields.float('Heigth(m)', digits_compute=dp.get_precision('Extra UOM data')),
        'area':fields.function(_compute_area, method=True, type='float', string='Area in M2', digits_compute=dp.get_precision('Product UoM')),
        }
        
        
    _defaults = {
        'cuchilla_heigth_start':lambda *a: 10,
        'cuchilla_heigth_end': lambda *a: 0,
        }

        
    _sql_constraints = [
            ('cuchillas_qty_gt_1', 'CHECK (cuchillas_qty>=2)', 'The cuchillas quantity mus be >= 2!'),
            ('product_pcs_gt_cuchillas_qty', 'CHECK (cuchillas_qty>=product_pcs+1)', 'The cuchillas quantity mus be greater than product_pcs'),
            ('product_pcs_gt_0', 'CHECK (product_pcs>=0)', 'The slabs quantity mus be >= 0!'),
            ('cuchilla_heigth_start_gt_zero', 'CHECK (cuchilla_heigth_start>=0)', 'The cuchilla heigth start must be >= 0!'),
            ('cuchilla_heigth_end_gt_zero', 'CHECK (cuchilla_heigth_end>=0)', 'The cuchilla heigth end must be >= 0!'),
            ('length_gt_zero', 'CHECK (length>=0)', 'The length must be >= 0!'),
            ('heigth_gt_zero', 'CHECK (heigth>=0)', 'The heigth must be >= 0!'),
        ]        
        
        
    def _rotate(self):
        ''' read lot info and swap heigth & width '''
        return 0
    
    
    def on_change_prod_lot(self, cr, uid, ids, prod_lot_id):
        res = {}
        if prod_lot_id:
            lot = self.pool.get('stock.production.lot').browse(cr,uid,prod_lot_id,context=None)
            res= {'value':{}}
            res['value'].update({'length':lot.length,
                                 'heigth':lot.heigth,
                                 'product_name_lot':lot.product_id.id})
        return res
    
        
    def on_change_cuchillas_qty(self, cr, uid, ids, cuchillas_qty, product_pcs, length, heigth):
        res = {}
        if not product_pcs or cuchillas_qty < product_pcs:
            pcs = cuchillas_qty-1
            res =  {'value':{'product_pcs':pcs,
                             'area':self._compute_area(cr, uid, ids, pcs, length, heigth)}}
        return res  
            

    def on_change_area(self, cr, uid, ids, product_pcs, length, heigth):
        return {'value':{'area':self._compute_area(cr, uid, ids, product_pcs, length, heigth)}}              

mrp_ctrl_telar_lines()


# ---------------------------------------------------  Telares

class mrp_ctrl_pulidora(osv.osv):
    '''
    OpenERP Model : mrp_ctrl_pulidora
    '''

    _name = 'mrp.ctrl.pulidora'
    _description = __doc__
    _inherit = 'mrp.ctrl.tcv.base'

    _columns = {
        'prod_lot_id':fields.many2one('stock.production.lot','Block(lot Nº)',required=True, help='The raw material lot'), 
        'product_name_lot':fields.related('prod_lot_id','product_id', type='many2one', relation='product.product', 
                           string='Product name',store=False, required=False, readonly=True),  
        'product_id':fields.many2one('product.product', 'Rslt. Product', help='The resulting product'), 
        'band_speed':fields.integer('Band speed'), 
        #~ 'base_id':fields.many2one('mrp.ctrl.tcv.base','mrp_ctrl_tcv_base', required=True, ondelete='cascase'),
        'lines_ids':fields.one2many('mrp.ctrl.pulidora.lines','ctrl_pulidora_id','Details'),
    }

    _defaults = {
        'name': lambda obj, cr, uid, context: obj.pool.get('ir.sequence').get(cr, uid, 'control.pulidora'),  
        'prod_lot_id': lambda self, cr, uid, c: c.get('prod_lot_id',False),
    }
    

    def on_change_prod_lot(self, cr, uid, ids, prod_lot_id):
        res = {}
        if prod_lot_id:
            lot = self.pool.get('stock.production.lot').browse(cr,uid,prod_lot_id,context=None)
            res= {'value':{}}
            res['value'].update({'product_name_lot':lot.product_id.id})
        return res
    
mrp_ctrl_pulidora()


class mrp_ctrl_pulidora_lines(osv.osv):
    '''
    OpenERP Model : mrp_ctrl_pulidora_line
    '''


    def default_get(self, cr, uid, fields, context=None):
        if context==None:
            context = {}
        res = super(mrp_ctrl_pulidora_lines,self).default_get(cr, uid, fields, context=context)
        if context['lines_ids']:
            for i in context['lines_ids']:
                res.update({'name':int(i[2]['name'])+1,'length':i[2]['length'],'heigth':i[2]['heigth']})
        if res == {} and context['prod_lot_id']:
            lot = self.pool.get('stock.production.lot').browse(cr,uid,context['prod_lot_id'],context=None)
            res.update({'length':lot.length,'heigth':lot.heigth})
        return res   
    

    def _compute_area(self, cr, uid, ids, length, heigth, context=None):
        obj_uom = self.pool.get('product.uom')
        return obj_uom._calc_area(length,heigth)
        
        
    _name = 'mrp.ctrl.pulidora.lines'
    _description = __doc__
    
    
    _columns = {
        'ctrl_pulidora_id':fields.many2one('mrp.ctrl.pulidora', 'Polish',required=True),
        'name': fields.char('Production Lot', size=64, required=True, help="Unique production lot, will be displayed as: PREFIX/SERIAL [INT_REF]"),
        'length': fields.float('Length(m)', digits_compute=dp.get_precision('Extra UOM data')),
        'heigth': fields.float('Heigth(m)', digits_compute=dp.get_precision('Extra UOM data')),
        'area':fields.function(_compute_area, method=True, type='float', string='Area in M2', digits_compute=dp.get_precision('Product UoM')),
        }

    def on_change_area(self, cr, uid, ids, length, heigth):
        return {'value':{'area':self._compute_area(cr,uid,ids,length, heigth)}}    
     

mrp_ctrl_pulidora_lines()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
