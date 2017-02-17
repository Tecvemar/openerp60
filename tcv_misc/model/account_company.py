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

#~ Este Metodo sobreescribe la funcion para autoasignacion de codigos del modulo account_management
#~ con la intencion de usar el ID del partner como auxiliar en lugar de un correlativo

from osv import fields,osv


class account_account(osv.osv):

    _inherit='account.account'
    
    def _get_custom_number(self, cr, uid, context=None):
        '''Override this method to set your 
        own number used in the accounting accounts'''
        if context is None: context = {}
        if context.get('res_partner_account_id_ref',False) and context['res_partner_account_id_ref'] and len(context['res_partner_account_id_ref']):
            return context['res_partner_account_id_ref'][0]
        return None    
        

account_account()
