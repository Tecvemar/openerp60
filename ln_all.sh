echo 'Generando la carpeta modulos y agregar todos los enlaces simbólicos'

cd /home/jmarquez/instancias/produccion/modulos/

echo 'tcv_municipal_tax'
ln -s -f /home/jmarquez/github/openerp60/tcv_municipal_tax/ .
echo 'tcv_stock'
ln -s -f /home/jmarquez/github/openerp60/tcv_stock/ .
echo 'tcv_mrp'
ln -s -f /home/jmarquez/github/openerp60/tcv_mrp/ .


cd /home/jmarquez/github/openerp60/
