# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan V. Márquez L.
#    Creation Date: 16/07/2012
#    Version: 0.0.0.0
#
#    Description: This module handle customers & suppliers advances
#
##############################################################################
#~ Amplia la funcionalidad de account management para incorporarle la capacidad de procesar 
#~ vouchers como anticipos en lugar de cxc o cxp
{
    "name" : "Tecvemar - Account.account sync",
    "version" : "0.1",
    "depends" : ["base","account"],
    "author" : "Tecvemar - Juan Márquez",
    "description" : '''Account.account multi-company sync.
    full_sync: full account sync inc. parent & chield
    no_child_sync: full account sync but parent only no chield sync
    no_sync: no account sync (requieres parent sync = no_child_sync)''',
    "website" : "https://blueprints.launchpad.net/openerp-tecvemar/+spec/account-account-multicompany-sync",
    "category" : "Custom",
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : [
                    'security/ir.model.access.csv',
                    'security/ir_rule.xml',
                    'data/tcv_account_sync.xml', 
                    'view/tcv_account_sync.xml', 
                    'view/account.xml', 
                    ],
    "active": False,
    "installable": True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
