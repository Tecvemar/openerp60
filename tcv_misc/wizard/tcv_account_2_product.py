# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2013-09-23
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
#~ import time
#~ import netsvc

##------------------------------------------------------- tcv_account_2_product


class tcv_account_2_product(osv.osv_memory):

    _name = 'tcv.account.2.product'

    _description = ''

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    def default_get(self, cr, uid, fields, context=None):
        context = context or {}
        data = super(tcv_account_2_product, self).default_get(cr, uid, fields,
                                                              context)
        if context.get('active_model') == 'account.account' and \
                context.get('active_id'):
            obj_acc = self.pool.get('account.account')
            acc = obj_acc.browse(cr, uid, context['active_id'],
                                 context=context)
            obj_wh = self.pool.get('islr.wh.concept')
            wh_id = obj_wh.search(cr, uid, [('name', '=',
                                             'NO APLICA RETENCION')])
            obj_prd = self.pool.get('product.product')
            prd_id = obj_prd.search(cr, uid, [('default_code', '=',
                                               acc.code)])
            data.update({'account_id': acc.id,
                         'name': '%s / %s' % (acc.parent_id.name, acc.name),
                         'concept_id': wh_id[0] if wh_id else 0,
                         'product_id': prd_id[0] if prd_id else 0})
        return data

    ##--------------------------------------------------------- function fields

    _columns = {
        'account_id': fields.many2one('account.account', 'Account',
                                      required=True, ondelete='restrict'),
        'name': fields.char('Product name', size=64, required=True,
                            readonly=False),
        'concept_id': fields.many2one('islr.wh.concept', 'Withhold  Concept'),
        'product_id': fields.many2one('product.product', 'Product',
                                      readonly=True),
        }

    _defaults = {
        }

    _sql_constraints = [
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    def button_create_product(self, cr, uid, ids, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        for item in self.browse(cr, uid, ids, context={}):
            obj_prd = self.pool.get('product.product')
            prd_id = obj_prd.search(cr, uid, [('default_code', '=',
                                               item.account_id.code)])
            if not prd_id:
                categ = self.pool.get('product.category').\
                    search(cr, uid, [('code', '=', '4430')])
                categ_id = categ[0] if categ else 0
                uom = self.pool.get('product.uom').\
                    search(cr, uid, [('name', '=', 'PCE')])
                uom_id = uom[0] if uom else 0
                tax = self.pool.get('account.tax').\
                    search(cr, uid, [('name', '=', 'IVA 12% Compras')])
                taxes_id = [(4, tax[0])] if tax else []
                prd = {'name': item.name,
                       'default_code': item.account_id.code,
                       'sale_ok': False,
                       'purchase_ok': True,
                       'type': 'service',
                       'procure_method': 'make_to_stock',
                       'supply_method': 'buy',
                       'cost_method': 'standard',
                       'categ_id': categ_id,
                       'uom_id': uom_id,
                       'uom_po_id': uom_id,
                       'stock_driver': 'normal',
                       'mes_type': 'fixed',
                       'property_account_expense': item.account_id.id,
                       'concept_id': item.concept_id.id,
                       'taxes_id': taxes_id}
                prd_id = obj_prd.create(cr, uid, prd, context)
        prd_id = prd_id[0] if isinstance(prd_id, (list)) else prd_id
        res = {'name': _('Create product from account'),
               'type': 'ir.actions.act_window',
               'res_model': 'product.product',
               'view_type': 'form',
               'view_id': False,
               'view_mode': 'form',
               'nodestroy': True,
               'target': 'current',
               'domain': "",
               'context': {},
               'res_id': prd_id}
        self.write(cr, uid, [item.id], {'product_id': prd_id}, context=context)
        return res

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow

tcv_account_2_product()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
