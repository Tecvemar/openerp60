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

##------------------------------------------------------------ tcv_sigesic_1201


class tcv_sigesic_1201(osv.osv):

    _name = 'tcv.sigesic.1201'

    _description = 'Marketed Goods\n' + \
                   'Bienes Comercializados No producidos por la U.E.'

    _csv_file_name = 'bienes_comercializacion_%s.csv'

    def _csv_header(self, cr, uid, ids, context):
        return (
            'CODIGO ARANCELARIO',
            'NOMBRE DEL BIEN',
            'ESPECIFICACIONES TECNICAS',
            'MARCA',
            'UNIDAD DE MEDIDA',
            'ORIGEN NACIONAL (SI/NO)',
            'PESO UNITARIO (KG/U)',
            'CANTIDAD VENDIDA ANHO CONCLUIDO',
            'MONTO TOTAL FACTURADO ANHO CONCLUIDO (Bs.)'
            )

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'hs_code_id': fields.many2one('tcv.sigesic.9901', 'HS Code',
                                      ondelete='restrict'),
        'name': fields.char('Name', size=64, required=False, readonly=False,
                            help="Denominación o nombre comercial del " +
                            "producto"),
        'product_id': fields.many2one('product.product', 'Product',
                                      ondelete='restrict', required=True),
        'tech_specs': fields.related('product_id', 'tech_specs', type='text',
                                     string='Tech specs', store=False,
                                     readonly=True,
                                     help="Composición o características " +
                                     "físicas y/o químicas del producto"),
        'uom_id': fields.related('product_id', 'uom_id', type='many2one',
                                 relation='product.uom', string='Uom',
                                 store=False, readonly=True),
        'local_good': fields.selection([('yes', 'Si'),
                                        ('no', 'No')], string='Local good'),
        'weight': fields.related('product_id', 'weight', type='float',
                                 string='Gross weight', store=False,
                                 readonly=True),
        'sale_qty': fields.float('Sale qty', digits=(15, 2), readonly=False,
                                 help="Cantidad total vendida del bien, " +
                                 "para el año inmediatamente concluido, de " +
                                 "acuerdo a la Udm"),
        'sale_amount': fields.float('Sale amount', digits=(15, 2),
                                    readonly=False,
                                    help="Monto total facturado del bien " +
                                    "expresado en Bs., para el año " +
                                    "inmediatamente concluido."),
        'data_year': fields.integer(
            'Year', required=True,
            help="El año al que corresponden los datos"),
        }

    _defaults = {
        }

    _sql_constraints = [
        ('product_id_uniq', 'UNIQUE(data_year, product_id)',
         'The product must be unique!'),
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
        return (str_line(line.hs_code_id and line.hs_code_id.code),
                str_line(line.name),
                str_line(line.tech_specs),
                str_line(line.product_id and line.product_id.name),
                str_uom(line.uom_id and line.uom_id.name),
                str_uom('SI' if line.local_good == 'yes' else 'NO'),
                str_line('%.2f' % line.weight),
                str_line('%.2f' % line.sale_qty),
                str_line('%.2f' % line.sale_amount),
                )

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    def on_change_hs_code_id(self, cr, uid, ids, hs_code_id, product_id):
        if product_id and hs_code_id:
            obj_prd = self.pool.get('product.product')
            prd = obj_prd.browse(cr, uid, product_id, context=None)
            if not prd.hs_code or hs_code_id != prd.hs_code:
                obj_hsc = self.pool.get('tcv.sigesic.9901')
                hsc = obj_hsc.browse(cr, uid, hs_code_id, context=None)
                obj_prd.write(cr, uid, prd.id, {'hs_code': hsc.code},
                              context=None)
        return {'value': {}}

    def on_change_product_id(self, cr, uid, ids, product_id):
        res = {}
        if product_id:
            obj_prd = self.pool.get('product.product')
            prd = obj_prd.browse(cr, uid, product_id, context=None)
            cntry = prd.origin_country_id and prd.origin_country_id.code or ''
            res.update({'tech_specs': prd.tech_specs,
                        'uom_id': prd.uom_id.id,
                        'weight': prd.weight,
                        'local_good': 'yes' if cntry == 'VE' else 'no'})
            if prd.hs_code:
                ids = self.pool.get('tcv.sigesic.9901').\
                    search(cr, uid, [('code', '=', prd.hs_code)])
                if ids and len(ids) == 1:
                    res.update({'hs_code_id': ids[0]})
        return {'value': res}

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_sigesic_1201()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
