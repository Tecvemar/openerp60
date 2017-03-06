# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Marquez
#    Creation Date: 23/09/2012
#    Version: 0.0.0.1
#
#    Description:
#
#
##############################################################################
{
    "name" : "Tecvemar - Profit import",
    "version" : "0.1",
    "depends" : ["base", "account", "purchase", "sale", "tcv_monthly_report"],
    "author" : "Tecvemar - Juan Márquez",
    "description" : "Tecvemar - Tools for document imports",
    "website" : "",
    "category" : "Custom",
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : [
        'security/security.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'view/tcv_profit_import_config.xml',
        'wizard/tcv_base_import.xml',
        'wizard/tcv_sale_order_import.xml',
        'wizard/tcv_purchase_order_import.xml',
        'wizard/tcv_stock_picking_import.xml',
        'wizard/tcv_sale_order_csv_import.xml',
        'wizard/tcv_load_external_data.xml',
        'report/tcv_related_annual_sales.xml',
        'view/tcv_profit_import_menus.xml',
        ],
    "active": False,
    "installable": True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
