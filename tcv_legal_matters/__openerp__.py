# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2014-02-17
#    Version: 0.0.0.1
#
#    Description:
#
#
##############################################################################

{
    "name": "tcv_legal_matters",
    "version": "",
    "depends": ["base", "account", "l10n_ve_imex"],
    "author": "Juan Márquez",
    "description": """
        Tools to load data related to legal matters
            - Sigesic
        Tecvemar, c.a.
        """,
    "website": "",
    "category": "Custom",
    "init_xml": [],
    "demo_xml": [],
    "update_xml": ['security/security.xml',
                   'view/sigesic/tcv_sigesic_09.xml',
                   'view/sigesic/tcv_sigesic_10.xml',
                   'view/sigesic/tcv_sigesic_11.xml',
                   'view/sigesic/tcv_sigesic_12.xml',
                   'view/sigesic/tcv_sigesic_99.xml',
                   'wizard/sigesic/tcv_sigesic_csv_export.xml',
                   'view/cnp/tcv_cnp.xml',
                   'workflow/tcv_cnp.xml',
                   'view/tcv_legal_matters_menus.xml',
                   'security/ir.model.access.csv',
                   ],
    "active": False,
    "installable": True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
