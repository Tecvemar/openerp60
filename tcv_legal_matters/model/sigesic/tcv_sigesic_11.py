# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2014-02-18
#    Version: 0.0.0.1
#
#    Description:
#
#
##############################################################################

#~ from datetime import datetime
from osv import fields, osv
#~ from tools.translate import _
#~ import pooler
#~ import decimal_precision as dp
#~ import time
#~ import netsvc


##------------------------------------------------------------ tcv_sigesic_1101


class tcv_sigesic_1101(osv.osv):

    _name = 'tcv.sigesic.1101'

    _description = 'Supplier\'s data\n' + \
                   'Datos de los Proveedores'

    _csv_file_name = 'proveedores_%s.csv'

    _goods_ids = []

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    def _csv_header(self, cr, uid, ids, context):
        return (
            'CODIGO ARANCELARIO',
            'NOMBRE DEL INSUMO',
            'ESPECIFICACIONES TECNICAS',
            'MARCA',
            'UNIDAD DE MEDIDA',
            'PESO UNITARIO (KG/U)',
            'NOMBRE DEL PROVEEDOR',
            'NACIONALIDAD DEL PROVEEDOR (V/E)',
            'RIF DEL PROVEEDOR',
            'PAIS DE PROCEDENCIA DEL INSUMO',
            'PAIS DE ORIGEN DEL INSUMO',
            'UNIDADES COMPRADAS ANHO CONCLUIDO',
            'MONTO TOTAL COMPRADO ANHO CONCLUIDO (Bs.)'
            )

    ##-------------------------------------------------------------------------

    _columns = {
        'input_id': fields.many2one(
            'tcv.sigesic.0901', 'Inputs/raw mat.', ondelete='restrict',
            required=False,
            help="Nombre del Insumo, Marca y Especificacione s técnicas"),
        'partner_id': fields.many2one(
            'res.partner', 'Supplier', readonly=False,
            required=False, ondelete='restrict',
            help="Nombre de la Unidad Económica que Provee el Insumo."),
        'qty_buy': fields.float(
            'Quantity', digits=(15, 2), readonly=False,
            help="Unidades compradas en el año concluido"),
        'amount_buy': fields.float(
            'Amount', digits=(15, 2), readonly=False,
            help="Monto total comprado en el año concluido expresado en Bs."),
        'data_year': fields.integer(
            'Year', required=True,
            help="El año al que corresponden los datos"),
        }

    _defaults = {
        'qty_buy': lambda *a: 0,
        'amount_buy': lambda *a: 0,
        }

    _sql_constraints = [
        ('qty_buy_gt_zero', 'CHECK (qty_buy>=0)',
         'The quantity must be >= 0 !'),
        ('amount_buy_gt_zero', 'CHECK (amount_buy>=0)',
         'The Amount must be >= 0 !'),

        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    def get_data_lines_ids(self, cr, uid, line_id, data_year, context):
        return self.search(
            cr, uid, [('data_year', '=', data_year)])

    def get_data_line(self, cr, uid, line_id, context):

        def str_uom(uom):
            uoms = {'m2': u'm²',
                    'm3': u'm³',
                    'Unidad': u'unid',
                    'ml': u'm',
                    }
            return uom and uoms.get(uom, uom) or ''

        def str_line(line):
            return line and line.replace(';', ',').strip() or ''

        line = self.browse(cr, uid, line_id, context=context)
        addr = [addr for addr in line.partner_id.address if
                addr.type == 'invoice'][0]
        return (str_line(line.input_id.hs_code_id and
                         line.input_id.hs_code_id.code),
                str_line(line.input_id.name),
                str_line(line.input_id.tech_specs),
                str_line(line.input_id.product_id and
                         line.input_id.product_id.name),
                str_uom(line.input_id.uom_id and line.input_id.uom_id.name),
                str_line('%.2f' % line.input_id.weight),
                str_line(line.partner_id.name),
                str_line('V' if line.partner_id.vat[:2] == 'VE' else 'E'),
                str_line(line.partner_id.rif),
                str_line(addr.country_id.name),
                str_line(line.input_id.product_id.origin_country_id.name),
                str_line('%.2f' % line.qty_buy),
                str_line('%.2f' % line.amount_buy),
                )

    ##-------------------------------------------------------- buttons (object)

    def button_refresh(self, cr, uid, ids, context=None):
        obj_inp = self.pool.get('tcv.sigesic.0901')
        obj_pnr = self.pool.get('res.partner')
        cr.execute("select max(data_year) from tcv_sigesic_0901")
        data_year = cr.fetchone()[0]
        for i in obj_inp.get_data_lines_ids(
                cr, uid, ids, data_year, context):
            inp = obj_inp.browse(cr, uid, i, context=context)
            for s in inp.product_id.seller_ids:
                p = s.name
                if not self.search(cr, uid, [('input_id', '=', i),
                                             ('partner_id', '=', p.id)]):
                    data = {'data_year': data_year,
                            'input_id': inp.id,
                            'partner_id': p.id}
                    if inp.supplier_qty == 1:
                        data.update(
                            {'qty_buy': inp.local_qty + inp.import_qty,
                             'amount_buy': inp.local_cost + inp.import_cost,
                             })
                    self.create(cr, uid, data, context)
        return True

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_sigesic_1101()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
