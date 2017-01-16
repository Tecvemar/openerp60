# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Márquez
#    Creation Date: 2014-01-30
#    Version: 0.0.0.1
#
#    Description: Some enhancements for account module (Reports)
#
#
##############################################################################

{
    "name": "tcv_account",
    "version": "0.1",
    "depends": ["base", "account", "tcv_monthly_report"],
    "author": "Juan Márquez",
    "description": """
        Some enhancements for account module
        """,
    "website": "",
    "category": "Custom",
    "init_xml": [],
    "demo_xml": [],
    "update_xml": [
        'security/security.xml',
        'report/account_move.xml',
        'report/tcv_liquidity_report_wizard.xml',
        'wizard/tcv_liquidity_report_wizard.xml',
        'wizard/tcv_fix_account_move_period.xml',
        'report/tcv_trial_balance.xml',
        'wizard/tcv_trial_balance.xml',
        'report/tcv_partner_balance.xml',
        'wizard/tcv_partner_balance.xml',
        'wizard/tcv_acc_change.xml',
        'view/account_view.xml',
        'view/tcv_account_menus.xml',
        'report/tcv_balance.xml',
        'report/tcv_legal_diary.xml',
        'report/tcv_account_anual_report.xml',
        'report/tcv_invoice_report.xml',
        'wizard/tcv_split_reconcile.xml',
        ],
    "active": False,
    "installable": True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
