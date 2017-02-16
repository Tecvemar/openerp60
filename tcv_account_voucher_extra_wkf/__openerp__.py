# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date: 22/08/2012
#    Version: 0.0.0.0
#
#    Description: Expand account_voucher workflow to enable all transition
#                 validations
#
##############################################################################
{
    "name" : "Tecvemar - account_voucher workflow extension",
    "version" : "0.1",
    "depends" : ["base","account_voucher"],
    "author" : "Tecvemar - Juan Márquez",
    "description" : '''Expand account_voucher workflow to enable all transition validations''',
    "website" : "https://code.launchpad.net/~jmarquez/openerp-tecvemar/tcv_account_voucher_extra_wkf",
    "category" : "Custom",
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : [
                    'workflow/account_voucher_workflow.xml', 
                    ],
    "active": False,
    "installable": True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
