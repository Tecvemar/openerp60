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
#~ ##############################################################################
from osv import fields,osv
import decimal_precision as dp
from tools.translate import _


#~ class stock_production_lot(osv.osv):
#~
    #~ _inherit = 'stock.production.lot'
#~
    #~ _columns = {
        #~ 'property_cost_price':fields.property(
            #~ 'product.template',
            #~ type='float',
            #~ string="Cost Price (multicompany)",
            #~ method=True,
            #~ view_load=True,
            #~ digits_compute=dp.get_precision('Purchase Price'),
            #~ help="Lot's cost for accounting stock valuation in multicompany environments."),
        #~ }
#~
#~ stock_production_lot()
