echo 'Generando la carpeta modulos y agregar todos los enlaces simbólicos'

cd ~/instancias/produccion/modulos/

echo 'tcv_municipal_tax'
ln -s -f ~/github/openerp60/tcv_municipal_tax/ .
echo 'tcv_stock'
ln -s -f ~/github/openerp60/tcv_stock/ .
echo 'tcv_mrp'
ln -s -f ~/github/openerp60/tcv_mrp/ .
echo 'tcv_account'
ln -s -f ~/github/openerp60/tcv_account/ .
echo 'tcv_rrhh_ari'
ln -s -f ~/github/openerp60/tcv_rrhh_ari/ .


cd ~/github/openerp60/