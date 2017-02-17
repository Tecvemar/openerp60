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


{
    "name" : "Tecvemar - Misc module",
    "version" : "0.1",
    "depends" : ["base", 
                 "base_setup",
                 "product",
                 #~ "account", #se elimino para heredar desde account_anglo_saxon
                 "sale",
                 "stock",
                 "account",
                 "account_management",
                 "account_anglo_saxon",
                 "l10n_ve_fiscal_requirements",
                 ],
    "author" : "Tecvemar - Juan Márquez",
    "description" : """
    This module adds misc functionality and data for Tecvemar's implementation

    -Product.template; Fields: list_price & standart_price -> propertys
    -Account.tax; Fields: account_collected_id & account_paid_id -> propertys
    -product.category: Fields: code
    """,
    "website" : "",
    "category" : "Custom",
    "init_xml" : [
    ],
    "demo_xml" : [
    ],
    "update_xml" : ['view/product_view.xml',
                    'view/res_currency_view.xml',
                    'view/stock_view.xml',
                    'view/partner_view.xml',
                    'view/account_view.xml',
                    'wizard/tcv_account_2_product.xml',
                    'security/sale_security.xml',
                    'workflow/sale_workflow.xml',
                    'data/ir_rule.xml',
    ],
    "active": False,
    "installable": True,
}     

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
