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


class product_product(osv.osv):

    _inherit = 'product.product'

    _columns = {
        'ppty_muni_tax': fields.property(
            'tcv.municipal.taxes.config', type='many2one',
            relation='tcv.municipal.taxes.config', string="Municipal tax",
            method=True, view_load=True, required=False,
            readonly=False, help="The municipal tax code for this product"),
        }

product_product()


class product_category(osv.osv):

    _inherit = 'product.category'

    _columns = {
        'ppty_muni_tax': fields.property(
            'tcv.municipal.taxes.config', type='many2one',
            relation='tcv.municipal.taxes.config', string="Municipal tax",
            method=True, view_load=True, required=False,
            readonly=False,
            help="The municipal tax code for this category"),
        }

product_category()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
