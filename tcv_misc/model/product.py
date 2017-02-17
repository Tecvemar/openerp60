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
from osv import fields,osv
import decimal_precision as dp
from tools.translate import _


class product_template(osv.osv):
    _inherit = 'product.template'

    _columns = {
        #original definitios
        #'list_price': fields.float('Sale Price', digits_compute=dp.get_precision('Sale Price'), help="Base price for computing the customer price. Sometimes called the catalog price."),
        #'standard_price': fields.float('Cost Price', required=True, digits_compute=dp.get_precision('Purchase Price'), help="Product's cost for accounting stock valuation. It is the base price for the supplier price."),
        'property_list_price':fields.property(
            'product.template',
            type='float',
            string="Sale Price (multicompany)",
            method=True,
            view_load=True,
            digits_compute=dp.get_precision('Sale Price'),
            help="Base price for computing the customer price in multicompany environments."),
        'property_standard_price':fields.property(
            'product.template',
            type='float',
            string="Cost Price  (multicompany)",
            method=True,
            view_load=True,
            digits_compute=dp.get_precision('Purchase Price'),
            help="Product's cost for accounting stock valuation in multicompany environments."),
        'company_id': fields.many2one('res.company', 'Company',select=1,readonly=True),
        }


    # In our case all products are multicompany
    _defaults = {
        'company_id': False,
    }

    _sql_constraints = [
        ('volume_gt_zero', 'CHECK (volume>=0)', 'The volume must be >= 0!'),
        ('weight_gt_zero', 'CHECK (weight>=0)', 'The weight must be >= 0!'),
        ('weight_net_gt_zero', 'CHECK (weight_net>=0)', 'The net weight must be >= 0!'),
    ]

product_template()


class product_category(osv.osv):
    '''Added to create a unique field to identifi the category'''
    _inherit = 'product.category'

    _columns = {
        'code': fields.char('Code', size=16, help="Unique code for this category."),
        }

    _sql_constraints = [
                 ('code_uniq', 'UNIQUE(code)', 'The category code must be unique!'),
             ]

    _order = 'code'


    def write(self, cr, uid, ids, vals, context=None):
        #~ print vals
        res = super(product_category, self).write(cr, uid, ids, vals, context)
        return res

product_category()

