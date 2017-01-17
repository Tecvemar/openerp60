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


class tcv_txt_profit_export(osv.osv_memory):

    _name = 'tcv.txt.profit.export'

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
            obj_so = self.pool.get('sale_order')
            if context.get('active_model') == u'sale.order' and \
                    context.get('active_id'):
                so_id = context.get('active_id')
                obj_so = self.pool.get('sale.order')
                so_brw = obj_so.browse(cr, uid, so_id, context=context)
                for line in so_brw.order_line:
                    reng = (line.product_id.default_code,
                            '001',
                            '%.4f' % line.product_uom_qty,
                            line.prod_lot_id.name,
                            '%.4f' % line.price_unit,
                            '%.3f;%.3f;%.3f;%s' % (
                                line.pieces,
                                line.prod_lot_id.length,
                                line.prod_lot_id.heigth,
                                'ACRO'),
                            '1',
                            )
                    res.append('\t'.join(reng))
                data = '\r\n'.join(res)
                buf = cStringIO.StringIO()
                buf.write(data.encode('latin-1'))
                output_file = base64.encodestring(buf.getvalue())
                buf.close()
                return self.write(
                    cr, uid, ids, {
                        'csv_file': output_file,
                        'name': 'captura_inventario_%s.txt' % so_brw.name},
                    context=context)

    ##----------------------------------------------------- on_change...

    ##----------------------------------------------------- create write unlink

    ##----------------------------------------------------- Workflow

tcv_txt_profit_export()
