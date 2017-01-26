# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date: 26/11/2012
#    Version: 0.0.0.0
#
#    Description: Gets a CSV file from data collector and import it to 
#                 sale order
#
##############################################################################
from datetime import datetime
from osv import fields,osv
from tools.translate import _
import pooler
import decimal_precision as dp
import time
import netsvc
import csv
import base64

##---------------------------------------------------------------------------------------- tcv_sale_data_collector

class tcv_sale_order_csv_import(osv.osv_memory):

    _name = 'tcv.sale.order.csv.import'

    _description = ''

    ##------------------------------------------------------------------------------------

    ##------------------------------------------------------------------------------------ _internal methods

    ##------------------------------------------------------------------------------------ function fields

    _columns = {
        'name': fields.char('File name', size=256, readonly=True),
        'obj_file': fields.binary('CSV file', required=True, filters='*.csv',help="CSV file name"),
        }

    _defaults = {
        }

    _sql_constraints = [        
        ]

    ##------------------------------------------------------------------------------------

    ##------------------------------------------------------------------------------------ public methods

    ##------------------------------------------------------------------------------------ buttons (object)
    
    def process_csv(self, cr, uid, ids, context=None):
        so_brw = self.browse(cr,uid,ids,context={})[0]
        file = so_brw.obj_file
        file_import = base64.decodestring(file)

        try:
            unicode(file_import, 'utf8')
        except Exception, e: # If we can not convert to UTF-8 maybe the file is codified in ISO-8859-1: We convert it.
            file_import = unicode(file_import, 'iso-8859-1').encode('utf-8')

        file_import = file_import.split('\n')
        #~ factura pedido cliente fecha
        reader = csv.DictReader(file_import, fieldnames=['inv_name','name','cliente','fecha','anulada'],delimiter=';', quotechar='"')

        obj_imp = self.pool.get('tcv.sale.order.import')
        obj_ord = self.pool.get('sale.order')
        
        save_context = context
        context.update({'tcv_sale_order_csv_import':True,'error_list':[],'partner_list':[]})
        lines = []
        last_inv = ''
        imp_id = []
        partner_id = 4674
        partner = self.pool.get('res.partner').browse(cr,uid,partner_id,context=context)
        address_id = 0
        for address in partner.address:
            if address.type == 'invoice':
                address_id = address.id
        ord_id = 0
        order_data = {
                        'partner_id':partner_id,
                        'partner_invoice_id':address_id,
                        'partner_order_id':address_id,
                        'partner_shipping_id':address_id,
                        }
        delta = 0
        for row in reader:
            delta += 1
            row.pop('fecha')
            row.pop('cliente')
            if row.pop('anulada') == '0':
                print 'Procesando:',row
                order_data.update({ 'name':'%s-%s'%(row['name'],delta),                        
                                    })
                try:
                    if row['inv_name'] != last_inv:
                        if imp_id:
                            obj_imp.unlink(cr,uid,[imp_id],context)        
                        ord_id = obj_ord.create(cr,uid,order_data,context)
                        context.update({'active_id':ord_id,'active_ids':[ord_id]})
                        last_inv = row['inv_name']
                        imp_id = obj_imp.create(cr,uid,row,context)
                    else:
                        obj_imp.write(cr,uid,[imp_id],row,context)    
                    obj_imp.import_button_click(cr,uid,[imp_id],context)
                except Exception as inst:
                    print u'error en: %s\n%s\n%s'%(row,inst,inst.args)
                    pass  
        #~ if context.get('error_list'):
            #~ f = open('/home/jmarquez/instancias/produccion/migration_data/data/tcv_sale_order_partners.csv', 'w')
            #~ f.write("\n".join(context['partner_list']).encode('utf-8'))
            #~ f.close()
            #~ f = open('/home/jmarquez/instancias/produccion/migration_data/data/tcv_sale_order_csv_import.csv', 'w')
            #~ f.write("\n".join(context['error_list']).encode('utf-8'))
            #~ f.close()
        context.pop('tcv_sale_order_csv_import')
        context.pop('error_list')
        context.update(save_context)
        print 'Proceso finalizado.\n'
        return {'type': 'ir.actions.act_window_close'}

    ##------------------------------------------------------------------------------------ on_change...

    ##------------------------------------------------------------------------------------ create write unlink

    ##------------------------------------------------------------------------------------ Workflow

tcv_sale_order_csv_import()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
