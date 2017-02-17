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
from datetime import datetime, timedelta
import netsvc
from dateutil.relativedelta import relativedelta
import time


class sale_order_line(osv.osv):
    
    # TODO product.procudt or product.template 
    _inherit = 'sale.order.line'

    _columns = {
                'purchase_order_line_id':fields.many2one('purchase.order.line','Purchase line'),
                'com_id':fields.many2one('res.company','Company'),
                }
    _defaults = {
                'com_id': lambda s,cr,uid,c: s.pool.get('res.company')._company_default_get(cr, uid, 'sale.order.line', context=c),
                }
    # TODO agregar validacion para requerir el nro de lote (track_outgoing)

    
sale_order_line()    

class sale_order(osv.osv):
    
    _inherit = 'sale.order'
    
    _columns = {
        'purchase_order_ids':fields.many2many('purchase.order','intercompany_rel','sales_order_id','purchase_order_id','Transactions')
    }
    
    def get_company(self,cr,uid,ids,context=None):
        if context is None:
            context = {}
        
        partner_id = self.browse(cr,uid,ids[0],context=context).partner_id.id
        rc_obj = self.pool.get("res.company")
        rc_ids = rc_obj.search(cr,uid,[('partner_id','=',partner_id)],context=context)
        if rc_ids:
            return rc_ids
        else:
            return rc_ids
