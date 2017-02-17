# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date: 10/12/2012
#    Version: 0.0.0.0
#
#    Description:
#
#
##############################################################################

import time

from report import report_sxw

class sale_order_parser(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context=None):
        super(sale_order_parser, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'get_vat':self._get_vat,
            'get_product_name':self._get_product_name,
            'get_lot_name':self._get_lot_name,
            'get_product_unit':self._get_product_unit,
        })
        
    
    def _get_vat(self,vat):
        if vat and vat[:2] == 'VE':
            r1 = vat[2]
            r2 = vat[3:11]
            r3 = vat[11]
            rif = r1
            if r2:
                rif = '%s-%s'%(rif,r2)
                if r3:
                    rif = '%s-%s'%(rif,r3)
            res = rif.upper().strip()
        else:
            res = ''
        return res
        
    def _get_product_name(self,obj):
        name = '[%s] %s'%(obj.product_id.default_code,obj.name)
        return name        

                
    def _get_lot_name(self,obj):
        
        drv = obj.prod_lot_id.product_id.stock_driver
       
        name = ''
        if obj.prod_lot_id.product_id.track_outgoing:
            if drv == 'tile':
                name = '%s (%sx%s)' % (obj.prod_lot_id.name.strip(),obj.prod_lot_id.length,obj.prod_lot_id.heigth)
            elif drv == 'slab':
                name = '%s (%sx%s)' % (obj.prod_lot_id.name.strip(),obj.prod_lot_id.length ,obj.prod_lot_id.heigth)
            elif drv == 'block':
                name = '%s (%sx%sx%s)' % (obj.prod_lot_id.name.strip(),obj.prod_lot_id.length,obj.prod_lot_id.heigth,obj.prod_lot_id.width)
            else:
                name = obj.prod_lot_id.name.strip()
        return name 
        
        
    def _get_product_unit(self,unit_name):
        
        if unit_name == 'm2':
            return u'm\u00b2'
        if unit_name == 'm3':
            return u'm\u00b3'
        else: 
            return unit_name

report_sxw.report_sxw('report.tcv_report.sale_order', 
                      'sale.order', 
                      'addons/tcv_report/report/sale_order.rml', 
                      parser=sale_order_parser, 
                      header=False)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

