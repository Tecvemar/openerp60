# -*- encoding: utf-8 -*-
##############################################################################
#    Company:
#    Author: Gabriel
#    Creation Date: 2014-11-05
#    Version: 1.0
#
#    Description:
#
#
##############################################################################

#~ from datetime import datetime
from osv import fields, osv
from tools.translate import _
#~ import pooler
import decimal_precision as dp
#~ import time
#~ import netsvc

##------------------------------------------------------------------ tcv_export_order_fix


class tcv_export_order_fix(osv.osv_memory):

    _name = 'tcv.export.order.fix'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def default_get(self, cr, uid, fields, context=None):
        context = context or {}
        data = super(tcv_export_order_fix, self).default_get(cr, uid, fields,
                                                             context)
        if context.get('active_model') == 'sale.order' and \
                context.get('active_id'):
            obj_ord = self.pool.get('sale.order')
            ord_brw = obj_ord.browse(cr, uid, context.get('active_id'),
                                     context=context)
            product_ids = []
            if ord_brw.state != 'draft':
                raise osv.except_osv(_('Error!'),
                                     _('you cannot update the values of a order in state != draft'))
            for line in ord_brw.order_line:
                if not line.product_id.id in product_ids:
                    product_ids.append(line.product_id.id)
            line_ids = []
            for item in product_ids:
                line_ids.append({'product_id': item})
            if line_ids:
                data.update({'line_ids': line_ids,
                            })
        return data

    ##--------------------------------------------------------- function fields

    _columns = {
        'name': fields.char(
            'Name', size=64, required=False, readonly=False),
        'line_ids': fields.one2many(
            'tcv.export.order.fix.lines', 'line_id', 'String'),
        }

    _defaults = {
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    def button_fix_order(self, cr, uid, ids, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        if context.get('active_model') == 'sale.order' and \
                context.get('active_id'):
            obj_ord = self.pool.get('sale.order')
            obj_oln = self.pool.get('sale.order.line')
            ord_brw = obj_ord.browse(cr, uid, context.get('active_id'),
                                     context=context)
            for item in self.browse(cr, uid, ids, context={}):
                for line in item.line_ids:
                    if line.amount and line.product_id:
                        ord_lines = obj_oln.search(
                            cr, uid, [('order_id', '=', ord_brw.id),
                                      ('product_id','=',line.product_id.id)])
                        if ord_lines:
                            obj_oln.write(
                                cr, uid, ord_lines,
                                {'price_unit': line.amount,
                                 'tax_id': [(6, 0, [line.tax_id.id])],
                                 },
                                context=context)
        return {'type': 'ir.actions.act_window_close'}

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_export_order_fix()


class tcv_export_order_fix_lines(osv.osv_memory):

    _name = 'tcv.export.order.fix.lines'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'name': fields.char(
            'Name', size=64, required=False, readonly=False),
        'line_id': fields.many2one(
            'tcv.export.order.fix', 'String',
            ondelete='cascade'),
        'product_id': fields.many2one(
            'product.product', 'Product', ondelete='restrict'),
        'amount': fields.float(
            'Amount', digits_compute=dp.get_precision('Account')),
        'tax_id': fields.many2one(
            'account.tax', 'Tax', required=True, ondelete='restrict',
            domain=[('type_tax_use', '=', 'sale')]),
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

tcv_export_order_fix_lines()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
