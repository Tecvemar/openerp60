# -*- encoding: utf-8 -*-
##############################################################################
#    Company:
#    Author: Gabriel
#    Creation Date: 2016-01-25
#    Version: 1.0
#
#    Description:
#
#
##############################################################################
#
# __openerp__.py

{
    "name": "tcv_rse",
    "version": "",
    "depends": ["base", "account", "account_voucher", "tcv_legal_matters"],
    "author": "Gabriel",
    "description":"""Modulo de manejo de solicitudes de RSE""",
    "website": "",
    "category": "Custom",
    "init_xml": [],
    "demo_xml": [],
    "update_xml": ['security/security.xml',
                   'security/ir.model.access.csv',
                   'data/sequence.xml',
                   'view/tcv_rse.xml',
                   'view/tcv_rse_menus.xml',
                   'workflow/tcv_rse.xml',
                   'report/tcv_rse_request.xml',
                   'report/tcv_rse.xml',
                   ],
    "active": False,
    "installable": True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
