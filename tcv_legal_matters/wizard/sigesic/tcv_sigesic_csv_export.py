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
from tools.translate import _
#~ import pooler
#~ import decimal_precision as dp
import time
import cStringIO
import base64


##------------------------------------------------------ tcv_sigesic_csv_export


class tcv_sigesic_csv_export(osv.osv):

    _name = 'tcv.sigesic.csv.export'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'name': fields.char('Filename', 64, readonly=True),
        'data_year': fields.integer(
            'Year', required=True,
            help="El año al que corresponden los datos"),
        'csv_file': fields.binary('TXT file', readonly=True,
                                  filters='*.csv', help="CSV file name"),
        'type': fields.selection(
            [('tcv.sigesic.0901',
              '0901 - Inputs and/or raw materials required'),
             ('tcv.sigesic.0902',
              '0902 - Goods produced'),
             ('tcv.sigesic.0903',
              '0903 - Raw materials / Goods relation'),
             ('tcv.sigesic.1001',
              '1001 - Machinery (unavaible)'),
             ('tcv.sigesic.1101',
              '1101 - Suppliers'),
             ('tcv.sigesic.1201',
              '1201 - Marketed Goods not produced by the Economic Unit'),
             ],
            string='Model', required=True),
        }

    _defaults = {
        'data_year': lambda *a: int(time.strftime('%Y')) - 1,
        }

    _sql_constraints = [
        ]

    ##-----------------------------------------------------

    ##----------------------------------------------------- public methods

    ##----------------------------------------------------- buttons (object)

    def button_create_csv(self, cr, uid, ids, context):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        context = context or {}
        for item in self.browse(cr, uid, ids, context={}):
            if item.data_year < 2012 or item.data_year > 2099:
                raise osv.except_osv(
                    _('Error!'),
                    _('The year must be in 2012-2099 range.'))
            res = []
            obj_data = self.pool.get(item.type)
            context.update({'data_year': item.data_year})
            header = ';'.join(obj_data._csv_header(cr, uid, ids, context))
            res.append(header)
            line_ids = obj_data.get_data_lines_ids(
                cr, uid, ids, item.data_year, context)
            if not line_ids:
                raise osv.except_osv(
                    _('Error!'),
                    _('Can\'t find any data.'))
            for line_id in line_ids:
                line = obj_data.get_data_line(cr, uid, line_id, context)
                res.append(';'.join(line))
            data = '\n'.join(res)
            buf = cStringIO.StringIO()
            buf.write(data.encode('utf-8'))
            output_file = base64.encodestring(buf.getvalue())
            buf.close()
            return self.write(
                cr, uid, ids, {
                    'csv_file': output_file,
                    'name': obj_data._csv_file_name % item.data_year},
                context=context)

    ##----------------------------------------------------- on_change...

    ##----------------------------------------------------- create write unlink

    ##----------------------------------------------------- Workflow

tcv_sigesic_csv_export()
