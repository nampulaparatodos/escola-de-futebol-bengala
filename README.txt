# FC BENGALA - Projecto Web Completo

## Estrutura de Ficheiros

bengala/
├── app.py              # Backend Flask (API + servidor)
├── wsgi.py             # Config WSGI para PythonAnywhere  
├── requirements.txt    # Dependencias Python
├── index.html          # Site publico (COLOCA AQUI O TEU INDEX.HTML)
├── logo.png            # Logo (COPIA OS TEUS FICHEIROS DE IMAGEM)
├── Clube.png           # Imagem hero
├── estatuto.pdf        # Estatutos (opcional)
├── bengala.db          # Criado automaticamente ao iniciar
├── templates/
│   └── admin.html      # Painel de administracao
└── static/
    └── uploads/        # Pasta para imagens carregadas via admin

## Instalacao no PythonAnywhere

1. Faz upload de todos os ficheiros para /home/SEUUSER/bengala/
2. Copia todas as tuas imagens para a mesma pasta
3. No terminal do PythonAnywhere:
   cd bengala
   pip install flask werkzeug

4. Configura o WSGI:
   - Va a Web > Add a new web app
   - Escolhe Manual configuration > Python 3.10
   - No ficheiro WSGI, apaga tudo e coloca o conteudo de wsgi.py
   - Muda SEUUSER para o teu nome de utilizador

5. Clica em Reload

## URLs

- Site publico: https://SEUUSER.pythonanywhere.com/
- Painel admin: https://SEUUSER.pythonanywhere.com/admin

## Credenciais padrao

- Utilizador: admin
- Password:   bengala2026

IMPORTANTE: Muda a password apos o primeiro login!
API publica (para o site): /api/public/jogadores, /api/public/noticias, etc.
