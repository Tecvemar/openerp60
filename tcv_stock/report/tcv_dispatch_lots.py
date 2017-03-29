# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description: Report parser for: tcv_dispatch_lots
#
#
##############################################################################
from report import report_sxw
#~ from datetime import datetime
from osv import fields, osv
#~ from tools.translate import _
#~ import pooler
#~ import decimal_precision as dp
import time
#~ import netsvc


##---------------------------------------------------- parser_tcv_dispatch_lots


class parser_tcv_dispatch_lots(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        context = context or {}
        super(parser_tcv_dispatch_lots, self).__init__(
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
        [[ repeatIn(get_summary(o.line_ids, ('fld_1', 'fld_2'..)), 't') ]]
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
    'report.tcv.dispatch.lots.report',
    'tcv.dispatch.lots',
    'addons/tcv_dispatch_lots/report/tcv_dispatch_lots.rml',
    parser=parser_tcv_dispatch_lots,
    header=False
    )


##----------------------------------------------------------- tcv_dispatch_lots


class tcv_dispatch_lots(osv.osv_memory):

    _name = 'tcv.dispatch.lots'

    _description = ''

    ##-------------------------------------------------------------------------

    def default_get(self, cr, uid, fields, context=None):
        data = super(tcv_dispatch_lots, self).default_get(
            cr, uid, fields, context)
        data.update({
            'date_start': time.strftime('%Y-01-01'),
            'date_end': time.strftime('%Y-12-31'),
            #~ 'pct_type': self._get_pct_type(data.get('type')) or 'none',
            })
        return data

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
        'company_id': fields.many2one(
            'res.company', 'Company', required=True, readonly=True,
            ondelete='restrict'),
        'date_start': fields.date(
            'From', required=True, select=True, help="From invoice date"),
        'date_end': fields.date(
            'To', required=True, select=True, help="To invoice date"),
        'loaded': fields.boolean(
            'Loaded'),
        'type': fields.selection(
            [('tile', 'Tile'), ('slab', 'Slab')], string='Type',
            required=True, readonly=False, help="Product's stock driver"),
        'line_ids': fields.one2many(
            'tcv.dispatch.lots.lines', 'line_id', 'Lots'),
        }

    _defaults = {
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company').
        _company_default_get(cr, uid, self._name, context=c),
        'type': lambda *a: 'slab',
        'loaded': lambda *a: False,
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    def button_load(self, cr, uid, ids, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        item = self.browse(cr, uid, ids[0], context={})
        params = {'date_start': item.date_start,
                  'date_end': item.date_end,
                  'type': item.type,
                  'company_id': item.company_id.id,
                  }
        sql = """
        select ail.origin, ail.product_id, spl.id , ai.number,
               ai.date_invoice, rp.id, ai.id, so.id, sm.picking_id,
               ail.name, spl.name
        from account_invoice_line ail
        left join account_invoice ai on ail.invoice_id = ai.id
        left join product_product pp on ail.product_id = pp.id
        left join stock_production_lot spl on ail.prod_lot_id = spl.id
        left join res_partner rp on ai.partner_id = rp.id
        left join sale_order so on ai.origin = so.name
        left join stock_move sm on spl.id = sm.prodlot_id and
                                   sm.location_dest_id = 9 and
                                   not sm.state in ('done', 'cancel')
        where not prod_lot_id is null and
              pp.stock_driver = %(type)s and
              ai.type = 'out_invoice' and
              ai.state in ('open', 'paid') and
              ai.date_invoice between %(date_start)s and %(date_end)s and
              ai.company_id = %(company_id)s and
              not ail.prod_lot_id in (
                  select prodlot_id from stock_move sm
                  where state = 'done' and location_dest_id = 9 and
                        not prodlot_id is null)
        order by ail.origin, ail.name, spl.name
        """
        cr.execute(sql, params)
        lines = []
        for row in cr.fetchall():
            data = {'origin': row[0],
                    'product_id': row[1],
                    'prod_lot_id': row[2],
                    'invoice_number': row[3],
                    'date_invoice': row[4],
                    'partner_id': row[5],
                    'invoice_id': row[6],
                    'order_id': row[7],
                    'picking_id': row[8],
                    }
            lines.append((0, 0, data))
        self._clear_lines(cr, uid, ids, context)
        if lines:
            self.write(cr, uid, ids, {'line_ids': lines,
                                      'loaded': bool(lines)}, context=context)
        return True

    def button_print(self, cr, uid, ids, context=None):
        return False

    ##------------------------------------------------------------ on_change...

    def on_change_date(self, cr, uid, ids, date_start, date_en, type):
        res = {}
        self._clear_lines(cr, uid, ids, context=None)
        res.update({'loaded': False,
                    'line_ids': [],
                    })
        return {'value': res}

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow


tcv_dispatch_lots()


class tcv_dispatch_lots_lines(osv.osv_memory):

    _name = 'tcv.dispatch.lots.lines'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'line_id': fields.many2one(
            'tcv.dispatch.lots', 'Lots', required=True, ondelete='cascade'),
        'name': fields.char(
            'Name', size=64, required=False, readonly=False),
        'origin': fields.char(
            'Origin', size=64, required=False, readonly=False),
        'date_invoice': fields.date(
            'Date invoice', required=True, readonly=True,
            states={'draft': [('readonly', False)]}, select=True),
        'invoice_number': fields.char(
            'Invoice number', size=64, required=False, readonly=False),
        'prod_lot_id': fields.many2one(
            'stock.production.lot', 'Production lot', required=False),
        'partner_id': fields.many2one(
            'res.partner', 'Partner', change_default=True,
            readonly=True, required=True,
            tstates={'draft': [('readonly', False)]}, ondelete='restrict'),
        'product_id': fields.many2one(
            'product.product', 'Product', ondelete='restrict'),
        'invoice_id': fields.many2one(
            'account.invoice', 'Invoice Reference', ondelete='restrict',
            select=True),
        'order_id': fields.many2one(
            'sale.order', 'Order Reference', ondelete='restrict',
            select=True),
        'picking_id': fields.many2one(
            'stock.picking', 'Picking', ondelete='restrict',
            select=True),

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


tcv_dispatch_lots_lines()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
