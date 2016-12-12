# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2015-10-13
#    Version: 0.0.0.1
#
#    Description:
#
#
##############################################################################
#
# __openerp__.py

{
    "name": "tcv_municipal_tax",
    "version": "",
    "depends": ["base", "account", "l10n_ve_fiscal_book",
                "l10n_ve_withholding"],
    "author": "Juan Márquez",
    "description":"""
        Tecvemar, c.a.
        """,
    "website": "",
    "category": "Custom",
    "init_xml": [],
    "demo_xml": [],
    "update_xml": ['security/security.xml',
                   'security/ir.model.access.csv',
                   'security/ir_rule.xml',
                   'report/tcv_municipal_tax.xml',
                   'view/tcv_municipal_taxes.xml',
                   'view/product.xml',
                   'workflow/tcv_municipal_tax.xml',
                   'workflow/tcv_municipal_tax_wh.xml',
                   'report/tcv_municipal_tax_products.xml',
                   'report/tcv_municipal_tax_invoice.xml',
                   'report/tcv_municipal_tax_wh.xml',
                   'view/tcv_municipal_tax_wh.xml',
                   'view/tcv_municipal_tax_menus.xml',
                   'view/partner_view.xml',
                   'data/sequence.xml',
                   ],
    "active": False,
    "installable": True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
