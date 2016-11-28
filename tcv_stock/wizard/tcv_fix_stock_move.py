# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2014-05-26
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
#~ import time
#~ import netsvc
import logging
logger = logging.getLogger('server')

##---------------------------------------------------------- tcv_fix_stock_move


class tcv_fix_stock_move(osv.osv_memory):

    _name = 'tcv.fix.stock.move'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def _clear_data(self, cr, uid, ids, context=None):
        unlink_ids = []
        for item in self.browse(cr, uid, ids, context={}):
            for l in item.line_ids:
                unlink_ids.append((2, l.id))
        data = {'prod_lot_id': None,
                'product_id': None,
                'line_ids': unlink_ids,
                }
        self.write(cr, uid, ids, data, context=context)
        return True

    ##--------------------------------------------------------- function fields

    _columns = {
        'prod_lot_id': fields.many2one(
            'stock.production.lot', 'Production lot', required=False),
        'product_id': fields.related(
            'prod_lot_id', 'product_id', type='many2one',
            relation='product.product', string='Product',
            store=False, readonly=True),
        'line_ids': fields.one2many(
            'tcv.fix.stock.move.lines', 'line_id', 'String'),
        }

    _defaults = {
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    def button_done(self, cr, uid, ids, context=None):
        for fix in self.browse(cr, uid, ids, context={}):
            for lin_brw in fix.line_ids:
                data = {'date': lin_brw.date,
                        'location_id': lin_brw.location_id.id,
                        'location_dest_id': lin_brw.location_dest_id.id,
                        'product_qty': lin_brw.product_qty or 0.0,
                        'pieces_qty': lin_brw.pieces_qty or 0,
                        'id': lin_brw.stock_move_id.id}
                sql = ("update stock_move set " +
                       "date='%(date)s', " +
                       "location_id=%(location_id)s, " +
                       "location_dest_id=%(location_dest_id)s, " +
                       "product_qty=%(product_qty)s, " +
                       "pieces_qty=%(pieces_qty)s " +
                       "where id=%(id)s") % data
                logger.info('Fixing stock.move: %s' % sql)
                cr.execute(sql)
        return {'type': 'ir.actions.act_window_close'}

    def button_done_new(self, cr, uid, ids, context=None):
        self.button_done(cr, uid, ids, context=None)
        self._clear_data(cr, uid, ids, context=None)
        return True

    def button_empty(self, cr, uid, ids, context=None):
        fix_brw = self.browse(cr, uid, ids, context={})
        for fix in fix_brw:
            if fix.line_ids and len(fix.line_ids) == 1:
                for lin_brw in fix.line_ids:
                    data = {'date': lin_brw.date,
                            'location_id': lin_brw.location_id.id,
                            'location_dest_id': 4,
                            'product_qty': lin_brw.product_qty or 0.0,
                            'pieces_qty': lin_brw.pieces_qty or 0,
                            'id': lin_brw.stock_move_id.id}
                    sql = ("update stock_move set " +
                           "date='%(date)s', " +
                           "location_id=%(location_id)s, " +
                           "location_dest_id=%(location_dest_id)s, " +
                           "product_qty=%(product_qty)s, " +
                           "pieces_qty=%(pieces_qty)s " +
                           "where id=%(id)s") % data
                    logger.info('Fixing stock.move: %s' % sql)
                    cr.execute(sql)
        return {'type': 'ir.actions.act_window_close'}

    def button_empty_new(self, cr, uid, ids, context=None):
        self.button_empty(cr, uid, ids, context=None)
        self._clear_data(cr, uid, ids, context=None)
        return True

    ##------------------------------------------------------------ on_change...

    def on_change_prod_lot_id(self, cr, uid, ids, prod_lot_id):
        res = {}
        if not prod_lot_id:
            return res
        ids = isinstance(ids, (int, long)) and [ids] or ids
        obj_lot = self.pool.get('stock.production.lot')
        lot_brw = obj_lot.browse(cr, uid, prod_lot_id, context=None)
        #~ wiz_brw = self.browse(cr, uid, ids[0], context=None)
        if lot_brw.move_ids:
            line_ids = []
            for m in lot_brw.move_ids:
                data = {
                    #~ 'line_id': wiz_brw.id,
                    'stock_move_id': m.id,
                    'date': m.date,
                    'location_id': m.location_id.id,
                    'location_dest_id': m.location_dest_id.id,
                    'product_qty': m.product_qty,
                    'pieces_qty': m.pieces_qty,
                    'name': m.state,
                    }
                #~ obj_lin.create(cr, uid, data, context)
                line_ids.append(data)
            line_ids.sort(key=lambda x: x['date'])
            line_ids.reverse()
            res.update({'line_ids': line_ids,
                        'product_id': lot_brw.product_id.id})
        return {'value': res}

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_fix_stock_move()


##---------------------------------------------------- tcv_fix_stock_move_lines


class tcv_fix_stock_move_lines(osv.osv_memory):

    _name = 'tcv.fix.stock.move.lines'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'line_id': fields.many2one(
            'tcv.fix.stock.move', 'String', required=True, ondelete='cascade'),
        'stock_move_id': fields.many2one(
            'stock.move', 'Stock move', ondelete='restrict', readonly=False),
        'date': fields.datetime(
            'Date', required=True),
        'location_id': fields.many2one(
            'stock.location', 'Location', ondelete='restrict', required=True),
        'location_dest_id': fields.many2one(
            'stock.location', 'Dest location', ondelete='restrict',
            required=True),
        'product_qty': fields.float(
            'Quantity', digits_compute=dp.get_precision('Product UoM'),
            required=True),
        'pieces_qty': fields.integer(
            'Pieces'),
        'name': fields.char(
            'State', size=16, readonly=True),
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

tcv_fix_stock_move_lines()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
