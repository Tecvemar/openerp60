# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2017-04-03
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
import netsvc
import logging
logger = logging.getLogger('server')

__to_dispatch_str__ = '-PD'

##------------------------------------------------------ tcv_to_dispatch_config


class tcv_to_dispatch_config(osv.osv):

    _name = 'tcv.to.dispatch.config'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def _copy_to_dispatch_picking(self, pck, cfg):
        return {
            'name': '%s%s' % (pck.name, __to_dispatch_str__),
            'origin': pck.origin,
            'address_id': pck.address_id.id,
            'min_date': pck.min_date,
            'date': pck.date,
            'stock_journal_id': pck.stock_journal_id.id,
            'backorder_id': pck.id,
            'partner_id': pck.partner_id.id,
            'auto_picking': False,
            'company_id': pck.company_id.id,
            'invoice_state': pck.invoice_state,
            'state': 'draft',
            'type': pck.type,
            'move_type': pck.move_type,
            'sale_id': pck.sale_id.id,
            'container': pck.container,
            'note': pck.note,
            }

    def _copy_to_dispatch_move_line(self, sm, cfg):
        return {
            'product_id': sm.product_id.id,
            'name': sm.name,
            'date': sm.date,
            'location_id': cfg.location_dest_id.id,
            'location_dest_id': cfg.location_id.id,
            'pieces_qty': sm.pieces_qty,
            'product_qty': sm.product_qty,
            'product_uom': sm.product_uom.id,
            'product_uos_qty': sm.product_uos_qty,
            'product_uos': sm.product_uos.id,
            'prodlot_id': sm.prodlot_id.id,
            'state': 'draft',
            }

    ##--------------------------------------------------------- function fields

    _columns = {
        'name': fields.char(
            'Name', size=64, required=False, readonly=False),
        'date_from': fields.date(
            'Date from', required=True, readonly=False,
            help="Create picking for moves from this date"),
        'location_id': fields.many2one(
            'stock.location', 'Actual dest Loc', required=True,
            readonly=False, ondelete='restrict',
            help="Autocreate stock picking to dispatch product/lot when " +
            "stock move isn't done and destination location is this. " +
            "Usually 'Customers'"),
        'location_dest_id': fields.many2one(
            'stock.location', 'To dispatch loc', required=True, readonly=False,
            ondelete='restrict',
            help="Move to dispatch product/lot to this location. Can't be a " +
            "chained location, Usually 'To dispatch'"),
        'stock_journal_id': fields.many2one(
            'stock.journal', 'Stock Journal', required=False,
            select=True, ondelete='restrict',
            help="Only select picking in this journal"),
        'company_id': fields.many2one(
            'res.company', 'Company', required=True, readonly=True,
            ondelete='restrict'),
        }

    _defaults = {
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company').
        _company_default_get(cr, uid, self._name, context=c),
        'date': lambda *a: time.strftime('%Y-01-01'),
        }

    _sql_constraints = [
        ('company_uniq', 'UNIQUE(company_id)',
         'The config must be unique for company!'),
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    def get_config(self, cr, uid, company_id=None, context=None):
        cfg_id = self.search(cr, uid, [])
        if cfg_id and len(cfg_id) == 1:
            cfg_id = cfg_id[0]
            return self.browse(cr, uid, cfg_id, context)
        else:
            logger.warn('No stock picking to dispatch settings !')
            return False

    def generate_to_dispatch_picking(self, cr, uid, context=None):
        cfg = self.get_config(cr, uid)
        if not cfg:
            return False
        obj_pck = self.pool.get('stock.picking')
        obj_mov = self.pool.get('stock.move')
        wf_service = netsvc.LocalService("workflow")
        logger.info(
            'Looking for stock picking to dispatch. From date: %s' %
            cfg.date_from)
        picking_ids = obj_pck.search(
            cr, uid, [('state', 'in', ('confirmed', 'assigned')),
                      ('date', '>=', cfg.date_from),
                      ('stock_journal_id', '=', cfg.stock_journal_id.id),
                      ('type', '=', 'out'),
                      ('sale_id', '!=', None),
                      ('company_id', '=', cfg.company_id.id)],
            order='name')
        to_dispatch = 0
        for pck in obj_pck.browse(cr, uid, picking_ids, context=context):
            if __to_dispatch_str__ in pck.name:
                continue  # Skip already processed pickings
            # Check all invoice's state in open or paid
            inv_ok = all([bool(x.state in ('open', 'paid'))
                          for x in pck.sale_id.invoice_ids])
            # Check all stock move's origin != 'to dispatch' location
            loc_ok = all([x.location_id.id != cfg.location_dest_id.id
                          for x in pck.move_lines])
            # Check if not tracking assigned to stock move
            trk_ok = all([not(x.tracking_id) for x in pck.move_lines])
            so_ok = pck.sale_id.order_policy == 'prepaid'
            if inv_ok and loc_ok and trk_ok and so_ok:
                to_dispatch += 1
                new_pck = self._copy_to_dispatch_picking(pck, cfg)
                move_lines = []
                for sm in pck.move_lines:
                    line = self._copy_to_dispatch_move_line(sm, cfg)
                    obj_mov.write(
                        cr, uid, [sm.id],
                        {'location_dest_id': cfg.location_dest_id.id},
                        context=context)
                    move_lines.append((0, 0, line))
                new_pck.update({'move_lines': move_lines})
                new_pck_id = obj_pck.create(cr, uid, new_pck, context)
                if new_pck_id:
                    logger.info(
                        'Set stock picking %s to dispatch.' % pck.name)
                    # Original pick workflow
                    if pck.state == 'confirmed':
                        obj_pck.action_assign(cr, uid, [pck.id])
                    wf_service.trg_validate(
                        uid, 'stock.picking', pck.id, 'button_done', cr)
                    # New pick workflow
                    wf_service.trg_validate(
                        uid, 'stock.picking', new_pck_id, 'button_confirm', cr)
            else:
                logger.info('Stock picking %s ignored.' % pck.name)
        if not to_dispatch:
            logger.info('No stock picking to dispatch.')
        return True

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow


tcv_to_dispatch_config()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