#~ 
    def inter_po_apply(self,cr,uid,ids,context=None):
        if context is None:
            context = {}
        return any(self.get_company(cr,uid,ids,context))
    
    def action_ship_create(self, cr, uid, ids, *args):
        """
       Modified to avoid confirm a sell order that not have lots related
        and generate stock picking and move lines in the company that generate the purchase order
        """
        result = super(sale_order, self).action_ship_create(cr, uid, ids, *args)
        sm_obj = self.pool.get('stock.move')
        picking_obj = self.pool.get('stock.picking')
        company_obj = self.pool.get('res.company')
        lot_obj = self.pool.get('stock.production.lot')
        sale_brw = self.browse(cr, uid, ids, context={})
        company_obj = self.pool.get('res.company')
        company_id = company_obj._company_default_get(cr, uid, 'sale.order')
        company_brws = company_obj.browse(cr,uid,company_id,context={})
        if not sale_brw[0].partner_id.seniat_updated and [i .id for i in sale_brw[0].partner_id.address if i.country_id.code == 'VE']:
            raise osv.except_osv(_('Processing Error'), _('The partner is not updated with seniat'))
        for order in sale_brw:
            if company_brws.company_out_ids:
                for company in company_brws.company_out_ids:
                    if company.id == order.partner_id.id:
                        dest = company.location_stock_id and company.location_stock_id.id
                        orig = company_brws.location_stock_internal_id and company_brws.location_stock_internal_id.id
                        break
                    else:
                        dest = order.shop_id.warehouse_id.lot_output_id and order.shop_id.warehouse_id.lot_output_id.id
                        orig = order.shop_id.warehouse_id.lot_stock_id and order.shop_id.warehouse_id.lot_stock_id.id
            else:
                dest = order.shop_id.warehouse_id.lot_output_id and order.shop_id.warehouse_id.lot_output_id.id
                orig = order.shop_id.warehouse_id.lot_stock_id and order.shop_id.warehouse_id.lot_stock_id.id
            
                
            for ol in order.order_line:
                
                if ol.prod_lot_id.id == False and ol.product_id.stock_driver is ('slab','normal','block','tile'):
                    raise osv.except_osv(_('Processing Error'), _('The line is not lot'))
                
                #~ elif ol.prod_lot_id.stock_move_id:
                    #~ self.create_internal_sale(cr,uid,ids,order,ol,context={})
              #~ 
                for sm in ol.move_ids:
                    sm_obj.write(cr, uid, [sm.id], 
                        {
                        'prodlot_id':ol.prod_lot_id and ol.prod_lot_id.id,
                        'pieces_qty':ol.pieces,
                        'location_id':orig,
                        'location_dest_id':dest,
                        'state':'draft',
                        })
            if order.purchase_order_ids:
                vals = []
                picking_in_ids = picking_obj.search(cr,uid,[('origin','=',order.purchase_order_ids[0].name)],context={})
                picking_out_ids = picking_obj.search(cr,uid,[('origin','=',order.name)],context={})
                picking_in_brw = picking_obj.browse(cr,uid,picking_in_ids[0],context={})
                picking_out_brw = picking_obj.browse(cr,uid,picking_out_ids[0],context={})
               
                for pickin_in in picking_in_brw.move_lines:
                    sm_obj.write(cr,uid,[pickin_in.id],{'state':'draft'},context={})
                    sm_obj.unlink(cr,uid,[pickin_in.id],context=None)
                    
                for picking_out in picking_out_brw.move_lines:
                    print "picking_in_brw.company_id.name",picking_in_brw.company_id.name
                    lot = {
                    'name':picking_out.prodlot_id.name,
                    'product_id':picking_out.prodlot_id.product_id and picking_out.prodlot_id.product_id.id,
                    'length':picking_out.prodlot_id.length,
                    'heigth':picking_out.prodlot_id.heigth,
                    'width':picking_out.prodlot_id.width,
                    'stock_move_id':picking_out.id,
                    'stock_move_in_id':[],
                    'company_id':order.partner_id.id,
                    }
                    lot_new = lot_obj.create(cr, uid, lot, context={})
                    mov_id = sm_obj.create(cr,uid,{'name':picking_in_brw.origin,
                    'product_id':picking_out.product_id and picking_out.product_id.id,
                    'product_qty':picking_out.product_qty,
                    'pieces_qty':picking_out.pieces_qty,
                    'product_uom': picking_out.product_uom.id,
                    'date':picking_out.date,
                    'date_expected':picking_out.date_expected,
                    'state':'draft',
                    'location_id':picking_in_brw.company_id.location_stock_id and picking_in_brw.company_id.location_stock_id.id,
                    'location_dest_id':picking_in_brw.company_id.location_stock_internal_id and picking_in_brw.company_id.location_stock_internal_id.id ,
                    'prodlot_id':lot_new,
                    'company_id':order.partner_id and order.partner_id.id,
                    'picking_id': picking_in_brw and picking_in_brw.id,
                    
                    })
                    lot_obj.write(cr,uid,[lot_new],{'stock_move_in_id':mov_id},context={})
                
        return result

    def purchase_order(self,cr,uid,ids,context=None):  
        if context is None:
            context = {}
        so_brw = self.browse(cr,uid,ids[0],context=context)
        po_obj = self.pool.get("purchase.order")
        rpa_obj = self.pool.get("res.partner.address")
        partner_id = so_brw.company_id.partner_id.id
        company = self.pool.get('res.users').browse(cr, uid, uid).company_id
        rpa_inv = rpa_obj.search(cr,uid,[('type','=','invoice'),('partner_id','=',partner_id)])
        rpa_ctc = rpa_obj.search(cr,uid,[('type','=','contact'),('partner_id','=',partner_id)])
        rpa_dft = rpa_obj.search(cr,uid,[('type','=','default'),('partner_id','=',partner_id)])
        rpa_shp = rpa_obj.search(cr,uid,[('type','=','delivery'),('partner_id','=',partner_id)])

        partner_invoice_id = rpa_inv and rpa_inv[0]
        ordering_invoice_id = rpa_ctc and rpa_ctc[0] or rpa_ctc and rpa_ctc[0] or rpa_inv and rpa_inv[0]  
        shipping_invoice_id = rpa_shp and rpa_shp[0] or rpa_inv and rpa_inv[0]  
        company_id = self.get_company(cr,uid,ids,context)
        so_line = []
        po_line = []
        for i in so_brw.order_line:
            if i.purchase_order_line_id:
                pass
                #~ pruebas con break
            else:
                date_planned = datetime.now() + relativedelta(days=i.delay or 0.0)
                date_planned = (date_planned - timedelta(days=company.security_lead)).strftime('%Y-%m-%d %H:%M:%S')
                po_line.append((0,0,{'product_id':i.product_id and i.product_id.id,
                                     #~ 'concept_id':i.concept_id and i.concept_id.id,
                                     'product_qty':i.product_uom_qty,
                                     'product_uom':i.product_uom and i.product_uom.id,
                                     'date_planned':date_planned,
                                     'price_unit':i.price_unit,
                                     'pieces':i.pieces,
                                     'prod_lot_id':[],
                                     'company_id':company_id and company_id[0],
                                     'name':i.name,
                                     'sale_order_line_ids':[(4,i.id)],
                                     }))
        so_line.append((4,so_brw.id))

        name = self.pool.get('ir.sequence').get(cr, uid,'purchase.order')
        company_obj = self.pool.get('res.company')
        company_brw = company_obj.browse(cr,uid,company_id[0],context=context)
        if not company_brw.user_in_id:
            raise osv.except_osv(_('Processing Error'), _('The partner need a in user'))
        user = company_brw.user_in_id.id
        values = {
                'partner_id':partner_id,
                'pricelist_id':so_brw.pricelist_id.id,
                'partner_address_id':partner_invoice_id,
                'partner_order_id':ordering_invoice_id,
                'partner_shipping_id':shipping_invoice_id,
                'company_id':company_id and company_id[0],
                'name': name,
                'location_id': company_brw.location_stock_id and company_brw.location_stock_id.id,
                'location_dest_id': company_brw.location_stock_internal_id and company_brw.location_stock_internal_id.id,
                'order_line':po_line,
                'validator':user,
                'user_id':user,
                'sale_order_ids':so_line,
                }
        if po_line:
            po_id = po_obj.create(cr,user,values,context=context)
            po_obj.wkf_confirm_order(cr, user, [po_id], context)
            po_obj.wkf_approve_order(cr, user, [po_id], context)
            po_obj.action_picking_create(cr, user, [po_id], ())
            self.action_ship_create(cr, uid, ids,())
            return po_id
        else:
            return po_line

    def create_internal_sale(self,cr,uid,ids,order_id,line_id,context=None):
        """
        Create a new picking for lots assigned for CONSIGNMENT and that is in a sale order
        @param order_id browse of sale order
        @param line_id browse of sale order line
        """
        if context == None: context = {}
        sm_obj = self.pool.get('stock.move')
        picking_obj = self.pool.get('stock.picking')
        company_obj = self.pool.get('res.company')
        res_address_obj = self.pool.get('res.partner.address')
        company_id = company_obj._company_default_get(cr, uid, 'sale.order', context=context),
        company_brw = company_obj.browse(cr,uid,company_id[0],context=context)
        picking_origin = picking_sale = []
        sm_in_brw = sm_obj.browse(cr,uid,line_id.prod_lot_id.stock_move_in_id.id,context=context)
        if sm_in_brw.state == 'draft':

            if line_id.quantity <= sm_in_brw.product_qty:
                vals = {
                'product_qty': sm_in_brw.product_qty - line_id.quantity,
                'pieces_qty': sm_in_brw.pieces_qty - line_id.pieces,}
                
                sm_obj.write(cr,uid,[line_id.prod_lot_id.stock_move_id.id],vals,context=context)
                sm_obj.write(cr,uid,[line_id.prod_lot_id.stock_move_in_id.id],vals,context=context)

            if line_id.quantity > sm_in_brw.product_qty:
                raise osv.except_osv(_('Invalid action !'), _('The quantity is greater than available!'))
            picking_ids_out = picking_obj.search(cr,uid,[('state_rw','=',1),('company_id','=',company_id[0])],context=context)
            picking_ids = picking_obj.search(cr,uid,[('state_rw','=',1),('company_id','=',line_id.prod_lot_id.stock_move_id.prodlot_id.company_id.id)],context=context)
            address_in = res_address_obj.search(cr,uid,[('partner_id','=',line_id.prod_lot_id.stock_move_id.prodlot_id.company_id.partner_id.id)],context=context)
            address_out = res_address_obj.search(cr,uid,[('partner_id','=',company_brw.id)],context=context)
            if picking_ids_out and picking_ids:
