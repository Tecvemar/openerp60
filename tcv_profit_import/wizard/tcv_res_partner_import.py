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


##---------------------------------------------------------------------------------------- tcv_res_partner_import

class tcv_res_partner_import(osv.osv_memory):

    _name = 'tcv.purchase.order.import'

    _inherit = 'tcv.base.import'

    _description = ''

    _import_settings = {'get_document_sql':'select * from prov where co_prov = %s',
                        'get_lines_sql':''}

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
        #~ so_brw = self.browse(cr,uid,ids,context=context)[0]
        
        updated_data = {'name':name,
                        'origin':document['n_control'],
                        'date_order':self.encode_date(document['fec_emis']),
                        'partner_ref':document['nro_fact'],
                        'partner_id':partner_id,
                        'partner_address_id':address_id,
                        'profit_doc':int(document['nro_doc']),
                        'profit_db':profit_config.id,
                        'notes':'Documento importado desde Profit\n\tFactura de Compra Nro: %s Control: %s\n\tobservaciones: %s\n\tImportado el: %s\n\tMoneda:%s'%(document['nro_doc'],document['n_control'],document['observa'],time.strftime('%Y-%m-%d %H:%M:%S'),document['moneda'])}
                        
        if context.get('active_model') == u'purchase.order' and context.get('active_id'):
            obj_sor = self.pool.get('purchase.order')
            obj_sor.write(cr,uid,context['active_id'],updated_data,context=context)
        return updated_data
        
        
    def _update_lines_data(self,cr,uid,ids,lines,context=None): 
        res = []
        document = context.get('document',{})
        if lines == []:
            lines = self._create_detail_line(cr,uid,ids,context)
        if lines == []:
            raise osv.except_osv(_('Error!'),_('No se encontraron lineas, debe indicar un producto para %s')%document.get('observa',''))
        obj_prd = self.pool.get('product.product')
        for line in lines:
            profit_config = context.get('profit_config')
            
            if line.get('product_id'): ## only for _create_detail_line case
                product_id = line['product_id']
            else:
                product_id = self._get_profit_code(cr, uid, 'product.product', 'co_art', line['co_art'])
            if not product_id:
                print line
                product_ids = obj_prd.search(cr, uid, [('default_code', '=', line['co_art'])])
                if len(product_ids) != 1:
                    raise osv.except_osv(_('Error!'),_('No se encontró el producto: %s')%line['co_art'])
                else:
                    product_id = product_ids[0]
            product = obj_prd.browse(cr,uid,product_id,context=context)
            
            tax_id = self.decode_tax_id(cr, uid, line['tipo_imp'], 'Compras')
                
            lot_id = 0
            lot = {}
            pieces = 0
            if line['nro_lote'] and line['aux02']:
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
                           'date':document.get('fe_us_in'),
                           }
                    lot.update(aux02)
                    if product.stock_driver in ['slab','tile']:
                        lot.update({'width':0})
                    pieces = aux02['pieces']
                    lot_id = obj_lot.create(cr,uid,lot,context)
            
            line_data = {'product_id':product_id,
                         'product_uom':product.uom_id.id,
                         'name':line.get('name',product.name),
                         'concept_id':product.concept_id.id,
                         'product_qty':line['total_art'],
                         'price_unit':line['prec_vta'],
                         'taxes_id':[(4,tax_id)] if tax_id else 0,
                         'date_planned':self.encode_date(document.get('fec_emis')),
                         'prod_lot_id':lot_id,
                         'pieces':pieces
                        }
                        
            res.append((0,0,line_data))
        if res and context.get('active_model') == u'purchase.order' and context.get('active_id'):
            obj_sor = self.pool.get('purchase.order')
            obj_sor.write(cr,uid,context['active_id'],{'order_line':res},context=context)
        return res

    ##------------------------------------------------------------------------------------ function fields

    _columns = {
        'product_id': fields.many2one('product.product', 'Product', ondelete='restrict', help="Producto para la factura sin detalle (Documentos de compra)"),
        'partner_id': fields.many2one('res.partner', 'Partner', , ondelete='restrict', help="Proveedor para la factura (Sin equivalente)"),
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

tcv_res_partner_import()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
