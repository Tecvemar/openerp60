# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2015-09-25
#    Version: 0.0.0.1
#
#    Description:
#
#
##############################################################################
#
# __openerp__.py

{
    "name": "tcv_mrp_planning",
    "version": "",
    "depends": ["base", "tcv_mrp", "tcv_stock", "tcv_bundle"],
    "author": "Juan Márquez",
    "description": """
        Tecvemar, c.a.
        """,
    "website": "",
    "category": "Custom",
    "init_xml": [],
    "demo_xml": [],
    "update_xml": ['security/security.xml',
                   'security/ir.model.access.csv',
                   'view/tcv_mrp_planning_config.xml',
                   'view/tcv_mrp_planning_menus.xml',
                   'report/tcv_mrp_planning.xml',
                   ],
    "active": False,
    "installable": True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
