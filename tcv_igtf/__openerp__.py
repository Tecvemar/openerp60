# -*- encoding: utf-8 -*-
##############################################################################
#    Company:
#    Author: Gabriel
#    Creation Date: 2016-02-23
#    Version: 1.0
#
#    Description:
#
#
##############################################################################
#
# __openerp__.py

{
    "name": "tcv_igtf",
    "version": "",
    "depends": ["base", "account", "tcv_account_voucher", "tcv_bank_deposit"],
    "author": "Gabriel",
    "description":"""

        """,
    "website": "",
    "category": "Custom",
    "init_xml": [],
    "demo_xml": [],
    "update_xml": ['security/security.xml',
                   'security/ir.model.access.csv',
                   'security/ir_rule.xml',
                   'view/tcv_igtf.xml',
                   'view/tcv_igtf_menus.xml',
                   #~ 'workflow/tcv_igtf.xml',
                   #~ 'report/tcv_igtf.xml',
                   ],
    "active": False,
    "installable": True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
