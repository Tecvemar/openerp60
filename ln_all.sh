echo 'Generando la carpeta modulos y agregar todos los enlaces simbólicos'



cd ~/instancias/produccion

rm modulos -r
mkdir modulos
cd modulos

ln -s ../addons/* .
ln -s -f ~/github/l10n_ve/* . -f
ln -s -f ~/github/extra_addons/* . -f

echo 'intercompany_tcv'
ln -s -f ~/github/openerp60/intercompany_tcv/ .
echo 'tcv_account'
ln -s -f ~/github/openerp60/tcv_account/ .
echo 'tcv_account_management'
ln -s -f ~/github/openerp60/tcv_account_management/ .
echo 'tcv_account_sync'
ln -s -f ~/github/openerp60/tcv_account_sync/ .
echo 'tcv_account_voucher'
ln -s -f ~/github/openerp60/tcv_account_voucher/ .
echo 'tcv_account_voucher_extra_wkf'
ln -s -f ~/github/openerp60/tcv_account_voucher_extra_wkf/ .
echo 'tcv_advance'
ln -s -f ~/github/openerp60/tcv_advance/ .
echo 'tcv_bank_deposit'
ln -s -f ~/github/openerp60/tcv_bank_deposit/ .
echo 'tcv_base_bank'
ln -s -f ~/github/openerp60/tcv_base_bank/ .
echo 'tcv_block_cost'
ln -s -f ~/github/openerp60/tcv_block_cost/ .
echo 'tcv_bounced_cheq'
ln -s -f ~/github/openerp60/tcv_bounced_cheq/ .
echo 'tcv_bundle'
ln -s -f ~/github/openerp60/tcv_bundle/ .
echo 'tcv_calculator'
ln -s -f ~/github/openerp60/tcv_calculator/ .
echo 'tcv_check_voucher'
ln -s -f ~/github/openerp60/tcv_check_voucher/ .
echo 'tcv_cost_imp'
ln -s -f ~/github/openerp60/tcv_cost_imp/ .
echo 'tcv_ctrl_mrp'
ln -s -f ~/github/openerp60/tcv_ctrl_mrp/ .
echo 'tcv_fiscal_report'
ln -s -f ~/github/openerp60/tcv_fiscal_report/ .
echo 'tcv_hr'
ln -s -f ~/github/openerp60/tcv_hr/ .
echo 'tcv_igtf'
ln -s -f ~/github/openerp60/tcv_igtf/ .
echo 'tcv_import_management'
ln -s -f ~/github/openerp60/tcv_import_management/ .
echo 'tcv_label_request'
ln -s -f ~/github/openerp60/tcv_label_request/ .
echo 'tcv_legal_matters'
ln -s -f ~/github/openerp60/tcv_legal_matters/ .
echo 'tcv_misc'
ln -s -f ~/github/openerp60/tcv_misc/ .
echo 'tcv_monthly_report'
ln -s -f ~/github/openerp60/tcv_monthly_report/ .
echo 'tcv_mrp'
ln -s -f ~/github/openerp60/tcv_mrp/ .
echo 'tcv_mrp_planning'
ln -s -f ~/github/openerp60/tcv_mrp_planning/ .
echo 'tcv_municipal_tax'
ln -s -f ~/github/openerp60/tcv_municipal_tax/ .
echo 'tcv_payroll_import'
ln -s -f ~/github/openerp60/tcv_payroll_import/ .
echo 'tcv_petty_cash'
ln -s -f ~/github/openerp60/tcv_petty_cash/ .
echo 'tcv_profit_codes'
ln -s -f ~/github/openerp60/tcv_profit_codes/ .
echo 'tcv_profit_import'
ln -s -f ~/github/openerp60/tcv_profit_import/ .
echo 'tcv_purchase'
ln -s -f ~/github/openerp60/tcv_purchase/ .
echo 'tcv_report'
ln -s -f ~/github/openerp60/tcv_report/ .
echo 'tcv_rrhh_ari'
ln -s -f ~/github/openerp60/tcv_rrhh_ari/ .
echo 'tcv_rse'
ln -s -f ~/github/openerp60/tcv_rse/ .
echo 'tcv_sale'
ln -s -f ~/github/openerp60/tcv_sale/ .
echo 'tcv_sale_commission'
ln -s -f ~/github/openerp60/tcv_sale_commission/ .
echo 'tcv_stock'
ln -s -f ~/github/openerp60/tcv_stock/ .
echo 'tcv_stock_driver'
ln -s -f ~/github/openerp60/tcv_stock_driver/ .
echo 'tcv_stock_book'
ln -s -f ~/github/openerp60/tcv_stock_book/ .
echo 'tcv_technical_support_request'
ln -s -f ~/github/openerp60/tcv_technical_support_request/ .
echo 'tcv_reconvertion'
ln -s -f ~/github/openerp60/tcv_reconvertion/ .
echo 'tcv_consignment'
ln -s -f ~/github/openerp60/tcv_consignement/ .

cd ~/github/openerp60/
