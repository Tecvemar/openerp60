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
from tools.translate import _
#~ import pooler
#~ import decimal_precision as dp
import time
#~ import netsvc

##----------------------------------------------------- tcv_get_bundle_tracking


class tcv_get_bundle_tracking(osv.osv_memory):

    _name = 'tcv.get.bundle.tracking'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def default_get(self, cr, uid, fields, context=None):
        data = super(tcv_get_bundle_tracking, self).\
            default_get(cr, uid, fields, context)
        if context.get('active_model') == u'stock.picking' and \
                context.get('active_id'):
            pic_id = context.get('active_id')
            obj_pic = self.pool.get('stock.picking')
            pic_brw = obj_pic.browse(cr, uid, pic_id, context=context)
            obj_bdl = self.pool.get('tcv.bundle.lines')
            line_ids = []
            for move in pic_brw.move_lines:
                if move.state not in ('done', 'cancel') and move.prodlot_id:
                    bdl_id = obj_bdl.search(
                        cr, uid, [('prod_lot_id', '=', move.prodlot_id.id)])
                    if not bdl_id:
                        raise osv.except_osv(
                            _('Error!'),
                            _('The lot %s is not linked to a bundle') %
                            move.prodlot_id.name)
                    bdl_brw = obj_bdl.browse(
                        cr, uid, bdl_id, context=context)
                    line_ids.append({
                        'move_id': move.id,
                        'product_id': move.product_id.id,
                        'prod_lot_id': move.prodlot_id.id,
                        'bundle_id': bdl_brw and bdl_brw[0].bundle_id.id,
                        })
            if pic_brw.state not in ('done', 'cancel'):
                lines = sorted(line_ids, key=lambda k: k['bundle_id'])
                data.update({'picking_id': pic_id,
                             'line_ids': lines})
        return data

    ##--------------------------------------------------------- function fields

    _columns = {
        'picking_id': fields.many2one(
            'stock.picking', 'Picking', ondelete='restrict', readonly=True),
        'line_ids': fields.one2many(
            'tcv.get.bundle.tracking.lines', 'line_id', 'String',
            readonly=True),
        }

    _defaults = {
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    def button_done(self, cr, uid, ids, context=None):
        obj_trk = self.pool.get('stock.tracking')
        obj_bun = self.pool.get('tcv.bundle')
        for item in self.browse(cr, uid, ids, context={}):
            trk_lst = {}
            used_bundle_ids = []
            for line in item.line_ids:
                if not line.bundle_id:
                    raise osv.except_osv(
                        _('Error!'),
                        _('No se encontro el bundle para el lote %s') %
                        line.prod_lot_id.name)
                if line.move_id.tracking_id:
                    raise osv.except_osv(
                        _('Error!'),
                        _('The traking number is already linked'))
                if line.bundle_id.name not in trk_lst:
                    used_bundle_ids.append(line.bundle_id.id)
                    trk_id = obj_trk.search(
                        cr, uid, [('name', '=', line.bundle_id.name)])
                    if trk_id:
                        raise osv.except_osv(
                            _('Error!'),
                            _('The tracking %s already exist') %
                            line.bundle_id.name)
                    trk_lst.update({line.bundle_id.name: {
                        'name': line.bundle_id.name,
                        'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'weight_net': line.bundle_id.weight_net,
                        'active': True,
                        'image': line.bundle_id.image,
                        'move_ids': [],
                        }})
                trk_lst[line.bundle_id.name]['move_ids'].append(
                    (4, line.move_id.id))
            for data in trk_lst.values():
                obj_trk.create(cr, uid, data, context)
                obj_bun.write(
                    cr, uid, used_bundle_ids, {'reserved': True},
                    context=context)
        return {'type': 'ir.actions.act_window_close'}

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_get_bundle_tracking()


##----------------------------------------------- tcv_get_bundle_tracking_lines


class tcv_get_bundle_tracking_lines(osv.osv_memory):

    _name = 'tcv.get.bundle.tracking.lines'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'line_id': fields.many2one(
            'tcv.get.bundle.tracking', 'String', required=True,
            ondelete='cascade'),
        'move_id': fields.many2one(
            'stock.move', 'Internal Moves',
            readonly=False, required=True, ondelete='restrict'),
        'product_id': fields.related(
            'move_id', 'product_id',
            type='many2one',
            relation='product.product',
            string='Product',
            store=False, readonly=True),
        'prod_lot_id': fields.related(
            'move_id', 'prodlot_id',
            type='many2one',
            relation='stock.production.lot',
            string='Production lot',
            store=False, readonly=True),
        'bundle_id': fields.many2one(
            'tcv.bundle', 'Bundle', ondelete='restrict'),
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

tcv_get_bundle_tracking_lines()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
