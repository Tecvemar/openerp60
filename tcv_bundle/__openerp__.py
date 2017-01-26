# -*- encoding: utf-8 -*-
##############################################################################
#    Company:
#    Author: Gabriel
#    Creation Date: 2015-09-15
#    Version: 1.0
#
#    Description:
#
#
##############################################################################
#
# __openerp__.py

{
    "name": "tcv_bundle",
    "version": "",
    "depends": ["base", "stock", "tcv_stock_driver"],
    "author": "Gabriel",
    "description":"""

        """,
    "website": "",
    "category": "Custom",
    "init_xml": [],
    "demo_xml": [],
    "update_xml": [
                   'security/security.xml',
                   'security/ir.model.access.csv',
                   'report/tcv_bundle_report.xml',
                   'report/tcv_bundle_list.xml',
                   'view/tcv_bundle.xml',
                   'view/tcv_bundle_menus.xml',
                   'data/sequence.xml',
                   #~ 'workflow/tcv_bundle.xml',
                   ],
    "active": False,
    "installable": True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
