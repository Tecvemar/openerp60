# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2014-06-25
#    Version: 0.0.0.1
#
#    Description:
#
#
##############################################################################
#
# __openerp__.py

{
    "name": "tcv_hr",
    "version": "",
    "depends": ["base","hr"],
    "author": "Juan Márquez",
    "description":"""
        Extends basic hr module to add some required fields
        Tecvemar, c.a.
        """,
    "website": "",
    "category": "Custom",
    "init_xml": [],
    "demo_xml": [],
    "update_xml": ['security/ir_rule.xml',
                   'view/hr_view.xml',
                   'wizard/tcv_employee_2_account.xml',
                   ],
    "active": False,
    "installable": True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
