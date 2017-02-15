# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2013-08-26
#    Version: 0.0.0.1
#
#    Description:
#
#
##############################################################################

{
    "name": "",
    "version": "",
    "depends": ["base", "product", "account", "stock", "tcv_stock_driver"],
    "author": "Juan Márquez",
    "description": """
        Tecvemar, c.a.

        Block cost

        This module helps users to calculate block cost:
            block cost = block + transport
        """,
    "website": "",
    "category": "Custom",
    "init_xml": [],
    "demo_xml": [],
    "update_xml": ['security/security.xml',
                   'workflow/workflow.xml',
                   'data/secuence.xml',
                   'security/ir.model.access.csv',
                   'report/tcv_block_cost.xml',
                   'view/tcv_block_cost.xml',
                   'view/tcv_block_file.xml',
                   'view/tcv_block_cost_menu.xml',
                   ],
    "active": False,
    "installable": True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
