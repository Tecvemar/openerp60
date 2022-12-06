# -*- encoding: utf-8 -*-
##############################################################################
#    Company:
#    Author: Gabriel
#    Creation Date: 2014-07-22
#    Version: 1.0
#
#    Description:
#
#
##############################################################################
#
# __openerp__.py

{
    "name": "tcv_internal_forms",
    "version": "10.0",
    "depends": ["base", "knowledge", "hr"],
    "author": "Gabriel Gamez",
    "description": """Modulo para crear Formularios internos""",
    "website": "http://launchpad.net/openerp-tecvemar/",
    "category": "Custom",
    "init_xml": [],
    "demo_xml": [],
    "update_xml": [
                   'security/security.xml',
                   'security/ir.model.access.csv',
                   'security/ir_rule.xml',
                   'view/tcv_internal_forms_group.xml',
                   'view/tcv_internal_forms_personal.xml',
                   'view/tcv_internal_forms.xml',
                   'view/tcv_internal_forms_menus.xml',
                   ],
    "active": False,
    "installable": True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
