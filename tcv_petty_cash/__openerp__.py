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
    "name" : "Tecvemar - Caja Chica",
    "version" : "0.1",
    "depends" : ["base", "account", "tcv_base_bank"],
    "author" : "Tecvemar - Gabriel Gamez - Juan Márquez",
    "description" : "Petty cash management",
    "website" : "",
    "category" : "Custom",
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : [
                    'security/ir.model.access.csv',
                    'security/ir_rule.xml',
                    'report/tcv_petty_cash_expense.xml',
                    'report/tcv_petty_cash_refund.xml',
                    'view/tcv_petty_cash_config.xml',
                    'wizard/tcv_petty_cash_multi_view.xml',
                    'view/tcv_petty_cash_refund.xml',
                    'view/tcv_petty_cash_expense.xml',
                    'workflow/tcv_petty_cash.xml',
                    'workflow/tcv_petty_cash_expense.xml',
                    'view/tcv_petty_cash_menus.xml',
                    'data/sequence.xml',
                    ],
    "active": False,
    "installable": True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
