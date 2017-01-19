# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2014-06-18
#    Version: 0.0.0.1
#
#    Description:
#
#
##############################################################################
#
# __openerp__.py

{
    "name": "tcv_payroll_import",
    "version": "",
    "depends": ["base", "hr", "tcv_profit_import", "tcv_account_management",
                ],
    "author": "Juan Márquez",
    "description":"""
        Tecvemar, c.a.
        """,
    "website": "",
    "category": "Custom",
    "init_xml": [],
    "demo_xml": [],
    "update_xml": ['security/security.xml',
                   'security/ir.model.access.csv',
                   'security/ir_rule.xml',
                   'data/sequence.xml',
                   'view/tcv_payroll_import_data.xml',
                   'view/tcv_payroll_import_table.xml',
                   'view/tcv_payroll_import_job.xml',
                   'view/tcv_payroll_import.xml',
                   'wizard/tcv_payroll_import_profit.xml',
                   'view/tcv_payroll_import_menus.xml',
                   'workflow/tcv_payroll_import.xml',
                   'report/tcv_payroll_import.xml',
                   ],
    "active": False,
    "installable": True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
