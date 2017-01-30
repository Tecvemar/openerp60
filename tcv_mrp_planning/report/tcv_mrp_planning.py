# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description: Report parser for: tcv_mrp_planning
#
#
##############################################################################
from report import report_sxw
#~ from datetime import datetime
from osv import fields, osv
#~ from tools.translate import _
#~ import pooler
import decimal_precision as dp
import time
#~ import netsvc


class parser_tcv_mrp_planning(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        context = context or {}
        super(parser_tcv_mrp_planning, self).__init__(
            cr, uid, name, context=context)
        self.localcontext.update({
            'get_summary': self._get_summary,
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


report_sxw.report_sxw(
    'report.tcv.mrp.planning.report',
    'tcv.mrp.planning',
    'addons/tcv_mrp_planning/report/tcv_mrp_planning.rml',
    parser=parser_tcv_mrp_planning,
    header=False
    )


##------------------------------------------------------------ tcv_mrp_planning


class tcv_mrp_planning(osv.osv_memory):

    _name = 'tcv.mrp.planning'

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

    def _get_blocks_stock(self, cr, uid, item, location_id,
                          product_id, context):
        obj_loc = self.pool.get('tcv.stock.by.location.report')
        loc_data_id = obj_loc.create(
            cr, uid, {'date': item.date,
                      'location_id': location_id,
                      'product_id': product_id}, context)
        obj_loc.button_load_inventory(
            cr, uid, loc_data_id, context=context)
        loc_brw = obj_loc.browse(
            cr, uid, loc_data_id, context=context)
        stock = 0
        pcs = 0
        for line in loc_brw.line_ids:
            stock += line.product_qty
            pcs += 1
        return (stock, pcs)

    def _get_in_process_data(self, cr, uid, ids, item, context):
        obj_inp = self.pool.get('tcv.mrp.in.process')
        inp_data_id = obj_inp.create(
            cr, uid, {'date_from': '2015-01-01',
                      'date_to': item.date}, context)
        obj_inp.button_load_in_process(
            cr, uid, inp_data_id, context=context)
        inp_brw = obj_inp.browse(
            cr, uid, inp_data_id, context=context)
        data = {}
        for line in inp_brw.line_ids:
            group = line.template_id.name.split()[0]
            product = line.product_id.id
            if not data.get(group):
                data.update({group: {}})
            if not data[group].get(product):
                data[group].update({product: {'pcs': 0,
                                              'stock': 0}})
            data[group][product]['pcs'] += line.pieces
            data[group][product]['stock'] += line.area
        return data

    def _get_stock_in_bundle(self, cr, uid, ids, item, context):
        obj_bun = self.pool.get('tcv.bundle')
        bun_ids = obj_bun.search(cr, uid, [('state', '=', 'available'),
                                           ('reserved', '=', False)])
        data = {}
        for bundle in obj_bun.browse(cr, uid, bun_ids, context):
            for line in bundle.line_ids:
                product = line.product_id.id
                if not data.get(product):
                    data.update({product: {'pcs': 0,
                                           'stock': 0}})
                data[product]['pcs'] += 1
                data[product]['stock'] += line.lot_factor
        return data

    ##--------------------------------------------------------- function fields

    _columns = {
        'name': fields.char(
            'Name', size=64, required=False, readonly=False),
        'date': fields.date(
            'Date', required=True),
        'company_id': fields.many2one(
            'res.company', 'Company', required=True, readonly=True,
            ondelete='restrict'),
        'line_ids': fields.one2many(
            'tcv.mrp.planning.lines', 'line_id', 'String', readonly=True),
        }

    _defaults = {
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company').
        _company_default_get(cr, uid, self._name, context=c),
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    def button_load(self, cr, uid, ids, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        obj_conf = self.pool.get('tcv.mrp.planning.config')
        conf_ids = obj_conf.search(cr, uid, [])
        item = self.browse(cr, uid, ids[0], context=context)
        if item.line_ids:
            self._clear_lines(cr, uid, ids, context)
        lines = []
        in_process = {}
        stock_bundle = {}
        for product in obj_conf.browse(cr, uid, conf_ids, context=context):
            stock_quarry = self._get_blocks_stock(
                cr, uid, item, product.quarry_location_id.id,
                product.product_id1.id, context)
            stock_plant = self._get_blocks_stock(
                cr, uid, item, product.plant_location_id.id,
                product.product_id1.id, context)
            if not in_process:
                in_process = self._get_in_process_data(
                    cr, uid, ids, item, context)
            stock_gangsaw = in_process.get(
                'Aserrado', {}).get(product.product_id2.id, {})
            stock_polish = in_process.get(
                'Apomazado', {}).get(product.product_id2.id, {})
            stock_resin = in_process.get(
                'Resinado', {}).get(product.product_id2.id, {})
            stock_available = self._get_blocks_stock(
                cr, uid, item, product.stock_location_id.id,
                product.product_id3.id, context)
            if not stock_bundle:
                stock_bundle = self._get_stock_in_bundle(
                    cr, uid, ids, item, context)
            lines.append((0, 0, {
                'name': product.name,
                'stock_quarry': stock_quarry[0],
                'pcs_quarry': stock_quarry[1],
                'stock_plant': stock_plant[0],
                'pcs_plant': stock_plant[1],
                'stock_gangsaw': stock_gangsaw.get('stock', 0),
                'pcs_gangsaw': stock_gangsaw.get('pcs', 0),
                'stock_polish': stock_polish.get('stock', 0),
                'pcs_polish': stock_polish.get('pcs', 0),
                'stock_resin': stock_resin.get('stock', 0),
                'pcs_resin': stock_resin.get('pcs', 0),
                'stock_available': stock_available[0],
                'pcs_available': stock_available[1],
                'stock_bundle': stock_bundle.get(
                    product.product_id3.id, {}).get('stock', 0),
                'pcs_bundle': stock_bundle.get(
                    product.product_id3.id, {}).get('pcs', 0),
                }))
        self.write(cr, uid, ids, {'line_ids': lines}, context=context)
        return True

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_mrp_planning()


class tcv_mrp_planning_lines(osv.osv_memory):

    _name = 'tcv.mrp.planning.lines'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'line_id': fields.many2one(
            'tcv.mrp.planning', 'String', required=True, ondelete='cascade'),
        'name': fields.char(
            'Name', size=64, required=False, readonly=False),
        'stock_quarry': fields.float(
            'stock_quarry', digits_compute=dp.get_precision('Product UoM'),
            readonly=False),
        'pcs_quarry': fields.integer(
            'pcs_quarry'),
        'stock_plant': fields.float(
            'stock_plant', digits_compute=dp.get_precision('Product UoM'),
            readonly=False),
        'pcs_plant': fields.integer(
            'pcs_plant'),
        'stock_gangsaw': fields.float(
            'stock gangsaw', digits_compute=dp.get_precision('Product UoM'),
            readonly=False),
        'pcs_gangsaw': fields.integer(
            'pcs gangsaw'),
        'stock_polish': fields.float(
            'stock pumiced', digits_compute=dp.get_precision('Product UoM'),
            readonly=False),
        'pcs_polish': fields.integer(
            'pcs polish'),
        'stock_resin': fields.float(
            'stock resin', digits_compute=dp.get_precision('Product UoM'),
            readonly=False),
        'pcs_resin': fields.integer(
            'pcs resin'),
        'stock_available': fields.float(
            'stock available', digits_compute=dp.get_precision('Product UoM'),
            readonly=False),
        'pcs_available': fields.integer(
            'pcs available'),
        'stock_bundle': fields.float(
            'stock bundle', digits_compute=dp.get_precision('Product UoM'),
            readonly=False),
        'pcs_bundle': fields.integer(
            'pcs bundle'),
        }

    _defaults = {
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_mrp_planning_lines()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
