# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Gabriel Gamez
#    Creation Date: 27/09/2012
#    Version: 0.0.0.1
#
#    Description: Creacion y solicitud de impresion de etiquetas
#
##############################################################################
{
    "name" : "Tecvemar - Label Request",
    "version" : "0.1",
    "depends" : ["base","account","stock","tcv_mrp"],
    "author" : "Tecvemar - Gabriel Gamez",
    "description" : '''Modulo para solicitar las etiquetas.''',
    "website" : "",
    "category" : "Custom",
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : [
                    'security/security.xml',
                    'view/tcv_label_request.xml',
                    'view/tcv_mrp_gangsaw.xml',
                    'view/tcv_mrp_config.xml',
                    'security/ir.model.access.csv',
                    'workflow/tcv_label_request.xml',
                    'data/sequence.xml',
                    'wizard/tcv_label_request_print_prn_export.xml',
                    ],
    "active": False,
    "installable": True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
