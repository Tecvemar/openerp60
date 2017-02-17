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


class price_type(osv.osv):
    _inherit = 'product.price.type'
    
    def _price_field_get(self, cr, uid, context=None):
        res = super(price_type, self)._price_field_get(cr, uid, context)
        # add special property fields
        res.append(('property_list_price','Sale Price (multicompany)'))
        res.append(('property_standard_price','Cost Price  (multicompany)'))
        return res
        
    _columns = {
        "field" : fields.selection(_price_field_get, "Product Field", size=32, required=True, help="Associated field in the product form."),
    }
        

price_type()