#-----------------------------Acropolis Picking -------------------------------------------------------------  
                picking_in_id = picking_ids_out[0]
                picking_in_brw = picking_obj.browse(cr,uid,picking_in_id,context=context)
                picking_obj.write(cr,uid,[picking_in_id],{'state_rw':0},context=context)
                pick_out = { 'product_qty':line_id.quantity,'pieces_qty':line_id.pieces,'picking_id':picking_in_id,
                    'state':'done',
                    'location_dest_id':line_id.prod_lot_id.stock_move_id.prodlot_id.company_id.location_stock_internal_id and line_id.prod_lot_id.stock_move_id.prodlot_id.company_id.location_stock_internal_id.id,
                    'location_id':company_brw.location_stock_internal_id and company_brw.location_stock_internal_id.id,
                    'note':
u"""
%s
\n Recibido el producto %s desde %s el dia %s
""" %(picking_in_brw.note,line_id.product_id.name,line_id.prod_lot_id.stock_move_id.prodlot_id.company_id.name,time.strftime('%d/%m/%Y')),
                    }
#~----------------------------Tecvemar Picking-------------------------------------------------------- 
                picking_id = picking_ids[0]
                picking_ids_brw = picking_obj.browse(cr,uid,picking_id,context=context)
                picking_obj.write(cr,uid,[picking_id],{'state_rw':0},context=context)
                pick_in = {'product_qty':line_id.quantity,'pieces_qty':line_id.pieces,'picking_id':picking_id,
                'state':'done',
                'location_dest_id':company_brw.location_stock_internal_id and company_brw.location_stock_internal_id.id,
                'location_id':line_id.prod_lot_id.stock_move_id.prodlot_id.company_id.location_stock_internal_id and line_id.prod_lot_id.stock_move_id.prodlot_id.company_id.location_stock_internal_id.id,
                'note':
u"""
%s
\n Enviado el producto %s hacia el acropolis %s el dia %s
""" %(picking_ids_brw.note,line_id.product_id.name,line_id.prod_lot_id.company_id.name,time.strftime('%d/%m/%Y'))
                }
            else:
