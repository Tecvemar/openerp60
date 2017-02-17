# -*- coding: UTF-8 -*-
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

class purchase_order(osv.osv):

  
    _inherit = "purchase.order"

    def get_company(self,cr,uid,ids,context=None):
        if context is None:
            context = {}
        rc_obj = self.pool.get("res.company")
        rc_ids = rc_obj.search(cr,uid,[],context=context)
        rc_brw = rc_obj.browse(cr,uid,rc_ids,context=context)
        partner_id = self.browse(cr,uid,ids[0],context=context).partner_id.id
        return [i.id for i in rc_brw if i.partner_id.id == partner_id]


    def inter_so_apply(self,cr,uid,ids,context=None):
        if context is None:
            context = {}
        return any(self.get_company(cr,uid,ids,context))
    
    def action_picking_create(self,cr, uid, ids, *args):
        """
        Assigned locations if is a transaction intercompany
        Causa error cuando existen ubicaciones encadenadas
        """
        result = super(purchase_order, self).action_picking_create(cr, uid, ids, args)
        #~ stock_mv_obj = self.pool.get('stock.move')
        #~ stock_loca_obj = self.pool.get('stock.location')
        #~ company_obj = self.pool.get('res.company')
        #~ company_id = company_obj._company_default_get(cr, uid, 'purchase.order')
        #~ company_brw = company_obj.browse(cr,uid,company_id,context={})
        #~ purchase_brw = self.browse(cr, uid, ids)
        #~ if not purchase_brw[0].partner_id.seniat_updated and [i .id for i in purchase_brw[0].partner_id.address if i.country_id.code == 'VE']:
            #~ raise osv.except_osv(_('Processing Error'), _('The partner is not updated with seniat'))
        #~ for order in purchase_brw:
            #~ if company_brw.company_in_ids:
                #~ for company in company_brw.company_in_ids:
                    #~ if company.id == order.partner_id.id:
                        #~ loc_id = company_brw.location_stock_id and company_brw.location_stock_id.id
                        #~ dest = company_brw.location_stock_internal_id and company_brw.location_stock_internal_id.id
                        #~ break
                    #~ else:
                        #~ loc_id = order.partner_id.property_stock_supplier and order.partner_id.property_stock_supplier.id
                        #~ dest = order.location_id.id
            #~ else:
                #~ loc_id = order.partner_id.property_stock_supplier and order.partner_id.property_stock_supplier.id
                #~ dest = order.location_id.id
            #~ 
            #~ for order_line in order.order_line:
                #~ for mv in order_line.move_ids:
                    #~ stock_mv_obj.write(cr, uid,[mv.id], {
                        #~ 'location_id': loc_id,
                        #~ 'location_dest_id': dest,
                        #~ })
        return result

    def action_so_create(self,cr,uid,ids,context=None):  
        '''
        Generate sale order from a purchase order
        '''
        if context is None:
            context = {}
        po_brw = self.browse(cr,uid,ids[0],context=context)
        so_obj = self.pool.get("sale.order")
        rpa_obj = self.pool.get("res.partner.address")
        partner_id = po_brw.company_id.partner_id.id

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
        for i in po_brw.order_line:
            if i.sale_order_line_ids:
                break
            #~ Puede ser mejor con un break (hacer pruebas)
            else:    
                so_line.append((0,0,{'product_id':i.product_id and i.product_id.id,
                                     #~ 'concept_id':i.concept_id and i.concept_id.id,
                                     'product_uom_qty':i.product_qty,
                                     'product_uom':i.product_uom and i.product_uom.id,
                                     'date_planned':i.date_planned,
                                     'price_unit':i.price_unit,
                                     'pieces':i.pieces,
                                     'company_id':company_id and company_id[0],
                                     'name':i.name,
                                     'purchase_order_line_id': i and i.id
                                     }))

                po_line.append((4,po_brw.id))
            name = self.pool.get('ir.sequence').get(cr, uid,'sale.order')

            company_obj = self.pool.get('res.company')
            company_brw = company_obj.browse(cr,uid,company_id[0],context=context)
            if not company_brw.user_in_id:
                raise osv.except_osv(_('Processing Error'), _('The partner need a in user'))
            user = company_brw.user_in_id.id
            values = {
                    'partner_id':partner_id,
                    'pricelist_id':po_brw.pricelist_id.id,
                    'partner_invoice_id':partner_invoice_id,
                    'partner_order_id':ordering_invoice_id,
                    'partner_shipping_id':shipping_invoice_id,
                    'company_id':company_id and company_id[0],
                    'name': name,
                    'order_line':so_line,
                    'user_id': user,
                    'purchase_order_ids':po_line,
                    }
        return so_obj.create(cr,user,values,context=context)
purchase_order()
