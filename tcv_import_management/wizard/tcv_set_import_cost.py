# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date:
#    Version: 0.0.0.0
#
#    Description: Report parser for: tcv_set_import_cost
#
#
##############################################################################
#~ from report import report_sxw
#~ from datetime import datetime
from osv import fields, osv
from tools.translate import _
#~ import pooler
import decimal_precision as dp
import time
#~ import netsvc


##--------------------------------------------------------- tcv_set_import_cost


class tcv_set_import_cost(osv.osv_memory):

    _name = 'tcv.set.import.cost'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def default_get(self, cr, uid, fields, context=None):
        context = context or {}
        data = super(tcv_set_import_cost, self).default_get(
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
                if len(lot_ids) == 1 and line.real_cost_unit > 0:
                    line_ids.append({'prod_lot_id': lot_ids[0],
                                     'product_id': line.product_id.id,
                                     'amount': line.real_cost_unit})
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
            'tcv.set.import.cost.lines', 'line_id', 'String'),
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
                obj_lot.write(
                    cr, uid, line.prod_lot_id.id,
                    {'property_cost_price': line.amount},
                    context=context)
                new_lot = True
            if new_lot:
                obj_note.create(
                    cr, uid, {
                        'import_id': item.import_id.id,
                        'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'name': _('Cost lots updated!'),
                        'locked': True,
                        }, context)
        return {'type': 'ir.actions.act_window_close'}

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_set_import_cost()


##--------------------------------------------------- tcv_set_import_cost_lines


class tcv_set_import_cost_lines(osv.osv_memory):

    _name = 'tcv.set.import.cost.lines'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'line_id': fields.many2one(
            'tcv.set.import.cost', 'String', required=True,
            ondelete='cascade'),
        'prod_lot_id': fields.many2one(
            'stock.production.lot', 'Production lot', required=True),
        'product_id': fields.related(
            'prod_lot_id', 'product_id', type='many2one',
            relation='product.product', string='Block / Product',
            store=True, readonly=True),
        'amount': fields.float(
            'Amount', digits_compute=dp.get_precision('Account')),

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

tcv_set_import_cost_lines()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
