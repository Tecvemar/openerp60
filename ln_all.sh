echo 'Generando la carpeta modulos y agregar todos los enlaces simbólicos'

cd /home/jmarquez/instancias/produccion/modulos/

echo 'tcv_municipal_tax'
ln -s -f /home/jmarquez/github/openerp60/tcv_municipal_tax/ .


cd /home/jmarquez/github/openerp60/
