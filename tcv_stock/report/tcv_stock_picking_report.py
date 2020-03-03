# -*- encoding: utf-8 -*-
##############################################################################
#    Company:
#    Author: David Bernal
#    Creation Date: 2020-02-12
#    Version: 1.0
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

##---------------------------------------------------- tcv_stock_picking_report


class tcv_stock_picking_report(osv.osv_memory):

    _name = 'tcv.stock.picking.report'

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
        'date_start': fields.date(
            'Date Start', required=True),
        'date_end': fields.date(
            'Date End', required=True),
        'partner_ids': fields.many2many(
            'res.partner', 'picking_report', 'picking_report_id',
            'partner_id', 'Partners', readonly=False),
        'product_ids': fields.many2many(
            'product.product', 'picking_report', 'picking_report_id',
            'product_id', 'Products'),
        'partner_id': fields.many2one(
            'res.partner', 'Partner', change_default=True,
            readonly=False,
            tstates={'draft': [('readonly', False)]}, ondelete='restrict'),
        'product_id': fields.many2one(
            'product.product', 'Product', ondelete='restrict'),
        'state_done': fields.boolean('Done'),
        'state_cancel': fields.boolean('Cancel'),
        'state_draft': fields.boolean('Draft'),
        'state_assigned': fields.boolean('Assigned'),
        'state_confirmed': fields.boolean('Confirmed'),
        'journal_id': fields.many2one(
            'stock.journal', 'Journal',
            domain="[('type','=','cash')]", ondelete='restrict'),
        'driver_id': fields.many2one(
            'tcv.driver.vehicle', 'Driver', required=False,
            domain="[('type','=','driver')]", ondelete='restrict'),
        'vehicle_id': fields.many2one(
            'tcv.driver.vehicle', 'Vehicle', required=False,
            domain="[('type','=','vehicle')]", ondelete='restrict'),
        'loaded': fields.boolean('Loaded'),
        'line_ids': fields.one2many(
            'tcv.stock.picking.report.lines', 'line_id', 'Lines'),

        }

    _defaults = {
        'loaded': lambda *a: False,
        'date_start': lambda *a: time.strftime('%Y-%m-%d'),
        'date_end': lambda *a: time.strftime('%Y-%m-%d'),
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    def button_load_inventory(self, cr, uid, ids, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        item = self.browse(cr, uid, ids[0], context={})
        params = {'date_start': item.date_start,
                  'date_end': item.date,
                  'product_id': '',
                  'partner_id': '',
                  'state_done': '',
                  'state_cancel': '',
                  'state_draft': '',
                  'state_assigned': '',
                  'state_confirmed': '',
                  'journal_id': '',
                  }
        if item.product_id:
            params.update(
                {'product_id': "and pp.id = '%s'" %
                 item.product_id.id})
        if item.partner_id:
            params.update(
                {'partner_id': "and rp.id = '%s'" %
                 item.partner_id.id})
        if item.journal_id:
            params.update(
                {'journal_id': "and sj.id = '%s'" %
                 item.journal_id.id})
        if item.state_done:
            params.update(
                {'state_done': "and sp.state = 'done'"})
        if item.state_cancel:
            params.update(
                {'state_cancel': "and sp.state = 'cancel'"})
        if item.state_draft:
            params.update(
                {'state_draft': "and sp.state = 'draft'"})
        if item.state_assigned:
            params.update(
                {'state_assigned': "and sp.state = 'assigned'"})
        if item.state_confirmed:
            params.update(
                {'state_confirmed': "and sp.state = 'confirmed'"})
        sql = """
        select rp.id, rp.name as partner, pp.id, pp.name_template as product,
            spl.id, spl.name as lot, sm.product_qty, pu.id, sp.id,
            sp.name as picking, sj.id, sj.name as journal, tdvd.id,
            tdvd.name as driver, tdvv.id, tdvv.name as vehicle,
            tdvv.ident as ident, sp.date_done, sld.id,
            sld.name as location_dest
        from stock_picking sp
            left join res_partner rp on rp.id = sp.partner_id
            left join stock_move sm on sm.picking_id = sp.id
            left join stock_production_lot spl on spl.id = sm.prodlot_id
            left join product_product pp on pp.id = spl.product_id
            left join stock_location slo on slo.id = sm.location_id
            left join stock_location sld on sld.id = sm.location_dest_id
            left join tcv_driver_vehicle tdvd on tdvd.id = sp.driver_id
            left join tcv_driver_vehicle tdvv on tdvv.id = sp.vehicle_id
            left join stock_journal sj on sj.id = sp.stock_journal_id
            left join product_uom pu on pu.id = sm.product_uom

            where sp.date_done between %(date_start)s and %(date_end)s
              %(product_id)s
              %(partner_id)s
              %(journal_id)s
              %(state_done)s
              %(state_cancel)s
              %(state_draft)s
              %(state_assigned)s
              %(state_confirmed)s

        """ % params
        cr.execute(sql)
        lines = []
        for row in cr.fetchall():
            data = {'partner_id': row[0],
                    'product_id': row[2],
                    'prod_lot_id': row[4],
                    'product_qty': row[6],
                    'uom_id': row[7],
                    'picking_id': row[8],
                    'journal_id': row[10],
                    'driver_id': row[12],
                    'vehicle_id': row[14],
                    'vehicle_ident': row[16],
                    'date': row[17],
                    'location_id': row[18],
                    }
            lines.append((0, 0, data))
        self._clear_lines(cr, uid, ids, context)
        if lines:
            self.write(cr, uid, ids, {'line_ids': lines,
                                      'loaded': bool(lines)}, context=context)
        return True

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow


tcv_stock_picking_report()


class tcv_stock_picking_report_lines(osv.osv_memory):

    _name = 'tcv.stock.picking.report.lines'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'line_id': fields.many2one(
            'tcv.stock.picking.report', 'Line', required=True,
            ondelete='cascade'),
        'prod_lot_id': fields.many2one(
            'stock.production.lot', 'Production lot'),
        'product_id': fields.many2one(
            'product.product', 'Product', ondelete='restrict'),
        'partner_id': fields.many2one(
            'res.partner', 'Partner', change_default=True,
            ondelete='restrict'),
        'product_qty': fields.float(
            'Quantity', digits_compute=dp.get_precision('Product UoM')),
        'uom_id': fields.many2one(
            'product.uom', 'UoM', ondelete='restrict'),
        'date': fields.date(
            'Date Picking', readonly=True,
            states={'draft': [('readonly', False)]}, select=True),
        'picking_id': fields.many2one(
            'stock.picking', 'Picking', readonly=True, ondelete='restrict',
            help="The picking for this entry line"),
        'move_id': fields.many2one(
            'stock.move', 'Moves', ondelete='restrict',
            help="Stock Move.", select=True, readonly=True),
        'location_id': fields.many2one(
            'stock.location', 'Location', readonly=False, ondelete='restrict',
            help=""),
        'driver_id': fields.many2one(
            'tcv.driver.vehicle', 'Driver', required=False,
            domain="[('type','=','driver')]", ondelete='restrict'),
        'vehicle_id': fields.many2one(
            'tcv.driver.vehicle', 'Vehicle', required=False,
            domain="[('type','=','vehicle')]", ondelete='restrict'),
        'journal_id': fields.many2one(
            'account.journal', 'Journal', required=True,
            domain="[('type','=','cash')]", ondelete='restrict'),
        'vehicle_ident': fields.char(
            'Vehicle Ident', size=64),
        }

    _defaults = {
        'loaded': lambda *a: False,
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow


tcv_stock_picking_report_lines()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
