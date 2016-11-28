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


##----------------------------------------- tcv_mrp_finished_product_txt_export

class tcv_mrp_finished_product_txt_export(osv.osv_memory):

    _name = 'tcv.mrp.finished.product.txt.export'

    _description = ''

    ##-------------------------------------------------------------------------

    def create_txt_profit(self, cr, uid, ids, obj_fin, context):
        buf = cStringIO.StringIO()
        for output in obj_fin.output_ids:
            l = ['ENT',
                 output.product_id.default_code,
                 '001',
                 'MT2',
                 '%.4f' % output.total_area,
                 output.prod_lot_ref,
                 '%.2f' % output.real_unit_cost,
                 '1',
                 '%.3f;%.3f;%.3f;%s' % (
                     output.pieces, output.length,
                     output.heigth, output.location_id.name)
                 ]
            str = ''
            for x in l:
                str = '%s\t%s' % (str, x) if str else x
            buf.write('%s\n' % str)
        out = base64.encodestring(buf. getvalue())
        buf.close()
        return out

    ##--------------------------------------------------------- function fields

    _columns = {
        'name': fields.char('Filename', 64, readonly=True),
        'txt_file': fields.binary(
            'TXT file', readonly=True, filters='*.txt', help="TXT file name"),
        'advice': fields.text('Advice', readonly=True),
        }

    _defaults = {

        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_mrp_finished_product_txt_export()
