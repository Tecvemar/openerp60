# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date: 25/06/2012
#    Version: 0.0.0.1
#
#    Description:
#       This module manage the tecvemar's sale commision policy
#
##############################################################################
{
    "name" : "Tecvemar - Comisiones por ventas",
    "version" : "1.0",
    "depends" : ["base", "sale", "account"],
    "author" : "Tecvemar - Juan Márquez",
    "description" : "This module manage the tecvemar's sale commision policy.",
    "website" : "",
    "category" : "Custom",
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : [
                    'security/ir.model.access.csv',
                    'security/ir_rule.xml',
                    'view/commission_view.xml',
                    'workflow/sale_commission_wkf.xml',
                    'data/sequences.xml',
                    'report/tcv_sale_commission.xml'
                    ],
    "active": False,
    "installable": True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
