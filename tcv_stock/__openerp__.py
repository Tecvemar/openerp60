# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2013-09-27
#    Version: 0.0.0.1
#
#    Description:
#
#
##############################################################################

{
    "name": "tcv_stock",
    "version": "0.1",
    "depends": ["base", "stock", "tcv_sale"],
    "author": "Juan Márquez",
    "description": """
        This module concentrates all customizations to the module "stock" at
        the request of Tecvemar.

        Tecvemar, c.a.
        """,
    "website": "",
    "category": "Custom",
    "init_xml": [],
    "demo_xml": [],
    "update_xml": ['security/security.xml',
                   'security/ir.model.access.csv',
                   'data/secuence.xml',
                   'view/driver_vehicle.xml',
                   'view/stock_view.xml',
                   'view/tcv_stock_changes_method.xml',
                   'view/tcv_stock_changes.xml',
                   'workflow/tcv_stock_changes.xml',
                   'report/stock_report.xml',
                   'report/tcv_stock_changes.xml',
                   'report/tcv_stock_by_location_report.xml',
                   'report/tcv_dispatch_lots.xml',
                   #~ 'report/tcv_valid_block_cost.xml',
                   'view/stock_menus.xml',
                   'wizard/lot_range_int_move.xml',
                   'wizard/tcv_internal_move_wiz.xml',
                   'wizard/tcv_split_stock_picking.xml',
                   'wizard/tcv_fix_stock_move.xml',
                   'wizard/tcv_fix_stock_move.xml',
                   'wizard/tcv_txt_lookup_export.xml',
                   'wizard/stock_return_picking_view.xml',
                   'wizard/tcv_get_bundle_tracking.xml',
                   #~ 'wizard/tcv_tracking_tool.xml',
                   ],
    "active": False,
    "installable": True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
