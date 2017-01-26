# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date: 23/04/2013
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
import time


##---------------------------------------------------------------------------------------- tcv_sale_order_import

class tcv_stock_picking_import(osv.osv_memory):

    _name = 'tcv.stock.picking.import'

    _inherit = 'tcv.base.import'

    _description = ''

    _import_settings = {'get_document_sql':'select * from ajuste where ajue_num = %s and anulada = 0',
                        'get_lines_sql':'select * from reng_aju where ajue_num = %s order by reng_num'}

    ##------------------------------------------------------------------------------------

    ##------------------------------------------------------------------------------------ _internal methods

    def _update_document_data(self,cr,uid,ids,document,context=None):
        '''
        This update field values in destination model
        need to be overwrited in inherited models
        '''
        if context is None:
            context = {}
        profit_config = context.get('profit_config')
        so_brw = context.get('tcv_base_import_brw')
        name = 'AJE%08d'%document['ajue_num']
        
        #~ partner_id = self._get_profit_code(cr, uid, 'res.partner', 'co_cli', document['co_cli'])
        #~ if not partner_id:
            #~ return {}
        #~ obj_pnr = self.pool.get('res.partner')
        partner = self.pool.get('res.users').browse(cr, uid, uid, context).company_id.partner_id
        
        address_id = 0
        for address in partner.address:
            if address.type == 'invoice':
                address_id = address.id
        
        #~ user_id = 0
        #~ user_name = self.profit_2_openerp_salesman(profit_config.company_ref,document['co_ven'])
        #~ obj_usr = self.pool.get('res.users')
        #~ user_ids = obj_usr.search(cr, uid, [('login', '=', user_name)])
        #~ if not user_ids or len(user_ids) != 1:
            #~ return {}
        #~ user_id = user_ids[0]
        
        updated_data = {'name':name,
                        'type':'in',
                        'date':self.encode_date(document['fecha']),
                        'min_date':self.encode_date(document['fecha']),
                        'address_id':address_id,
                        'invoice_state':'none',
                        'note':'Documento importado desde Profit\n\tajuste Nro: %s' \
                               '\n\tObservaciones: %s\n\tImportado el: %s'% \
                               (document['ajue_num'],
                                document.get('motivo',''),
                                time.strftime('%Y-%m-%d %H:%M:%S'))}
                        
        if context.get('active_model') == u'stock.picking' and context.get('active_id'):
            obj_sor = self.pool.get('stock.picking')
            obj_sor.write(cr,uid,context['active_id'],updated_data,context=context)
        return updated_data
        
        
    def _update_lines_data(self,cr,uid,ids,lines,context=None): 
        res = []
        obj_prd = self.pool.get('product.product')
        obj_lot = self.pool.get('stock.production.lot')
        obj_loc = self.pool.get('stock.location')
        str_error = ''
        for line in lines:
            profit_config = context.get('profit_config')
            
            product_id = self._get_profit_code(cr, uid, 'product.product', 'co_art', line['co_art'])
            if not product_id:
                return {}
            product = obj_prd.browse(cr,uid,product_id,context=context)
            
            if line['tipo'] != 'ENT':
                raise osv.except_osv(_('Error!'),_('Error en tipo de ajuste'))
                
            lot_id = 0
            lot = {}
            pieces = 0
            location_id = 97 # indeterminada
            if line['nro_lote'] and line['aux02']:
                print line['nro_lote'],line['aux02']
                obj_lot = self.pool.get('stock.production.lot')
                lot_ids = obj_lot.search(cr, uid, [('name', '=', line['nro_lote']),('product_id','=',product_id)])
                aux02 = self.decode_aux02(line['aux02'])
                if lot_ids: #Check if exits
                    lot_id = lot_ids[0]
                    lot_brw = obj_lot.browse(cr,uid,lot_id,context=context)
                    pieces = aux02['pieces']
                else:
                    lot = {'name':line['nro_lote'],
                           'product_id':product_id, 
                           'date':self.encode_date(line['fec_lote']),
                           }
                    lot.update(aux02)
                    if product.stock_driver in ['slab','tile']:
                        lot.update({'width':0})
                    pieces = aux02['pieces']
                    print lot
                    lot_id = obj_lot.create(cr,uid,lot,context)   
                if lot.get('location'):    
                    location_id = obj_loc.search(cr, uid, [('name', '=', lot['location'])])
                    if location_id and len(location_id) == 1:
                        location_id = location_id[0]
                        
            line_data = {'name':'Ajuste profit Nro: %s, Reng: %s'%(line['ajue_num'],line['reng_num']),
                         'product_id':product_id,
                         'location_id':4,
                         'product_qty':line['total_art'],
                         'location_dest_id':location_id,
                         'product_uom':product.uom_id.id,
                         'product_uos_qty':line['total_art'],
                         'product_uos':product.uom_id.id,
                         'date':self.encode_date(line['fec_lote']),
                         'date_expected':self.encode_date(line['fec_lote']),
                         'state':'draft',
                        }
            if lot_id:
                line_data.update({'prodlot_id':lot_id})
            res.append((0,0,line_data))
        if res and context.get('active_model') == u'stock.picking' and context.get('active_id'):
            obj_sor = self.pool.get('stock.picking')
            obj_sor.write(cr,uid,context['active_id'],{'move_lines':res},context=context)
        return res

    ##------------------------------------------------------------------------------------ function fields

    _columns = {
        }

    _defaults = {
        }

    _sql_constraints = [
        ]

    ##------------------------------------------------------------------------------------

    ##------------------------------------------------------------------------------------ public methods

    ##------------------------------------------------------------------------------------ buttons (object)

    ##------------------------------------------------------------------------------------ on_change...

    ##------------------------------------------------------------------------------------ create write unlink

    ##------------------------------------------------------------------------------------ Workflow

tcv_stock_picking_import()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
