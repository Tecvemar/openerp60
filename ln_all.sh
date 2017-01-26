echo 'Generando la carpeta modulos y agregar todos los enlaces simbólicos'

cd ~/instancias/produccion/modulos/

echo 'tcv_account'
ln -s -f ~/github/openerp60/tcv_account/ .
echo 'tcv_bank_deposit'
ln -s -f ~/github/openerp60/tcv_bank_deposit/ .
echo 'tcv_bundle'
ln -s -f ~/github/openerp60/tcv_bundle/ .
echo 'tcv_import_management'
ln -s -f ~/github/openerp60/tcv_import_management/ .
echo 'tcv_label_request'
ln -s -f ~/github/openerp60/tcv_label_request/ .
echo 'tcv_monthly_report'
ln -s -f ~/github/openerp60/tcv_monthly_report/ .
echo 'tcv_mrp'
ln -s -f ~/github/openerp60/tcv_mrp/ .
echo 'tcv_municipal_tax'
ln -s -f ~/github/openerp60/tcv_municipal_tax/ .
echo 'tcv_payroll_import'
ln -s -f ~/github/openerp60/tcv_payroll_import/ .
echo 'tcv_profit_import'
ln -s -f ~/github/openerp60/tcv_profit_import/ .
echo 'tcv_rrhh_ari'
ln -s -f ~/github/openerp60/tcv_rrhh_ari/ .
echo 'tcv_rse'
ln -s -f ~/github/openerp60/tcv_rse/ .
echo 'tcv_sale'
ln -s -f ~/github/openerp60/tcv_sale/ .
echo 'tcv_stock'
ln -s -f ~/github/openerp60/tcv_stock/ .
echo 'tcv_stock_book'
ln -s -f ~/github/openerp60/tcv_stock_book/ .

cd ~/github/openerp60/
