# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date: 14/08/2012
#    Version: 0.0.0.0
#
#    Description: This module extend account.voucher with check management system
#
##############################################################################
{
    "name" : "Tecvemar - Check voucher",
    "version" : "0.1",
    "depends" : ["base","account","account_voucher","tcv_base_bank","tcv_account_voucher_extra_wkf"],
    "author" : "Tecvemar - Juan Márquez",
    "description" : '''This module extend account.voucher with check management system''',
    "website" : "https://blueprints.launchpad.net/openerp-tecvemar/+spec/tcv-check-voucher",
    "category" : "Custom",
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : [
                    'security/security.xml',
                    'security/ir.model.access.csv',
                    'data/sequence.xml',
                    'view/tcv_bank_account.xml',
                    'view/tcv_bank_checkbook.xml',
                    'view/tcv_bank_checks.xml',
                    'view/account_voucher.xml',
                    'report/tcv_bank_ch_bounced.xml',
                    'view/tcv_bank_ch_bounced.xml',
                    'view/tcv_check_template.xml',
                    'report/tcv_bank_check.xml',
                    'workflow/tcv_bank_checkbook.xml',
                    'workflow/tcv_bank_checks.xml',
                    'workflow/tcv_bank_ch_bounced.xml',
                    'report/tcv_check_report_wizard.xml',
                    'wizard/tcv_check_report_wizard.xml',
                    'wizard/tcv_txt_check_export_vzla.xml',
                    'security/ir_rule.xml',
                    ],
    "active": False,
    "installable": True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
