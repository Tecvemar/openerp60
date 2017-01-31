# -*- encoding: utf-8 -*-
##############################################################################
#    Company:
#    Author: Gabriel
#    Creation Date: 2014-08-05
#    Version: 1.0
#
#    Description:
#
#
##############################################################################
#
# __openerp__.py

{
    "name": "tcv_technical_support_request",
    "version": "1.0",
    "depends": ["base", "knowledge", "hr"],
    "author": "Gabriel",
    "description":"""Manejador de solicitudes de soporte tecnico""",
    "website": "http://launchpad.net/openerp-tecvemar/",
    "category": "Custom",
    "init_xml": [],
    "demo_xml": [],
    "update_xml": ['security/security.xml',
                   'security/ir.model.access.csv',
                   'data/sequence.xml',
                   'view/tcv_technical_support_request_type.xml',
                   'view/tcv_technical_support_request.xml',
                   'workflow/tcv_technical_support_request.xml',
                   'view/tcv_technical_support_request_menus.xml',
                   'report/tcv_technical_support_request.xml',
                   ],
    "active": False,
    "installable": True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
