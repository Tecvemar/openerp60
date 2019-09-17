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
    "name": "tcv_consignment",
    "version": "0",
    "depends": ["base", "stock", "tcv_sale"],
    "author": "Juan Márquez",
    "description":"""
        This module hanlde all procces related to consignment.

        Tecvemar, c.a.
        """,
    "website": "www.tecvemar.com",
    "category": "Custom",
    "init_xml": [],
    "demo_xml": [],
    "update_xml": [
        'data/sequence.xml',
        'data/consignament_data.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'report/tcv_consignment.xml',
        'view/tcv_consignment.xml',
        'view/tcv_consig_invoice.xml',
        'view/tcv_consignment_config.xml',
        'view/tcv_consignment_menus.xml',
        'workflow/tcv_consignment.xml',
        'workflow/tcv_consig_invoice.xml',
        # ~ 'wizard/sale_lot_list.xml',
        ],
    "active": False,
    "installable": True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
