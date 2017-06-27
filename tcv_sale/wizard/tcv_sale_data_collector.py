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
#~ from datetime import datetime
from osv import fields, osv
from tools.translate import _
#~ import pooler
#~ import decimal_precision as dp
#~ import time
#~ import netsvc
import csv
import base64

##----------------------------------------------------- tcv_sale_data_collector


class tcv_sale_data_collector(osv.osv_memory):

    _name = 'tcv.sale.data.collector'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'name': fields.char('File name', size=128, readonly=True),
        'obj_file': fields.binary('TXT file', required=True, filters='*.txt',
                                  help="TXT file name"),
        }

    _defaults = {
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    def create_order_lines(self, cr, uid, ids, lot_list, context=None):
        '''
        lot_list is list of dict
        sample = [{'co_art': 'KASWHIBP101A', 'prod_lot': '01101',
                   'location': 'D0202', 'pieces': 12},
                  {'co_art': 'KASWHIBP101A', 'prod_lot': '01102',
                   'location': 'D0202', 'pieces': 12}]
        sample2 = [{'prod_lot_id': 120, 'pieces': 12}]
        only need: (prod_lot or prod_lot_id) and pieces
        '''
        lines = []
        obj_lot = self.pool.get('stock.production.lot')
        obj_prd = self.pool.get('product.product')

        for row in lot_list:
            prod_lot_id = [row['prod_lot_id']] if row.get('prod_lot_id') else \
                obj_lot.search(cr, uid, [('name', '=', row['prod_lot'])])
            if prod_lot_id and len(prod_lot_id) == 1:
                prod_lot_id = prod_lot_id[0]
                lot = obj_lot.browse(cr, uid, prod_lot_id, context=context)
                taxes = []
                for tax in lot.product_id.taxes_id:
                    taxes.append((4, tax.id))
                list_price = obj_prd.get_property_list_price(
                    cr, uid, lot.product_id, lot, None) or 0
                pieces = int(row['pieces'])
                data = {'product_id': lot.product_id.id,
                        'concept_id': lot.product_id.concept_id.id,
                        'prod_lot_id': prod_lot_id,
                        'pieces': pieces,
                        'product_uom_qty': lot.lot_factor * pieces or
                        row.get('product_qty', 0),
                        'product_uos_qty': lot.lot_factor * pieces or
                        row.get('product_qty', 0),
                        'product_uom': lot.product_id.uom_id.id,
                        'name': lot.product_id.name,
                        'price_unit': list_price,
                        'type': 'make_to_stock',
                        'delay': lot.product_id.sale_delay,
                        'tax_id': taxes,
                        }
                lines.append((0, 0, data))
        return lines

    def create_wizard_lines(self, cr, uid, ids, lot_list, context=None):
        '''
        lot_list is list of dict
        sample = [{'co_art': 'KASWHIBP101A', 'prod_lot': '01101',
                   'location': 'D0202', 'pieces': 12},
                  {'co_art': 'KASWHIBP101A', 'prod_lot': '01102',
                   'location': 'D0202', 'pieces': 12}]
        sample2 = [{'prod_lot_id': 120, 'pieces': 12}]
        only need: (prod_lot or prod_lot_id) and pieces
        '''
        lines = []
        obj_lot = self.pool.get('stock.production.lot')
        obj_prd = self.pool.get('product.product')

        for row in lot_list:
            prod_lot_id = [row['prod_lot_id']] if row.get('prod_lot_id') else \
                obj_lot.search(cr, uid, [('name', '=', row['prod_lot'])])
            if prod_lot_id and len(prod_lot_id) == 1:
                prod_lot_id = prod_lot_id[0]
                lot = obj_lot.browse(cr, uid, prod_lot_id, context=context)
                list_price = float(
                    obj_prd.get_property_list_price(
                        cr, uid, lot.product_id, lot, None) or 0)
                pieces = int(row['pieces'])
                data = {'product_id': lot.product_id.id,
                        'prod_lot_id': prod_lot_id,
                        'max_pieces': pieces,
                        'pieces': pieces,
                        'product_qty': lot.lot_factor * pieces,
                        'price_unit': list_price,
                        }
                lines.append((0, 0, data))
        return lines

    ##-------------------------------------------------------- buttons (object)

    def process_lots(self, cr, uid, ids, context=None):
        context = context or {}
        so_brw = self.browse(cr, uid, ids, context={})[0]
        file = so_brw.obj_file
        file_import = base64.decodestring(file)
        try:
            unicode(file_import, 'utf8')
        except Exception:  # If we can not convert to UTF-8 maybe the file
            #                is codified in ISO-8859-1: We convert it.
            file_import = unicode(file_import, 'iso-8859-15').encode('utf-8')

        file_import = file_import.split('\n')
        test_line = file_import[0]
        delim = ';'
        test_struct = len(test_line.split(delim))
        if test_struct == 5:
            field_list = ['co_art', 'prod_lot', 'location', 'pieces',
                          'price_unit']
        elif test_struct == 4:
            field_list = ['co_art', 'prod_lot', 'location', 'pieces']
        elif len(test_line.split(',')) == 3:
            delim = ','
            field_list = ['prod_lot', 'location', 'pieces']
        else:
            raise osv.except_osv(
                _('Error!'),
                _('Invalid file format. Verify that the file line\'s has ' +
                  'one of the following formats:\n' +
                  '\tco_art;prod_lot;location;pieces;price_unit\n' +
                  '\tco_art;prod_lot;location;pieces\n' +
                  '\tprod_lot,location,pieces'))
        reader = csv.DictReader(file_import, fieldnames=field_list,
                                delimiter=delim, quotechar='"')
        if context.get('active_model') == 'tcv.sale.lot.list' and \
                context.get('active_ids'):
            obj_so = self.pool.get('tcv.sale.lot.list')
            lines = self.create_wizard_lines(
                cr, uid, ids, reader, context=context)
            if lines:
                obj_so.write(cr, uid, context.get('active_ids'),
                             {'line_ids': lines}, context)
        return {'type': 'ir.actions.act_window_close'}

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow


tcv_sale_data_collector()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
