# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2014-03-27
#    Version: 0.0.0.1
#
#    Description: ARI
#
#
##############################################################################

{
    "name": "tcv_rrhh_ari",
    "version": "",
    "depends": ["base",
                "hr",
                "l10n_ve_fiscal_requirements",
                "account"
                ],
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
                   'data/secuence.xml',
                   'workflow/tcv_rrhh_ari.xml',
                   'report/tcv_rrhh_ari_forms.xml',
                   'view/tcv_rrhh_ari.xml',
                   'view/hr_view.xml',
                   'view/tcv_rrhh_ari_menus.xml',
                   'wizard/tcv_ari_personal_wiz.xml',
                   ],
    "active": False,
    "installable": True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
