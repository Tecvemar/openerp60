# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description:
#       Wizard to import multime account moves
#
##############################################################################

#~ from datetime import datetime
from osv import fields, osv
#~ from tools.translate import _
#~ import pooler
#~ import decimal_precision as dp
#~ import time
import cStringIO
import base64


##------------------------------------------------------- tcv_txt_profit_export


class tcv_txt_lookup_export(osv.osv_memory):

    _name = 'tcv.txt.lookup.export'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'name': fields.char('Filename', 64, readonly=True),
        'csv_file': fields.binary('TXT file', readonly=True,
                                  filters='*.txt', help="TXT file name"),
        }

    _defaults = {
        }

    _sql_constraints = [
        ]

    ##-----------------------------------------------------

    ##----------------------------------------------------- public methods

    ##----------------------------------------------------- buttons (object)

    def button_create_csv(self, cr, uid, ids, context):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        for item in self.browse(cr, uid, ids, context={}):
            res = []
            uom_obj = self.pool.get('product.uom')
            obj_loc = self.pool.get('tcv.stock.by.location.report')
            obj_prd = self.pool.get('product.product')
            obj_so = self.pool.get('sale_order')
            so_ids = obj_so.search(
                cr, uid, [('origin', '=', 'RESERVA_ACROPOLIS_201701')])
            loc_data_id = 0
            for location in (105, 1427, 1455, 1475):
                loc_data_id = obj_loc.create(
                    cr, uid, {'location_id': location}, context)
                obj_loc.button_load_inventory(
                    cr, uid, loc_data_id, context=context)
                loc_brw = obj_loc.browse(
                    cr, uid, loc_data_id, context=context)
                for line in loc_brw.line_ids:
                    reserved = 0
                    for sol in line.prod_lot_id.sale_lines_ids:
                        if sol.order_id.state != 'cancel':
                            if not (sol.order_id.id in so_ids and \
                                    uid in (3, 11)):
                                reserved += sol.product_uom_qty
                    product_qty = line.product_qty - reserved
                    pieces = uom_obj._compute_pieces(
                        cr, uid, line.product_id.stock_driver,
                        product_qty, line.prod_lot_id.lot_factor,
                        context=context)
                    if line.product_id.stock_driver in ('tile', 'slab') and \
                            line.product_qty > reserved:
                        list_price = obj_prd.get_property_list_price(
                            cr, uid, line.prod_lot_id.product_id,
                            line.prod_lot_id, None)
                        reng = (line.prod_lot_id.name,
                                line.product_id.default_code,
                                '%.3fx%.3f' % (line.prod_lot_id.length,
                                               line.prod_lot_id.heigth),
                                '%.4f%s' % (product_qty,
                                            line.uom_id.name),
                                '%s' % line.location_id.name,
                                '%.2f' % (list_price),
                                '%.2f' % (list_price * line.product_qty),
                                '%s' % pieces,
                                )
                        res.append(';'.join(reng))
            data = '\r\n'.join(res)
            buf = cStringIO.StringIO()
            buf.write(data.encode('latin-1'))
            output_file = base64.encodestring(buf.getvalue())
            buf.close()
            return self.write(
                cr, uid, ids, {
                    'csv_file': output_file,
                    'name': 'lookup.txt'},
                context=context)

    ##----------------------------------------------------- on_change...

    ##----------------------------------------------------- create write unlink

    ##----------------------------------------------------- Workflow

tcv_txt_lookup_export()
