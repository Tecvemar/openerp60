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

#~ Se sobreescribe para transmitir el ID del partner via context
#~ Requiere solucion bug: https://bugs.launchpad.net/account-management/+bug/994168
#~ Los datos se transfireren en el key:res_partner_account_id_ref

from osv import fields,osv


class res_partner(osv.osv):
    
    _inherit = 'res.partner'    
    
    def _update_code(self, cr, uid,ids,vals, context=None):
        context.update({'res_partner_account_id_ref':ids}) 
        return super(res_partner, self)._update_code(cr, uid, ids, vals, context)


res_partner()
