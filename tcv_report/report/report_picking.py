# -*- encoding: utf-8 -*-
############################################################################
#    Module Writen to OpenERP, Open Source Management Solution             #
#    Copyright (C) OpenERP Venezuela (<http://openerp.com.ve>).            #
#    All Rights Reserved                                                   #
###############Credits######################################################
#    Coded by: Maria Gabriela Quilarque  <gabrielaquilarque97@gmail.com>   #
#    Planified by: Nhomar Hernandez                                        #
#    Finance by: Helados Gilda, C.A. http://heladosgilda.com.ve            #
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

class tcv_picking_report(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        if context is None:
            context = {}
        super(tcv_picking_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'get_type': self.get_type,
            'get_total': self.get_total,
        })

    def get_total(self,aux,move_lines):
        aux2=0
        if aux=='total':
            for i in move_lines:
                aux2+=1
        else:
            for i in move_lines:
                if i.product_id.stock_driver and i.product_id.stock_driver == aux:
                    aux2+=1
            return aux2
        return aux2
        

    def get_type(self,obj):
        
        drv = obj.product_id.stock_driver
        
        if drv == 'tile':
            name ='BA'
        elif drv == 'slab':
            name ='LA'
        elif drv == 'block':
            name ='BL'
        elif drv == 'normal':
            name ='NO'
            
        return name

report_sxw.report_sxw(
  'report.tcv_picking_report.tcv_picking_report',
  'stock.picking',
  'addons/tcv_report/report/report_picking.rml',
  parser=tcv_picking_report
)
  # 1 addons/nombre del modulo/carpeta(report)/nombre del archivo rml
  # 2 A modo didactico vamos a poner que el modulo al que le vamos a poner el reporte es a res.partner
  #   pero podria ser cualquier modulo.
