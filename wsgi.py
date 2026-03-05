# WSGI config para PythonAnywhere
# Cole este conteudo no ficheiro WSGI da sua conta PythonAnywhere
# Caminho tipico: /var/www/SEUUSER_pythonanywhere_com_wsgi.py

import sys
import os

# MUDE ESTE CAMINHO para o caminho real do seu projeto no PythonAnywhere
project_home = '/home/SEUUSER/bengala'

if project_home not in sys.path:
    sys.path.insert(0, project_home)

os.chdir(project_home)

from app import app as application
