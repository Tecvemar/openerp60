# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date: 05/06/2012
#    Version: 0.0.0.0
#
#    Description:
#       This module add a extra model to save the profit's code fields
#
##############################################################################
{
    "name" : "Tecvemar - Campos clave profit",
    "version" : "0.1",
    "author" : "Tecvemar,ca - Juan Márquez",
    "category" : "Custom",
    "depends" : ["base","product"],
    "init_xml" : [],
    "demo_xml" : [],
    "description": "This module add a extra model to save the profit's codes values",
    "update_xml" : [
                    'security/ir.model.access.csv',
                    'security/ir_rule.xml',
                    'view/tcv_profit_codes.xml',
                    ],
    "active": False,
    "installable": True,    
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
