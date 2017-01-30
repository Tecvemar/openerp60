# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Marquez
#    Creation Date: 13/09/2012
#    Version: 0.0.0.1
#
#    Description:
#
#
##############################################################################
{
    "name": "Tecvemar - Purchase",
    "version": "0.1",
    "depends": ["base", "purchase", "tcv_import_management",
                "l10n_ve_sale_purchase"],
    "author": "Tecvemar - Juan Márquez",
    "description": "Purchase order customizations",
    "website": "",
    "category": "Custom",
    "init_xml": [],
    "demo_xml": [],
    "update_xml": ['wizard/purchase_lot_list.xml',
                   'view/purchase_view.xml',
                   'view/account_invoice_view.xml',
                   'view/partner_view.xml',
                   'report/purchase.xml',
                   'report/tcv_purchase_anual_report.xml',
                   'security/security.xml',
                   ],
    "active": False,
    "installable": True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
