# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2018-10-16
#    Version: 0.0.0.1
#
#    Description:
#
#
##############################################################################
#
# __openerp__.py

{
    "name": "tcv_consignement",
    "version": "0",
    "depends": ["base", "stock", "tcv_sale"],
    "author": "David Bernal",
    "description":"""
        This module hanlde all procces related to consignement.

        Tecvemar, c.a.
        """,
    "website": "www.tecvemar.com",
    "category": "Custom",
    "init_xml": [],
    "demo_xml": [],
    "update_xml": [
        'data/sequence.xml',
        #~ 'data/consignement_data.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'report/tcv_consignement.xml',
        'view/tcv_consignement.xml',
        'view/tcv_consignement_invoice.xml',
        'view/tcv_consignement_config.xml',
        'view/tcv_consignement_menus.xml',
        'workflow/tcv_consignement.xml',
        'workflow/tcv_consignement_invoice.xml',
        #~ 'wizard/sale_lot_list.xml',
        #~ 'wizard/tcv_consignement_lot_list.xml',
        ],
    "active": False,
    "installable": True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
