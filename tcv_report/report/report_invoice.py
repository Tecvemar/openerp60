# -*- encoding: utf-8 -*-
############################################################################
#    Module Writen to OpenERP, Open Source Management Solution             #
#    Copyright (C) OpenERP Venezuela (<http://openerp.com.ve>).            #
#    All Rights Reserved                                                   #
###############Credits######################################################
#    Coded by: Jose Antonio Morales  <jose@vauxoo.com>                     #
#    Planified by: Nhomar Hernandez                                        #
#    Finance by: Tecvemar, C.A. http://tecvemar.com.ve                     #
#    Audited by: Humberto Arocha humberto@openerp.com.ve                   #
############################################################################
#    This program is free software: you can redistribute it and/or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation, either version 3 of the License, or     #
#    (at your option) any later version.                                   #
#                                                                          #
#    This program is distributed in the hope that it will be useful,       #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of        #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         #
#    GNU General Public License for more details.                          #
#                                                                          #
#    You should have received a copy of the GNU General Public License     #
#    along with this program.  If not, see <http://www.gnu.org/licenses/>. #
############################################################################
import time
import pooler
from report import report_sxw
from tools.translate import _

class tcv_invoice_report(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        if context is None:
            context = {}
        super(tcv_invoice_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'get_date': self._get_date,
            '_get_name':self._get_name,
            'get_tax':self._get_tax,
        })

    def _get_date(self,obj,aux):
        aux2= obj.date_invoice
        DMY=str(aux2)
        res= DMY.split('/')
        if aux == 0:
            return res[0]
        if aux == 1:
            return res[1]
        if aux == 2:
            return res[2]
            
    def _get_name(self,obj):
        
        drv = obj.prod_lot_id.product_id.stock_driver
       
        if drv == 'tile':
            name = '%s (%sx%s)' % (obj.prod_lot_id.name.strip(),obj.prod_lot_id.length /10,obj.prod_lot_id.heigth /10)
        elif drv == 'slab':
            name = '%s (%sx%s)' % (obj.prod_lot_id.name.strip(),obj.prod_lot_id.length /10 ,obj.prod_lot_id.heigth /10)
        elif drv == 'block':
            name = '%s (%sx%sx%s)' % (obj.prod_lot_id.name.strip(),obj.prod_lot_id.length /10,obj.prod_lot_id.heigth/10,obj.prod_lot_id.width /10)
       
        return name
        
    def _get_tax(self,obj):
        
        return (obj.invoice_line_tax_id[0].amount *100)
        
        
report_sxw.report_sxw(
  'report.tcv_report.tcv_report',
  'account.invoice',
  'addons/tcv_report/report/report_invoice.rml',
  parser=tcv_invoice_report
)
  # 1 addons/nombre del modulo/carpeta(report)/nombre del archivo rml
  # 2 A modo didactico vamos a poner que el modulo al que le vamos a poner el reporte es a res.partner
  #   pero podria ser cualquier modulo.
