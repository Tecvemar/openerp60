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
import time

class res_company(osv.osv):

    _inherit = "res.company"
    
    _columns = {
        'user_in_id':fields.many2one('res.users','User IN'),
        'location_stock_id':fields.many2one('stock.location','Stock Consignacion'),
        'location_stock_internal_id':fields.many2one('stock.location','Stock Internal'),
        'company_in_ids':fields.many2many('res.company','res_intercompany_rel','company_in_id','company_out_id','Companies'),
        'company_out_ids':fields.many2many('res.company','res_intercompany_rel','company_out_id','company_in_id','Companies'),
    
    }
    
res_company()
