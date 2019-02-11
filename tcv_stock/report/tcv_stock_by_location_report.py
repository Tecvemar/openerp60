# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2014-11-20
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
import decimal_precision as dp
import time
#~ import netsvc
from report import report_sxw

##------------------------------------------------ tcv_stock_by_location_report


class tcv_stock_by_location_report(osv.osv_memory):

    _name = 'tcv.stock.by.location.report'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def _clear_lines(self, cr, uid, ids, context):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        unlink_ids = []
        for item in self.browse(cr, uid, ids, context={}):
            for l in item.line_ids:
                unlink_ids.append((2, l.id))
            self.write(cr, uid, ids, {'line_ids': unlink_ids}, context=context)
        return True

    ##--------------------------------------------------------- function fields

    _columns = {
        'name': fields.char(
            'Name', size=64, required=False, readonly=False),
        'date': fields.date(
            'Date', required=True),
        'company_id': fields.many2one(
            'res.company', 'Company', required=True, readonly=True,
            ondelete='restrict'),
        'location_id': fields.many2one(
            'stock.location', 'Location', ondelete='restrict'),
        'product_id': fields.many2one(
            'product.product', 'Product', ondelete='restrict'),
        'stock_driver': fields.selection(
            [('normal', 'Normal'), ('tile', 'Tile'),
             ('slab', 'Slab'), ('block', 'Block')],
            'Stock driver'),
        'order_by': fields.selection(
            [('lt.name', 'Lot'), ('pt.name', 'Product'),
             ('product_qty', 'Quantity'), ('l.name', 'Location')],
            'Order By',
            ),
        'categ_id': fields.many2one(
            'product.category', 'Category'),
        'zero_cost': fields.boolean(
            'Only 0 cost'),
        'loaded': fields.boolean(
            'Loaded'),
        'available': fields.boolean(
            'Available'),
        'line_ids': fields.one2many(
            'tcv.stock.by.location.report.lines', 'line_id', 'Lines'),
        'report_type': fields.selection(
            [('normal', 'Normal'),
             ('take_location', 'Take inventory (by location)')],
            string='Report type', required=True, readonly=False),
        }

    _defaults = {
        'available': lambda *a: False,
        'loaded': lambda *a: False,
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company').
        _company_default_get(cr, uid, self._name, context=c),
        'report_type': lambda *a: 'normal',
        'order_by': lambda *a: 'l.name',
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    def button_load_inventory(self, cr, uid, ids, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        item = self.browse(cr, uid, ids[0], context={})
        params = {'date': "i.date <= '%s 23:59:59' and" % item.date,
                  'location_ids': '',
                  'stock_driver': '',
                  'product_id': '',
                  'categ_ids': '',
                  'zero_cost': '',
                  'available': '',
                  'company_id': item.company_id.id,
                  'order_by': '',
                  }
        if item.location_id:
            obj_loc = self.pool.get('stock.location')
            loc_brw = item.location_id
            loc_ids = obj_loc.search(
                cr, uid, [('location_id', 'child_of', [loc_brw.id])])
            params.update(
                {'location_ids': "i.location_id in (%s) and" %
                 (str(loc_ids)[1:-1]).replace('L', '')})
        if item.stock_driver:
            params.update(
                {'stock_driver': "pp.stock_driver  = '%s' and" %
                 item.stock_driver})
        if item.product_id:
            params.update(
                {'product_id': "i.product_id = '%s' and" %
                 item.product_id.id})
        if item.categ_id:
            obj_cat = self.pool.get('product.category')
            cat_brw = item.categ_id
            cat_ids = obj_cat.search(
                cr, uid, [('parent_id', 'child_of', [cat_brw.id])])
            params.update(
                {'categ_ids': "pt.categ_id in (%s) and" %
                 (str(cat_ids)[1:-1]).replace('L', '')})
        if item.zero_cost:
            params.update(
                {'zero_cost': "ip.value_float is null and"})
        if item.available:
            params.update(
                {'available': "i.prodlot_id not in (select prod_lot_id " +
                 "from sale_order_line where state != 'cancel' and " +
                 "prod_lot_id is not null) and " +
                 "i.prodlot_id not in " +
                 "(select distinct prod_lot_id from tcv_bundle_lines) and"})
        if item.order_by:
            params.update(
                {'order_by': item.order_by})
        sql = """
        select i.location_id, l.name as location,
               i.product_id, pt.name as product,
               i.prodlot_id as prod_lot_id, lt.name as lot,
               lt.length, lt.width, lt.heigth,
               lt.date, sum(product_qty) as product_qty,
               pt.uom_id, ip.value_float as cost, pt.categ_id
        from report_stock_inventory i
        left join stock_location l ON (i.location_id=l.id)
        LEFT JOIN product_product pp ON (i.product_id=pp.id)
        LEFT JOIN product_template pt ON (pp.product_tmpl_id=pt.id)
        LEFT JOIN stock_production_lot lt ON (i.prodlot_id=lt.id)
        left join ir_property ip on ip.name = 'property_cost_price' and
                  res_id='stock.production.lot,' || cast(lt.id as char(9)) and
                  ip.company_id = %(company_id)s
        where i.state = 'done' and
              %(date)s
              %(location_ids)s
              %(stock_driver)s
              %(product_id)s
              %(categ_ids)s
              %(zero_cost)s
              %(available)s
              l.usage = 'internal' and i.company_id = %(company_id)s
        group by i.location_id, l.name,
                 i.product_id, pt.name,
                 i.prodlot_id, lt.name,
                 lt.length, lt.width, lt.heigth,
                 lt.date, pt.uom_id, ip.value_float, pt.categ_id
        having sum(product_qty) > 0
        order by %(order_by)s
        """ % params
        cr.execute(sql)
        lines = []
        for row in cr.fetchall():
            data = {'location_id': row[0],
                    'product_id': row[2],
                    'prod_lot_id': row[4],
                    'date': ('%s' % row[9])[:10],
                    'product_qty': row[10],
                    'uom_id': row[11],
                    'cost': row[12],
                    }
            lines.append((0, 0, data))
        self._clear_lines(cr, uid, ids, context)
        if lines:
            self.write(cr, uid, ids, {'line_ids': lines,
                                      'loaded': bool(lines)}, context=context)
        return True

    def button_update_block_cost(self, cr, uid, ids, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        obj_lot = self.pool.get('stock.production.lot')
        for item in self.browse(cr, uid, ids, context={}):
            for line in item.line_ids:
                lot = line.prod_lot_id
                product = line.product_id
                if lot and product and product.stock_driver == 'block' and \
                        lot.property_cost_price == 0 and \
                        lot.invoice_lines_ids and \
                        len(lot.invoice_lines_ids) == 1 and \
                        lot.invoice_lines_ids[0].invoice_id.type == \
                        'in_invoice':
                    price_unit = lot.invoice_lines_ids[0].price_unit
                    obj_lot.write(
                        cr, uid, [lot.id], {'property_cost_price': price_unit},
                        context=context)

        return True

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow


tcv_stock_by_location_report()


class tcv_stock_by_location_report_lines(osv.osv_memory):

    _name = 'tcv.stock.by.location.report.lines'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def _compute_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for item in self.browse(cr, uid, ids, context=context):
            res[item.id] = {
                'total_cost': item.product_qty * item.cost
                if item.product_qty and item.cost else 0}
        return res

    ##--------------------------------------------------------- function fields

    _columns = {
        'line_id': fields.many2one(
            'tcv.stock.by.location.report', 'Line', required=True,
            ondelete='cascade'),
        'location_id': fields.many2one(
            'stock.location', 'Location', ondelete='restrict'),
        'product_id': fields.many2one(
            'product.product', 'Product', ondelete='restrict'),
        'categ_id': fields.related(
            'product_id', 'categ_id', type='many2one',
            relation='product.category', string='Category',
            store=False, readonly=True),
        'prod_lot_id': fields.many2one(
            'stock.production.lot', 'Production lot', ondelete='restrict'),
        'date': fields.date(
            'Date'),
        'product_qty': fields.float(
            'Quantity', digits_compute=dp.get_precision('Product UoM'),
            required=True),
        'uom_id': fields.many2one(
            'product.uom', 'UoM', ondelete='restrict'),
        'cost': fields.float(
            'Cost', digits_compute=dp.get_precision('Account'), required=True),
        'total_cost': fields.function(
            _compute_all, method=True, type='float', string='Total cost',
            digits_compute=dp.get_precision('Account'), multi='all'),
        }

    _defaults = {
        'product_qty': lambda *a: 0,
        'cost': lambda *a: 0,
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow


tcv_stock_by_location_report_lines()


class parser_tcv_stock_by_location_report(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        context = context or {}
        super(parser_tcv_stock_by_location_report, self).__init__(
            cr, uid, name, context=context)
        self.localcontext.update({
            'get_summary': self._get_summary,
            'get_groups': self._get_groups,
            })
        self.context = context

    def _get_summary(self, obj_lines, *args):
        '''
        obj_lines: an obj.line_ids (lines to be totalized)
        args: [string] with csv field names to be totalized

        Use in rml:
        [[ repeatIn(get_summary(o.line_ids, ('fld_1,fld_2,...')), 't') ]]
        '''
        totals = {}
        field_list = args[0][0]
        fields = field_list.split(',')
        for key in fields:
            totals[key] = 0
        for line in obj_lines:
            for key in fields:
                totals[key] += line[key]
        return [totals]

    def _get_groups(self, obj_id):
        res = []
        groups = []
        group = {}
        obj_inv = self.pool.get('tcv.stock.by.location.report')
        inv_brw = obj_inv.browse(self.cr, self.uid, obj_id, context={})
        for ln in inv_brw.line_ids:
            #~ key = (ln.location_id.id, ln.product_id.id)
            key = (ln.location_id.id)
            if key not in groups:
                groups.append(key)
                if group:
                    res.append(group)
                group = {'location': ln.location_id.name,
                         #~ 'product': ln.product_id.name,
                         'lines': [],
                         }
            group['lines'].append(ln)
        if group:
            res.append(group)
        res = sorted(res, key=lambda k: k['location'])
        return res


report_sxw.report_sxw(
    'report.tcv.stock.by.location.report.report',
    'tcv.stock.by.location.report',
    'addons/tcv_stock/report/tcv_stock_by_location_report.rml',
    parser=parser_tcv_stock_by_location_report,
    header=False
    )


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
