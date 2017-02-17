# -*- coding: utf-8 -*-
"""
    Company: Tecvemar, c.a.
    Author: Juan V. Márquez L.
    Creation Date: 05/06/2012
    Version: 0.0.0.0

    Description:
        Main model definition
"""

from datetime import datetime
from osv import fields,osv
from tools.translate import _
import pooler
import decimal_precision as dp
import time


class tcv_profit_codes(osv.osv):
   
    _name = 'tcv.profit.codes'
    
    _description = 'Save the profit code value'

    _columns = {
        'company_id': fields.many2one('res.company','Company', required=True, readonly=True),
        'type':fields.selection([('co_cli', 'cliente'), ('co_prov', 'Proveedor'), ('co_art', 'Producto')], 'Field type', required=True, select=True),
        'name':fields.char('Model name',64, required=True),
        'profit_code':fields.char('Profit code',64, required=True),
        'code_id':fields.integer('OpenERP ID', required=True),
        }
    
    _defaults = {
        'company_id':lambda s,cr,uid,c: s.pool.get('res.company')._company_default_get(cr, uid, 'tcv.profit.codes', context=c),
        }
        
    _sql_constraints = [
                 ('unique_code', 'UNIQUE(company_id, type, name, profit_code)', 'The profit code must be unique !'),
             ] 

tcv_profit_codes()