#~ ----------------------------Picking Acropolis----------------------------------------------------------------
              
                pick_name_in = self.pool.get('ir.sequence').get(cr, uid, 'stock.picking.in')
                picking_in_id = picking_obj.create(cr, uid, {
                    'name': pick_name_in,
                    'origin': order_id.name+((order_id.origin and (':'+order_id.origin)) or ''),
                    'type': 'in','address_id': address_in[0],'invoice_state': '2binvoiced','state_rw': 0,
                    'purchase_id': [],
                    'note':
u"""
Picking generados por consignación el dia %s
Transacción generada entre %s ------> %s
""" %(time.strftime('%d/%m/%Y'),line_id.prod_lot_id.stock_move_id.prodlot_id.company_id.name,line_id.prod_lot_id.company_id.name),
                    'company_id': company_id[0],
                    'move_lines' : [], })
               
                pick_out = {
                'product_qty':line_id.quantity,'pieces_qty':line_id.pieces,'picking_id':picking_in_id,
                'state':'done',
                'location_dest_id':company_brw.location_stock_internal_id and company_brw.location_stock_internal_id.id,
                'location_id':line_id.prod_lot_id.stock_move_id.prodlot_id.company_id.location_stock_internal_id and line_id.prod_lot_id.stock_move_id.prodlot_id.company_id.location_stock_internal_id.id,
                }
                
