# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Gabriel Gamez
#    Creation Date: 07/06/2012
#    Version: 0.0.0.1
#
#    Description:
#
#
##############################################################################
{
    "name" : "Tecvemar - Depositos Bancarios",
    "version" : "0.1",
    "depends" : ["base", "account", "tcv_base_bank"],
    "author" : "Tecvemar - Juan Márquez / Gabriel Gamez",
    "description" : "Bang deposit's management",
    "website" : "",
    "category" : "Custom",
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : [
                    'security/security.xml',
                    'security/ir.model.access.csv',
                    'security/ir_rule.xml',
                    'view/tcv_bank_config.xml',
                    'wizard/tcv_bank_deposit_multi_view.xml',
                    'view/tcv_bank_deposit.xml',
                    'view/tcv_bank_moves.xml',
                    'view/tcv_bank_deposit_menus.xml',
                    'workflow/tcv_bank_deposit.xml',
                    'workflow/tcv_bank_moves.xml',
                    'report/tcv_bank_deposit.xml',
                    'report/tcv_bank_moves.xml',
                    'data/sequence.xml',
                    ],
    "active": False,
    "installable": True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
