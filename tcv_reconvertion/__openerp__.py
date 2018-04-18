# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2018-04-16
#    Version: 0.0.0.1
#
#    Description:
#
#
##############################################################################
#
# __openerp__.py

{
    "name": "tcv_reconvertion",
    "version": "0",
    "depends": ["base"],
    "author": "Juan Márquez",
    "description":"""
        Tecvemar, c.a.

        This module handles reconvertion process to be executed on 06/04/2018
        """,
    "website": "",
    "category": "Custom",
    "init_xml": [],
    "demo_xml": [],
    "update_xml": [
        'security/security.xml',
        'security/ir.model.access.csv',
        'view/tcv_reconvertion.xml',
        'view/tcv_reconvertion_menus.xml',
        # ~ 'workflow/tcv_reconvertion.xml',
        # ~ 'report/tcv_reconvertion.xml',
        ],
    "active": False,
    "installable": True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
