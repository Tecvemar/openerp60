# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from osv import fields, osv
import decimal_precision as dp
from tools.translate import _
import time


class product_product(osv.osv):

    _inherit = 'product.product'

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    def get_property_list_price(self, cr, uid, product, prod_lot, currency_id):
        price_unit = product and product.property_list_price or 0
        if not currency_id:
            obj_cur = self.pool.get('res.currency')
            currency_id = obj_cur.search(
                cr, uid, [('name', '=', 'VEB')])[0]
        if prod_lot and currency_id:
            obj_prc = self.pool.get('tcv.pricelist')
            prc_ids = obj_prc.search(
                cr, uid,
                [('product_id', '=', prod_lot.product_id.id),
                 ('currency_id', '=', currency_id),
                 ('date', '<=', prod_lot.date)],
                limit=1, order='date desc')
            if prc_ids:
                prc_brw = obj_prc.browse(cr, uid, prc_ids[0], context=None)
                price_unit = prc_brw.price_unit
        return price_unit

    ##-------------------------------------------------------- buttons (object)

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow


product_product()


##--------------------------------------------------------------- tcv_pricelist


class tcv_pricelist(osv.osv):

    _name = 'tcv.pricelist'

    _order = 'currency_id,date,product_id'

    ##-------------------------------------------------------------------------

    ##------------------------------------------------------- _internal methods

    ##--------------------------------------------------------- function fields

    _columns = {
        'company_id': fields.many2one(
            'res.company', 'Company', required=True, readonly=True,
            ondelete='restrict'),
        'date': fields.date(
            'Date', required=True, readonly=False, select=True),
        'product_id': fields.many2one(
            'product.product', 'Product', ondelete='restrict', required=True),
        'property_list_price': fields.related(
            'product_id', 'property_list_price', type='float',
            digits_compute=dp.get_precision('Account'),
            string='Price (Multicompany)', store=False, readonly=True),
        'price_unit': fields.float(
            'Unit price', digits_compute=dp.get_precision('Account'),
            required=True),
        'currency_id': fields.many2one(
            'res.currency', 'Currency', required=True),
        #~ 'quality': fields.selection(
            #~ [('extra', 'Extra'), ('estandar', 'Estandar'),
             #~ ('comercial', 'Comercial')],
            #~ 'Quality', readonly=False
            #~ ),
        'print': fields.boolean(
            'Imprimir'),
        }

    _defaults = {
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company').
        _company_default_get(cr, uid, self._name, context=c),
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        }

    _sql_constraints = [
        ('price_unique', 'UNIQUE(company_id,date,product_id,currency_id)',
         'The price must be unique!'),
        ]

    ##-------------------------------------------------------------------------

    ##---------------------------------------------------------- public methods

    ##-------------------------------------------------------- buttons (object)

    def update_price(self, cr, uid, ids, context=None):
        ids = isinstance(ids, (int, long)) and [ids] or ids
        if len(ids) != 1:
            raise osv.except_osv(
                _('Error!'),
                _('Only one product by time'))
        obj_prd = self.pool.get('product.product')
        for item in self.browse(cr, uid, ids, context={}):
            if item.product_id and item.price_unit:
                obj_prd.write(
                    cr, uid, [item.product_id.id],
                    {'property_list_price': item.price_unit}, context=context)
        return True

    ##------------------------------------------------------------ on_change...

    ##----------------------------------------------------- create write unlink

    ##---------------------------------------------------------------- Workflow


tcv_pricelist()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
