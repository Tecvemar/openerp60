# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2014-04-24
#    Version: 0.0.0.1
#
#    Description: tcv sale & purchase books
#
#
##############################################################################

{
    "name": "",
    "version": "",
    "depends": ["base", "l10n_ve_fiscal_book"],
    "author": "Juan Márquez",
    "description":"""
        Tecvemar, c.a.
        """,
    "website": "",
    "category": "Custom",
    "init_xml": [],
    "demo_xml": [],
    "update_xml": ['report/fiscal_book_report.xml',
                   'report/list_wh_iva.xml',
                   'report/list_wh_islr_report.xml',
                   ],
    "active": False,
    "installable": True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
