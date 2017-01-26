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
    "name": "Tecvemar - Import management",
    "version": "0.1",
    "depends": ["base", "account", "stock", "decimal_precision",
                "l10n_ve_imex", "purchase"],
    "author": "Tecvemar - Juan Márquez",
    "description": "Import management",
    "website": "",
    "category": "Custom",
    "init_xml": [],
    "demo_xml": [],
    "update_xml": [
        'security/security.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'data/import_management_data.xml',
        'wizard/tcv_import_cost_wizard_view.xml',
        'wizard/tcv_create_import_lot.xml',
        'wizard/tcv_set_import_cost.xml',
        'view/tcv_import_management.xml',
        'view/tcv_import_config.xml',
        'view/account_invoice_view.xml',
        'view/purchase_view.xml',
        'workflow/tcv_import_management.xml',
        'workflow/account_invoice_workflow.xml',
        'data/sequence.xml',
        'report/tcv_import_management.xml',
        ],
    "active": False,
    "installable": True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
