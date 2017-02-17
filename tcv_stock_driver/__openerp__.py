##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    "name" : "Stock driver functionallity for area & volume calculation",
    "version" : "0.4",
    "author" : "Tecvemar,ca - Juan Márquez",
    "category" : "Custom",
    "depends" : ["base", "account", "product", "stock", "mrp", "sale","purchase","l10n_ve_fiscal_requirements","tcv_misc"],
    "init_xml" : [],
#    "demo_xml" : ["extra_UOM_demo.xml"],
    "demo_xml" : [],
    "description":
"""
Extends the functionality of the UOM module to incorporate a unique
function for calculating areas and volumes.

    Add in Decimal Precision: Extra UOM data & Stock Precision
    Add in UOM Categories: Area & Volume
    Add in UOM: m2, m3 & ml
    Add new models: (linked to product.product in Special features)
        Layout
        Material
        Finish
        Quality
        Color
        Tile Format
        Thickness
        Pricelist Group
        Country of origin
        Similar products
    All this models have basic data (data/extra_UOM_data.xml)
""",
    "update_xml" : [
                    "security/product_feature_security.xml",
                    "security/ir.model.access.csv",
                    "data/stock_driver_data.xml",
                    "wizard/transaction_intercompany_view.xml",
                    "view/stock_driver_view.xml",
                    "view/account_invoice.xml",
                    #~ "view/purchase_view.xml", moved -> tcv_purchase
                    #~ "view/changes_stock_view.xml",
                    "view/stock_driver_extra_menus.xml",
                    "wizard/stock_move_split_view.xml",
                    "view/stock_view.xml",
                    #~ "workflow/changes_stock_workflow.xml",
                     ],

    "active": False,
    "installable": True
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

