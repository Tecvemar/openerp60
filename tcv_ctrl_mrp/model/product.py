# -*- coding: utf-8 -*-
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

class product_product(osv.osv):
    # TODO product.procudt or product.template 
    _inherit = 'product.product'

    _columns = {
        'resulting_products_ids': fields.many2many('product.product', 'rel_product_resulting_products', 'product_id1', 'product_id2', 'Resulting products')
        }
        
    
product_product()
            
           
