# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Marquez
#    Creation Date: 07/08/2013
#    Version: 0.0.0.1
#
#    Description:
#
#
##############################################################################
{
    "name" : "Tecvemar - Stock Book",
    "version" : "0.1",
    "depends" : ["base","product","l10n_ve_fiscal_book"],
    "author" : "Tecvemar - Juan Márquez",
    "description" : "Tecvemar - Prueba Libro de Inventario",
    "website" : "",
    "category" : "Custom",
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : [
                    'security/security.xml',
                    'security/ir.model.access.csv',
                    'report/tcv_stock_book_report.xml',
                    'view/tcv_stock_book.xml',
                    'view/tcv_stock_book_menus.xml',
                    'workflow/tcv_stock_book.xml',
                    ],
    "active": False,
    "installable": True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
