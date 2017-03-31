# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Marquez
#    Creation Date: 03/11/2014
#    Version: 0.0.0.1
#
#    Description: Base wizard for montly reports
#
#
##############################################################################
{
    "name" : "Tecvemar - Monthly report base",
    "version" : "0.1",
    "depends" : ["base"],
    "author" : "Tecvemar - Juan Márquez",
    "description" : "Base wizard for montly & top ten reports",
    "website" : "",
    "category" : "Custom",
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : [
        'wizard/tcv_monthly_report.xml',
        'wizard/tcv_top_ten_report.xml',
        ],
    "active": False,
    "installable": True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
