# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2013-09-10
#    Version: 0.0.0.1
#
#    Description: Handle tecvemar's reports and views for sale process
#
#
##############################################################################

{
    "name": "tcv_sale",
    "version": "18.06",
    "depends": ["base", "account", "sale", "tcv_stock_driver",
                "tcv_calculator", "tcv_misc", "tcv_monthly_report",
                "tcv_bundle"],
    "author": "Juan Márquez",
    "description": """
        Handle tecvemar's reports and views for sale process

        Tecvemar, c.a.
        """,
    "website": "",
    "category": "Custom",
    "init_xml": [],
    "demo_xml": [],
    "update_xml": ['security/ir_rule.xml',
                   'security/security.xml',
                   'security/ir.model.access.csv',
                   'data/secuence.xml',
                   'data/sale_order_cron.xml',
                   'report/sale_order.xml',
                   'report/tcv_pricelist.xml',
                   'report/account_report.xml',
                   'report/tcv_sale_proforma.xml',
                   'report/tcv_sale_anual_report.xml',
                   'report/tcv_sale_time_lapse.xml',
                   'report/tcv_sale_top_10.xml',
                   'view/sale_order.xml',
                   'view/tcv_sale_proforma.xml',
                   'view/account_invoice_view.xml',
                   'view/tcv_sale_order_config_menus.xml',
                   'view/tcv_sale_proforma_menus.xml',
                   'view/tcv_pricelist.xml',
                   'wizard/sale_lot_list.xml',
                   'wizard/tcv_sale_data_collector.xml',
                   'wizard/tcv_lot_range_sale.xml',
                   'wizard/tcv_bundle_sale.xml',
                   'wizard/tcv_export_order_fix.xml',
                   'wizard/tcv_txt_profit_export.xml',
                   # ~ 'wizard/tcv_special_tax_sel.xml',  # Deprecated
                   'workflow/sale_order_workflow.xml',
                   'workflow/tcv_sale_proforma.xml',
                   ],
    "active": False,
    "installable": True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
