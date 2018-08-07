#!/bin/bash
# Created by: Israel Fermin Montilla <israel@openerp.com.ve>
# Vauxoo Team
#HOW TO USE:

#Just invoke it with the route to the module directory (including the module directory)
#and it will create the needed directories if they don't exists and all the
#basic structure of a module with its empty files to be written.

#To execute it properly, you must give it execution privilege to the script.
echo "Moving to $1"
mkdir -p $1
cd $1
pwd
echo "Creating Module Structure"
mkdir data
mkdir demo
mkdir i18n
mkdir report
mkdir security
mkdir wizard
mkdir view
mkdir model
mkdir workflow
#~ mkdir wiki
echo "Creating Module __init__.py and __openerp__.py"
touch __init__.py
echo import model > __init__.py
echo import wizard >> __init__.py
echo import report >> __init__.py
touch __openerp__.py
cd model
touch __init__.py
cd ../wizard
touch __init__.py
cd ../report
touch __init__.py
echo "Done."
