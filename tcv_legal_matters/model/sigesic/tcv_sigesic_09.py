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

##------------------------------------------------------------ tcv_sigesic_0901


class tcv_sigesic_0901(osv.osv):

    _name = 'tcv.sigesic.0901'

    _description = 'Inputs and/or raw materials required\n' + \
                   'Insumos y/o Materia Prima requerida'

    _csv_file_name = 'insumos_materia_prima_%s.csv'

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def _csv_header(self, cr, uid, ids, context):
        return (
            'CODIGO ARANCELARIO',
            'NOMBRE DEL INSUMO',
            'ESPECIFICACIONES TECNICAS',
            'MARCA',
            'UNIDAD DE MEDIDA',
            'PESO UNITARIO (KG/U)',
            'CANTIDAD COMPRADA NACIONAL ANHO CONCLUIDO',
            'CANTIDAD COMPRADA IMPORTADA ANHO CONCLUIDO',
            'PRECIO DE ADQUISICION NACIONAL ANHO CONCLUIDO (Bs.)',
            'PRECIO DE ADQUISICION INTERNACIONAL (FOB) ANHO CONCLUIDO (Bs.)',
            'NUMERO DE PROVEEDORES',
            'SEGUN EL PLAN DE PRODUCCION, QUE CANTIDAD DE UNIDADES ESTIMA ' +
            'NECESITARA EN EL ANHO ACTUAL?',
            )

    def _get_full_name(self, item):
        return '%s. Marca: %s. Esp. Tec.: %s' % \
            (item.name.strip() or '',
             item.product_id and item.product_id.name.strip() or '',
             item.tech_specs.strip() or '')

    def name_get(self, cr, uid, ids, context):
        if not len(ids):
            return []
        res = []
        so_brw = self.browse(cr, uid, ids, context)
        for item in so_brw:
            res.append((item.id, self._get_full_name(item)))
        return res

    ##--------------------------------------------------------- function fields

    _columns = {
        'hs_code_id': fields.many2one('tcv.sigesic.9901', 'HS Code',
                                      ondelete='restrict'),
        'name': fields.char('Name', size=100, required=False, readonly=False,
                            help="Nombre genérico del insumo requerido."),
        'product_id': fields.many2one('product.product', 'Product',
                                      ondelete='restrict', required=True,
                                      help="Denominación o nombre " +
                                      "comercial del producto (Marca)"),
        'tech_specs': fields.related('product_id', 'tech_specs', type='text',
                                     string='Tech specs', store=False,
                                     readonly=True,
                                     help="Composición o características " +
                                     "físicas y/o químicas del producto"),
        'uom_id': fields.related('product_id', 'uom_id', type='many2one',
                                 relation='product.uom', string='Uom',
                                 store=False, readonly=True),
        'weight': fields.related('product_id', 'weight', type='float',
                                 string='Gross weight', store=False,
                                 readonly=True, digits=(3, 5)),
        'local_qty': fields.float('Local qty', digits=(15, 2), readonly=False,
                                  help="Número de unidades compradas en el " +
                                  "mercado nacional, de acuerdo a la Udm"),
        'import_qty': fields.float('Imported qty', digits=(15, 2),
                                   readonly=False,
                                   help="Número de unidades compradas en el " +
                                   "mercado internacional, de acuerdo a la " +
                                   "Udm"),
        'local_cost': fields.float('Local price', digits=(15, 2),
                                   readonly=False),
        'import_cost': fields.float('Imported price', digits=(15, 2),
                                    readonly=False),
        'supplier_qty': fields.integer('Supplier qty'),
        'required_qty': fields.float('Required qty', digits=(15, 2),
                                     readonly=False,
                                     help="Según el Plan de Producción, " +
                                     "número de unidades que estima " +
                                     "necesitará en el año actual, de " +
                                     "acuerdo a la Udm"),
        'seller_ids': fields.related(
            'product_id', 'seller_ids', type='one2many',
            relation='product.supplierinfo', string='Suppliers',
            store=False, readonly=True),
        'data_year': fields.integer(
            'Year', required=True,
            help="El año al que corresponden los datos"),
        }

    _defaults = {
        'supplier_qty': 1,
        }

    _sql_constraints = [
        ('product_id_uniq', 'UNIQUE(data_year,product_id)',
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

        def str_line(name):
            return name and name.replace(';', ',').strip() or ''

        line = self.browse(cr, uid, line_id, context=context)
        return (str_line(line.hs_code_id and line.hs_code_id.code),
                str_line(line.name),
                str_line(line.tech_specs),
                str_line(line.product_id and line.product_id.name),
                str_uom(line.uom_id and line.uom_id.name),
                str_line('%.2f' % line.weight),
                str_line('%.2f' % line.local_qty),
                str_line('%.2f' % line.import_qty),
                str_line('%.2f' % line.local_cost),
                str_line('%.2f' % line.import_cost),
                str_line('%d' % line.supplier_qty),
                str_line('%.2f' % line.required_qty),
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
            supplier_qty = len(prd.seller_ids) or 1
            res.update({'tech_specs': prd.tech_specs,
                        'uom_id': prd.uom_id.id,
                        'weight': prd.weight,
                        'supplier_qty': supplier_qty,
                        })
            if prd.hs_code:
                ids = self.pool.get('tcv.sigesic.9901').\
                    search(cr, uid, [('code', '=', prd.hs_code)])
                if ids and len(ids) == 1:
                    res.update({'hs_code_id': ids[0]})
        return {'value': res}

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_sigesic_0901()


##------------------------------------------------------------ tcv_sigesic_0902


class tcv_sigesic_0902(osv.osv):

    _name = 'tcv.sigesic.0902'

    _description = 'Goods produced\n' + \
                   'Bienes producidos'

    _csv_file_name = 'bienes_%s.csv'

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def _csv_header(self, cr, uid, ids, context):
        return (
            'CODIGO ARANCELARIO',
            'NOMBRE DEL PRODUCTO',
            'ESPECIFICACIONES TECNICAS',
            'MARCA',
            'UNIDAD DE MEDIDA',
            'PESO UNITARIO (KG/U)',
            'CANTIDAD PRODUCIDA ANHO CONCLUIDO',
            'CANTIDAD VENDIDA ANHO CONCLUIDO',
            'MONTO FACTURADO POR VENTA ANUAL (Bs.)',
            '% DE LOS BIENES VENDIDOS AL MERCADO NACIONAL ANHO CONCLUIDO',
            'NUMERO DE UNIDADES ECONOMICAS CLIENTES',
            'SEGUN EL PLAN DE PRODUCCION, QUE CANTIDAD DE UNIDADES ESTIMA ' +
            'PRODUCIRA EN EL ANHO ACTUAL?',
            )

    def _get_full_name(self, item):
        return '%s. Marca: %s. Esp. Tec.: %s' % \
            (item.name.strip() or '',
             item.product_id and item.product_id.name.strip() or '',
             item.tech_specs.strip() or '')

    def name_get(self, cr, uid, ids, context):
        if not len(ids):
            return []
        res = []
        so_brw = self.browse(cr, uid, ids, context)
        for item in so_brw:
            res.append((item.id, self._get_full_name(item)))
        return res

    ##--------------------------------------------------------- function fields

    _columns = {
        'hs_code_id': fields.many2one('tcv.sigesic.9901', 'HS Code',
                                      ondelete='restrict'),
        'name': fields.char('Name', size=100, required=False, readonly=False,
                            help="Nombre genérico delproducto fabricado."),
        'product_id': fields.many2one('product.product', 'Product',
                                      ondelete='restrict', required=True,
                                      help="Denominación o nombre " +
                                      "comercial del producto (Marca)"),
        'tech_specs': fields.related('product_id', 'tech_specs', type='text',
                                     string='Tech specs', store=False,
                                     readonly=True,
                                     help="Composición o características " +
                                     "físicas y/o químicas del producto"),
        'uom_id': fields.related('product_id', 'uom_id', type='many2one',
                                 relation='product.uom', string='Uom',
                                 store=False, readonly=True),
        'weight': fields.related('product_id', 'weight', type='float',
                                 string='Gross weight', store=False,
                                 readonly=True, digits=(8, 3)),
        'qty_prod': fields.float('Qty produced', digits=(15, 2),
                                 readonly=False,
                                 help="Cantidad total fabricada en el año " +
                                 "inmediatamente concluido, de acuerdo a " +
                                 "la Udm"),
        'qty_sale': fields.float('Qty sales', digits=(15, 2),
                                 readonly=False,
                                 help="Cantidad total vendida en el año " +
                                 "inmediatamente concluido, de acuerdo a " +
                                 "la Udm"),
        'total_inv': fields.float('Invoiced', digits=(15, 2),
                                  readonly=False,
                                  help="Cantidad total en Bs. más IVA " +
                                  "incluido, por la venta del producto en " +
                                  "el año"),
        'pct_local': fields.float('% local', digits=(15, 2),
                                  readonly=False,
                                  help="Porcentaje (%) de la cantidad  " +
                                  "vendida que fue destinado al mercado " +
                                  "nacional, en el año"),
        'customer_qty': fields.integer('Customer qty',
                                       help="Cantidad de unidades " +
                                       "económicas que adquirieron el " +
                                       "producto"),
        'estimated_qty': fields.float('Required qty', digits=(15, 2),
                                      readonly=False,
                                      help="Según el Plan de Producción, " +
                                      "número de unidades que estima " +
                                      "producirá en el año actual, de " +
                                      "acuerdo a la Udm"),
        'data_year': fields.integer(
            'Year', required=True,
            help="El año al que corresponden los datos"),
        }

    _defaults = {
        'pct_local': 100,
        }

    _sql_constraints = [
        ('product_id_uniq', 'UNIQUE(data_year,product_id)',
         'The product must be unique!'),
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    def copy(self, cr, uid, id, default=None, context=None):
        brw = self.browse(cr, uid, id, context={})
        default = default or {}
        default.update({
            'data_year': brw.data_year + 1,
            })
        res = super(tcv_sigesic_0902, self).copy(cr, uid, id, default, context)
        return res

    def get_data_lines_ids(self, cr, uid, line_id, data_year, context):
        return self.search(
            cr, uid, [('data_year', '=', data_year)])

    def get_data_line(self, cr, uid, line_id, context):

        def str_uom(uom):
            uoms = {'m2': u'm²',
                    'm3': u'm³',
                    'unid': u'Unidad',
                    'ml': u'm',
                    }
            return uom and uoms.get(uom, uom) or ''

        def str_line(name):
            return name and name.replace(';', ',').strip() or ''

        line = self.browse(cr, uid, line_id, context=context)
        return (str_line(line.hs_code_id and line.hs_code_id.code),
                str_line(line.name),
                str_line(line.tech_specs),
                str_line(line.product_id and line.product_id.name),
                str_uom(line.uom_id and line.uom_id.name),
                str_line('%.2f' % line.weight),
                str_line('%.2f' % line.qty_prod),
                str_line('%.2f' % line.qty_sale),
                str_line('%.2f' % line.total_inv),
                str_line('%.2f' % line.pct_local),
                str_line('%d' % line.customer_qty),
                str_line('%.2f' % line.estimated_qty),
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
            res.update({'tech_specs': prd.tech_specs,
                        'uom_id': prd.uom_id.id,
                        'weight': prd.weight})
            if prd.hs_code:
                ids = self.pool.get('tcv.sigesic.9901').\
                    search(cr, uid, [('code', '=', prd.hs_code)])
                if ids and len(ids) == 1:
                    res.update({'hs_code_id': ids[0]})
        return {'value': res}

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_sigesic_0902()

##------------------------------------------------------------ tcv_sigesic_0903


class tcv_sigesic_0903(osv.osv):

    _name = 'tcv.sigesic.0903'

    _description = 'Raw materials / Goods relation\n' + \
                   'Relación Bienes / Materias Primas'

    _csv_file_name = 'relacion_bienes_insumos_%s.csv'

    _goods_ids = []

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    def _csv_header(self, cr, uid, ids, context):
        res = ['',
               '']
        obj_good = self.pool.get('tcv.sigesic.0902')
        self._goods_ids = obj_good.search(
            cr, uid, [('data_year', '=', context.get('data_year'))])
        for item in obj_good.browse(cr, uid, self._goods_ids, context={}):
            res.append('"%s"' % obj_good._get_full_name(item))
        return res

    def _compute_uom_rel(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        ids = isinstance(ids, (int, long)) and [ids] or ids
        for item in self.browse(cr, uid, ids, context=context):
            if item and item.input_id and item.goods_id:
                res[item.id] = {'uom_rel': '%s -x-> %s' %
                                (item.input_id.product_id.uom_id.name,
                                 item.goods_id.product_id.uom_id.name)
                                }
        return res
    ##-------------------------------------------------------------------------

    _columns = {
        'input_id': fields.many2one(
            'tcv.sigesic.0901', 'Inputs/raw mat.', ondelete='restrict',
            required=True,
            help="Nombre del Insumo, Marca y Especificacione s técnicas"),
        'uom_rel': fields.function(
            _compute_uom_rel, method=True, type='char', size=32, string='UoM',
            multi='all'),
        'goods_id': fields.many2one(
            'tcv.sigesic.0902', 'Goods produced', ondelete='restrict',
            required=True,
            help="Nombre del producto, marca y especificaciones técnicas"),
        'quantity': fields.float(
            'Quantity', digits=(15, 4), required=True,
            help="Cantidad del insumo que es requerido para producir el " +
            "Bien correspondiente"),
        'used': fields.boolean(
            'Used input', required=True),
        'data_year': fields.integer(
            'Year', required=True,
            help="El año al que corresponden los datos"),
        }

    _defaults = {
        'used': lambda *a: True,
        'quantity': lambda *a: 0,

        }

    _sql_constraints = [
        ('quantity_gt_zero', 'CHECK (quantity>=0)',
         'The quantity must be >= 0 !'),
        ('relation_uniq', 'UNIQUE(input_id,goods_id)',
         'The relation must be unique!'),
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    def get_data_lines_ids(self, cr, uid, line_id, data_year, context):
        obj_imp = self.pool.get('tcv.sigesic.0901')
        return obj_imp.search(
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

        output = []
        obj_imp = self.pool.get('tcv.sigesic.0901')
        for g_id in self._goods_ids:  # always same order load in header
            rel_ids = self.search(cr, uid, [('input_id', '=', line_id),
                                            ('goods_id', '=', g_id)])
            if rel_ids:
                rel = self.browse(cr, uid, rel_ids[0], context=context)
                if not output:  # only first time
                    output.append(obj_imp._get_full_name(rel.input_id))
                    output.append('(%s)' % str_uom(rel.input_id.uom_id.name))
                output.append(str_line('%.4f' % rel.quantity))
        return output

    ##-------------------------------------------------------- buttons (object)

    def button_refresh(self, cr, uid, ids, context=None):
        obj_inp = self.pool.get('tcv.sigesic.0901')
        obj_goo = self.pool.get('tcv.sigesic.0902')
        ids = isinstance(ids, (int, long)) and [ids] or ids
        brw = self.browse(cr, uid, ids[0], context={})
        year = brw.data_year
        input_ids = obj_inp.get_data_lines_ids(
            cr, uid, ids, year, context)
        goods_ids = obj_goo.get_data_lines_ids(
            cr, uid, ids, year, context)
        if input_ids and goods_ids:
            for g in goods_ids:
                for i in input_ids:
                    if not self.search(
                            cr, uid, [('data_year', '=', year),
                                      ('input_id', '=', i),
                                      ('goods_id', '=', g)]):
                        self.create(cr, uid, {'data_year': year,
                                              'input_id': i,
                                              'goods_id': g}, context)

        if year <= 2012:
            return True
        # Copy relation data from previus year
        last_year = year - 1
        rel_ids = self.search(
            cr, uid, [('data_year', '=', year)])
        for rel in self.browse(cr, uid, rel_ids, context=context):
            li = obj_inp.search(cr, uid, [
                ('product_id', '=', rel.input_id.product_id.id),
                ('data_year', '=', last_year)])
            lg = obj_goo.search(cr, uid, [
                ('product_id', '=', rel.goods_id.product_id.id),
                ('data_year', '=', last_year)])
            if li and lg:
                last_rel_id = self.search(
                    cr, uid, [('data_year', '=', last_year),
                              ('input_id', '=', li[0]),
                              ('goods_id', '=', lg[0])])
                if last_rel_id:
                    last_rel = self.browse(
                        cr, uid, last_rel_id[0], context=context)
                    data = {'quantity': last_rel.quantity,
                            'used': last_rel.used,
                            }
                    self.write(cr, uid, [rel.id], data, context=context)
        return True

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_sigesic_0903()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
