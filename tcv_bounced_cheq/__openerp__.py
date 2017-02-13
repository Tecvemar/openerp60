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
    "name" : "Tecvemar - Cheque devuelto",
    "version" : "0.1",
    "depends" : ["base","tcv_base_bank","tcv_bank_deposit"],
    "author" : "Tecvemar - Juan Márquez - Gabriel Gamez",
    "description" : "Bounced cheq",
    "website" : "",
    "category" : "Custom",
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : [
                    'security/ir.model.access.csv',
                    'security/ir_rule.xml',
                    'view/tcv_bounced_cheq_config.xml',
                    'view/tcv_bounced_cheq.xml',
                    'view/tcv_bank_config.xml',
                    'view/tcv_bank_deposit.xml',
                    'view/deposit_line_view.xml',
                    'workflow/tcv_bounced_cheq.xml',
                    'report/tcv_bounced_cheq.xml',
                    'data/sequence.xml',
                    'data/tcv_bounced_cheq_motive.xml',
                    ],
    "active": False,
    "installable": True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