#~-------------------------Tecvemar Picking-------------------------------------------------------------------
              
                pick_name = self.pool.get('ir.sequence').get(cr, uid, 'stock.picking.out')
                picking_id = picking_obj.create(cr, uid, {
                    'name': pick_name,
                    'origin': order_id.name+((order_id.origin and (':'+order_id.origin)) or ''),
                    'type': 'out', 'address_id': address_out[0],'invoice_state': '2binvoiced','state_rw': 0,
                    'sale_id': [],
                    'note':
u"""
Picking generados por consignación el dia %s
Transacción generada entre %s ------> %s
""" %(time.strftime('%d/%m/%Y'),line_id.prod_lot_id.stock_move_id.prodlot_id.company_id.name,line_id.prod_lot_id.company_id.name),
                    'company_id': line_id.prod_lot_id.stock_move_id.prodlot_id.company_id and line_id.prod_lot_id.stock_move_id.prodlot_id.company_id.id,
                    'move_lines' : [],})
              
                pick_in = {'product_qty':line_id.quantity,'pieces_qty':line_id.pieces,'picking_id':picking_id,
                'state':'draft',
                'location_dest_id':company_brw.location_stock_internal_id and company_brw.location_stock_internal_id.id,
                'location_id':line_id.prod_lot_id.stock_move_id.prodlot_id.company_id.location_stock_internal_id and line_id.prod_lot_id.stock_move_id.prodlot_id.company_id.location_stock_internal_id.id,
                }
            sm_obj.copy(cr,uid,line_id.prod_lot_id.stock_move_id.id,pick_in,context=context)
            sm_obj.copy(cr,uid,line_id.prod_lot_id.stock_move_in_id.id,pick_out,context=context)
            picking_origin.append((4,picking_id))
            picking_sale.append((4,picking_in_id))
            picking_obj.write(cr,uid,[picking_in_id],{'picking_origin_ids':picking_origin,'state_rw':1},context=context)
            picking_obj.write(cr,uid,[picking_id],{'picking_sale_ids':picking_sale,'state_rw':1},context=context)

        return True

    def unlink(self, cr, uid, ids, context=None):
        """
       Modified to avoid delete a sell order that have purchase order related

        """
        sale_orders = self.browse(cr, uid, ids,context=context)
        unlink_ids = []
        for s in sale_orders:
            for po in s.order_line:
                if po.purchase_order_line_id.id != False:
                    raise osv.except_osv(_('Invalid action !'), _('Cannot delete a sales order because have a purchase order related!'))
            if s.state in ('draft', 'cancel'):
                unlink_ids.append(s.id)
            else:
                raise osv.except_osv(_('Invalid action !'), _('Cannot delete Sales Order(s) which are already confirmed !'))
        return super(sale_order, self).unlink(cr, uid, unlink_ids, context=context)
   
    def copy(self, cr, uid, id, default=None, context=None):
        """
       Modified to avoid doubling a sell order, bring the order that the genre
        
        """
        if not default:
            default = {}
        so_line = []
        so_brw = self.browse(cr,uid,id,context=context)
        for i in so_brw.order_line:
            so_line.append((0,0,{'product_id':i.product_id and i.product_id.id,
                                 #~ 'concept_id':i.concept_id and i.concept_id.id,
                                 'product_uom_qty':i.product_uom_qty,
                                 'product_uom':i.product_uom and i.product_uom.id,
                                 'price_unit':i.price_unit,
                                 'pieces':i.pieces,
                                 'company_id': i.company_id and i.company_id.id,
                                 'prod_lot_id':[],
                                 'name':i.name,
                                 }))
        default.update({
            'purchase_order_ids':False,
            'order_line':so_line,
            'state': 'draft',
            'shipped': False,
            'invoice_ids': [],
            'picking_ids': [],
            'date_confirm': False,
            'name': self.pool.get('ir.sequence').get(cr, uid, 'sale.order'),
        })
        return super(sale_order, self).copy(cr, uid, id, default, context=context)


sale_order()


