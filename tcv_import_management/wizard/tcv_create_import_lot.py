# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description: Report parser for: tcv_create_import_lot
#
#
##############################################################################
#~ from report import report_sxw
#~ from datetime import datetime
from osv import fields, osv
from tools.translate import _
#~ import pooler
#~ import decimal_precision as dp
import time
#~ import netsvc


##------------------------------------------------------- tcv_create_import_lot


class tcv_create_import_lot(osv.osv_memory):

    _name = 'tcv.create.import.lot'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def default_get(self, cr, uid, fields, context=None):
        context = context or {}
        data = super(tcv_create_import_lot, self).default_get(
            cr, uid, fields, context)
        if context.get('active_model') == u'tcv.import.management' \
                and context.get('active_id'):
            data.update({
                'import_id': context.get('active_id'),
                })
            obj_imp = self.pool.get('tcv.import.management')
            obj_lot = self.pool.get('stock.production.lot')
            imp_brw = obj_imp.browse(cr, uid, data['import_id'], context={})
            line_ids = []
            for line in imp_brw.line_ids:
                lot_ids = obj_lot.search(
                    cr, uid, [('product_id', '=', line.product_id.id),
                              ('name', '=', imp_brw.name)])
                line_ids.append({'prod_lot_id': lot_ids and lot_ids[0] or 0,
                                 'product_id': line.product_id.id,
                                 'name': imp_brw.name})
            data.update({'line_ids': line_ids})
        return data

    ##--------------------------------------------------------- function fields

    _columns = {
        'name': fields.char(
            'Name', size=64, required=False, readonly=False),
        'import_id': fields.many2one(
            'tcv.import.management', 'Import exp', required=False,
            ondelete='restrict', readonly=True),
        'line_ids': fields.one2many(
            'tcv.create.import.lot.lines', 'line_id', 'String'),
        }

    _defaults = {
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    def button_apply(self, cr, uid, ids, context=None):
        obj_lot = self.pool.get('stock.production.lot')
        obj_note = self.pool.get('tcv.import.notes')
        new_lot = False
        for item in self.browse(cr, uid, ids, context={}):
            for line in item.line_ids:
                if not line.prod_lot_id:
                    lot = {
                        'name': line.name,
                        'product_id': line.product_id.id,
                        }
                    obj_lot.create(cr, uid, lot, context)
                    new_lot = True
            if new_lot:
                obj_note.create(
                    cr, uid, {
                        'import_id': item.import_id.id,
                        'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'name': _('Referenced lots created!'),
                        'locked': True,
                        }, context)
        return {'type': 'ir.actions.act_window_close'}

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_create_import_lot()


##------------------------------------------------- tcv_create_import_lot_lines


class tcv_create_import_lot_lines(osv.osv_memory):

    _name = 'tcv.create.import.lot.lines'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'line_id': fields.many2one(
            'tcv.create.import.lot', 'String', required=True,
            ondelete='cascade'),
        'product_id': fields.related(
            'prod_lot_id', 'product_id', type='many2one',
            relation='product.product', string='Block / Product',
            store=True, readonly=True),
        'name': fields.char(
            'Name', size=64, required=True, readonly=False),
        'prod_lot_id': fields.many2one(
            'stock.production.lot', 'Production lot', required=False),

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

tcv_create_import_lot_lines()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
