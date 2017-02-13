# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2014-02-04
#    Version: 0.0.0.1
#
#    Description: This modole add generic expense payment to account
#    voucher module.
#    Must be joined with tcv_advance, tcv_account_check &
#    tcv_account_voucer_extra_wkf
#
#
##############################################################################

{
    "name": "tcv_account_voucher",
    "version": "0.1",
    "depends": [
        "base", "account", "account_voucher", "tcv_check_voucher",
        "tcv_account_voucher_extra_wkf", "tcv_advance"],
    "author": "Juan Márquez",
    "description": """
        General income egress voucher
        """,
    "website": "",
    "category": "Custom",
    "init_xml": [],
    "demo_xml": [],
    "update_xml": [
        'view/account_voucher.xml',
        #~ 'report/tcv_account_voucher.xml',
        ],
    "active": False,
    "installable": True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
