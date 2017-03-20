# -*- encoding: utf-8 -*-
##############################################################################
#    Company: Tecvemar, c.a.
#    Author: Juan Marquez
#    Creation Date: 13/09/2012
#    Version: 0.0.0.1
#
#    Description:
#
#
##############################################################################
{
    "name": "Tecvemar - mrp",
    "version": "0.1",
    "depends": ["base", "account", "mrp", "tcv_stock_driver", "product",
                "stock", "tcv_monthly_report"],
    "author": "Tecvemar - Juan Márquez",
    "description": "Tecvemar mrp",
    "website": "",
    "category": "Custom",
    "init_xml": [],
    "demo_xml": [],
    "update_xml": [
        'security/security.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'workflow/tcv_mrp_gangsaw_order.xml',
        'workflow/tcv_mrp_production_supplies.xml',
        'wizard/tcv_mrp_finished_slab_output_wizard.xml',
        'wizard/tcv_mrp_finished_slab_output_change_location.xml',
        'wizard/tcv_mrp_finished_product_txt_export.xml',
        'wizard/tcv_mrp_gangsaw_summary_wizard.xml',
        'report/tcv_mrp_supplies_by_product.xml',
        'wizard/tcv_mrp_supplies_by_product_wizard.xml',
        'report/tcv_mrp_blade_yield.xml',
        'wizard/tcv_mrp_blade_yield_wizard.xml',
        'view/tcv_mrp_template.xml',
        'view/tcv_mrp_config.xml',
        'view/tcv_mrp_stops_issues.xml',
        'view/tcv_mrp_process.xml',
        'view/tcv_mrp_subprocess.xml',
        'view/tcv_mrp_basic_task.xml',
        'view/tcv_mrp_gangsaw.xml',
        'view/tcv_mrp_polish.xml',
        'view/tcv_mrp_abrasive_durability.xml',
        'view/tcv_mrp_resin.xml',
        'view/tcv_mrp_io_slab.xml',
        'view/tcv_mrp_finished_slab.xml',
        'view/tcv_mrp_waste_slab.xml',
        'view/tcv_mrp_gangsaw_order.xml',
        'view/tcv_mrp_gangsaw_params.xml',
        'view/tcv_mrp_output_result.xml',
        'view/tcv_mrp_production_supplies.xml',
        'report/tcv_mrp_anual_report.xml',
        'report/tcv_mrp_in_process.xml',
        'report/tcv_mrp_gangsaw_order.xml',
        'wizard/tcv_mrp_in_process.xml',
        'report/tcv_production_rates.xml',
        'view/tcv_mrp_menus.xml',
        'view/tcv_mrp_reports.xml',
        'report/tcv_mrp_gangsaw_summary.xml',
        'report/tcv_mrp_abrasive_durability.xml',
        'report/tcv_mrp_days_lapses.xml',
        'report/tcv_mrp_gangsaw_by_hardness.xml',
        'report/tcv_mrp_gangsaw_control_form.xml',
        'data/sequence.xml',
        'data/decimal_precision.xml',
        ],
    "active": False,
    "installable": True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
