# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date: 
#    Version: 0.0.0.0
#
#    Description:
#
#
##############################################################################

from datetime import datetime
from osv import fields,osv
from tools.translate import _
import pooler
import decimal_precision as dp
import time

class res_partner(osv.osv):
    
    _inherit = 'res.partner'
    
    _columns = {
          'from_profit':fields.boolean('From profit', help='',),
          }  


    _defaults = {
        'from_profit': False,  
    }          

    def save_profit_code(self, cr, uid, vals, res_id, context=None):
        if vals.has_key('from_profit') and vals['from_profit'] and vals.has_key('profit_data'):
            #~ Crear datos en profit codes
            obj = self.pool.get('tcv.profit.codes')
            data = vals['profit_data']
            if type(res_id) == list:
                res_id = res_id[0]
            data.update({'code_id':res_id,'name':self._name})
            try:
                if not obj.search(cr, uid, [('company_id', '=', data['company_id']),
                                            ('type', '=', data['type']),
                                            ('name', '=', data['name']),
                                            ('profit_code', '=', data['profit_code'])]):
                    obj.create(cr, uid, data, context)
            except:
                pass    
    
    
    def create(self, cr, uid, vals, context=None):
        ## Se incorpora mara manejar el caso de vat duplicados
        if vals.get('vat'): 
            id = self.pool.get('res.partner').search(cr, uid, [('vat', '=', vals['vat'])])
            if id:
                self.save_profit_code(cr, uid, vals, id[0], context)
                return []    
        res = super(res_partner, self).create(cr, uid, vals, context)
        self.save_profit_code(cr, uid, vals, res, context)
        return res

        
    def write(self, cr, uid, ids, vals, context=None):
        res = super(res_partner, self).write(cr, uid, ids, vals, context)
        self.save_profit_code(cr, uid, vals, ids, context)    
        return res

res_partner()    
