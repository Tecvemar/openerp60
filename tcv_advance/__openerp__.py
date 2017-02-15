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
    "name" : "Tecvemar - Anticipos de clientes y proveedores",
    "version" : "0.1",
    "depends" : ["base","base_vat","account","tcv_account_management","account_voucher","account_smart_unreconcile"],
    "author" : "Tecvemar - Juan Márquez",
    "description" : "customers & suppliers advances",
    "website" : "",
    "category" : "Custom",
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : [
                    'security/ir.model.access.csv',
                    'security/ir_rule.xml',
                    #~ 'view/account_partner.xml',  ## moved -> tcv_account_management
                    #~ 'view/partner.xml',  ## moved -> tcv_account_management
                    'view/account_voucher.xml',
                    'view/voucher_advance.xml',
                    'view/voucher_advance_customer.xml',
                    'view/voucher_advance_supplier.xml',
                    'workflow/voucher_advance.xml',
                    'data/sequence.xml',
                    'report/tcv_voucher_advance.xml',
                    ],
    "active": False,
    "installable": True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
