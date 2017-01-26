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

class tcv_sale_order_import(osv.osv_memory):

    _name = 'tcv.sale.order.import'

    _inherit = 'tcv.base.import'

    _description = ''

    _import_settings = {'get_document_sql':'select * from pedidos where fact_num = %s and anulada = 0',
                        'get_lines_sql':'select * from reng_ped where fact_num = %s order by reng_num'}

    ##------------------------------------------------------------------------------------
    
    def default_get(self, cr, uid, fields, context=None):
        data = super(tcv_sale_order_import, self).default_get(cr, uid, fields, context)
        if context.get('active_model') == u'sale.order' and context.get('active_id'):
            ord = self.pool.get('sale.order').browse(cr,uid,context['active_id'],context=context)
            if ord.profit_doc:
                data.update({'name':'%s'%ord.profit_doc})
            if ord.profit_doc:
                data.update({'name_inv':'%s'%ord.profit_inv})
        return data

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
        
        name = 'PED%08d'%document['fact_num']
        
        if not so_brw.partner_id:
            partner_id = self._get_profit_code(cr, uid, 'res.partner', 'co_cli', document['co_cli'])
            if not partner_id:
                str_error = _(u'No se encontro el cliente para la factura: %s')%document.get('co_cli','')
                if context.get('tcv_sale_order_csv_import'):
                    print str_error
                    if context.get('partner_list'):
                        context['partner_list'].append(str_error)
                else:
                    raise osv.except_osv(_('Error!'),str_error)
        else:
            partner_id = so_brw.partner_id.id
        
        obj_pnr = self.pool.get('res.partner')
        partner = obj_pnr.browse(cr,uid,partner_id,context=context)
        
        address_id = 0
        for address in partner.address:
            if address.type == 'invoice':
                address_id = address.id
        
        user_id = 0
        user_name = self.profit_2_openerp_salesman(profit_config.company_ref,document['co_ven'])
        obj_usr = self.pool.get('res.users')
        user_ids = obj_usr.search(cr, uid, [('login', '=', user_name)])
        if not user_ids or len(user_ids) != 1:
            return {}
        user_id = user_ids[0]
        
        date = self.encode_date(document['fec_emis'])
        if date < '2013-01-01':
            date = '2013-01-01'
            
        note = 'Documento importado desde Profit\n\tPedido Nro: %s, Factura Nro: %s' \
               '\n\tObservaciones: %s\n\tImportado el: %s' \
               '\n\tMonto original: %s'% \
               (document['fact_num'],so_brw.inv_name,
                document.get('descrip',''),
                time.strftime('%Y-%m-%d %H:%M:%S'),document.get('tot_neto'))
        
        updated_data = {'name':name,
                        'date_order':date,
                        'create_date':date,
                        'partner_id':partner_id,
                        'partner_invoice_id':address_id,
                        'partner_order_id':address_id,
                        'partner_shipping_id':address_id,
                        'user_id':user_id,
                        'client_order_ref':document.get('tot_neto'),
                        'profit_doc':int(document['fact_num']),
                        'profit_inv':so_brw.inv_name,
                        'profit_db':profit_config.id,                        
                        'note':note}
        if context.get('active_model') == u'sale.order' and context.get('active_id'):
            obj_sor = self.pool.get('sale.order')
            order = obj_sor.browse(cr,uid,context['active_id'],context=context)
            ord_ids = obj_sor.search(cr, uid, [('name', 'ilike', name)])
            if ord_ids:
                updated_data.update({'name':'%s-%s'%(name,len(ord_ids))})
            if order and order.note:
                updated_data.update({'note':'%s\n%s'%(order.note,note)})
            obj_sor.write(cr,uid,context['active_id'],updated_data,context=context)
        return updated_data
        
        
    def _update_lines_data(self,cr,uid,ids,lines,context=None): 
        res = []
        obj_prd = self.pool.get('product.product')
        obj_lot = self.pool.get('stock.production.lot')
        str_error = ''
        error_list = context.get('error_list',[])
        lines.reverse()
        for line in lines:
            profit_config = context.get('profit_config')
            
            if line['co_art'] == 'ROSCARLS201':
                line.update({'co_art':'CARIBELS201'})
            
            product_id = self._get_profit_code(cr, uid, 'product.product', 'co_art', line['co_art'])
            if not product_id:
                return {}
            product = obj_prd.browse(cr,uid,product_id,context=context)
            
            tax_id = product.taxes_id[0].id
            
            line_data = {'product_id':product_id,
                         'product_uom':product.uom_id.id,
                         'name':product.name,
                         'concept_id':product.concept_id.id,
                         'product_uom_qty':line['total_art'],
                         'product_uos_qty':line['total_art'],
                         'price_unit':line['prec_vta'],
                         'tax_id':[(4,tax_id)],
                        }
             
            if line['nro_lote']:
                prod_lot_id = obj_lot.search(cr, uid, [('name', '=', line['nro_lote']),('product_id','=',product_id)])
                if prod_lot_id and len(prod_lot_id) == 1:
                    line_data.update({'prod_lot_id':prod_lot_id[0]})
                    if line['aux02']:
                        aux02 = self.decode_aux02(line['aux02'])
                        line_data.update({'pieces':aux02['pieces']})
                else:
                    if not str_error:
                        str_error = u'Error, lote(s) inexistente(s):'
                    str_error = '%s\n(%s) %s'%(str_error,line['nro_lote'].strip(),product.name)
                    error_list.append('"%s";"%s";%s;0'%(line['co_art'].strip(),line['nro_lote'].strip(),line['aux02'].strip()))
            res.append((0,0,line_data))
        if str_error: 
            if context.get('tcv_sale_order_csv_import'):
                print str_error
                context.update({'error_list':error_list})
            else:
                raise osv.except_osv(_('Error!'),str_error)        
        
        if res and context.get('active_model') == u'sale.order' and context.get('active_id'):
            obj_sor = self.pool.get('sale.order')
            data = {'order_line':res}
            if str_error:
                data.update({'client_order_ref':'Error'})
            obj_sor.write(cr,uid,context['active_id'],data,context=context)
        return res

    ##------------------------------------------------------------------------------------ function fields

    _columns = {
        'inv_name': fields.char('Invoice number', 32, readonly=False, required=True),
        'partner_id': fields.many2one('res.partner', 'Partner', ondelete='restrict', help="Indique el cliente para la factura"),
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

tcv_sale_order_import()


class tcv_profit_invoice_import(osv.osv_memory):

    _name = 'tcv.profit.invoice.import'

    _inherit = 'tcv.base.import'

    _description = ''

    _import_settings = {'get_document_sql':'select * from factura where fact_num = %s and anulada = 0',
                        'get_lines_sql':'select * from reng_fac where fact_num = %s order by reng_num'}

tcv_profit_invoice_import()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
