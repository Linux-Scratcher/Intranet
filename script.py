from flask import Flask, request, render_template, redirect, url_for, send_from_directory, abort, make_response, session
from werkzeug.security import generate_password_hash, check_password_hash
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = 'votre_cle_secrete_hyper_secure_123!'  # Changez ceci en production !

# Configuration
BASE_DIR = os.path.expanduser("~")
PICTURES_DIR = os.path.expanduser("~/Pictures")

# Utilisateur et mot de passe (à changer en production !)
USER_CREDENTIALS = {
    "Prodadmin": generate_password_hash("Fish123")  # Mot de passe : admin123
}

# Fonction de vérification de sécurité
def is_safe_path(basedir, path):
    return os.path.abspath(path).startswith(os.path.abspath(basedir))

# Décorateur d'authentification
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.context_processor
def inject_os():
    return dict(os=os)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in USER_CREDENTIALS and check_password_hash(USER_CREDENTIALS[username], password):
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('index'))
        return "Identifiants incorrects", 401
    
    return '''
        <form method="post">
            <input type="text" name="username" placeholder="Nom d'utilisateur" required>
            <input type="password" name="password" placeholder="Mot de passe" required>
            <button type="submit">Connexion</button>
        </form>
    '''

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return redirect(url_for('browse', path=''))

@app.route('/browse/', defaults={'path': ''})
@app.route('/browse/<path:path>')
@login_required
def browse(path):
    full_path = os.path.join(BASE_DIR, path)
    
    if not is_safe_path(BASE_DIR, full_path):
        abort(403)
    
    if not os.path.exists(full_path):
        return "Dossier introuvable", 404

    if os.path.isfile(full_path):
        return redirect(url_for('edit_file', path=path))

    try:
        items = os.listdir(full_path)
        dirs = [d for d in items if os.path.isdir(os.path.join(full_path, d)) and not d.startswith('.')]
        files = [f for f in items if os.path.isfile(os.path.join(full_path, f)) and not f.startswith('.')]
        
        return render_template('index.html',
                           dirs=dirs,
                           files=files,
                           current_path=path,
                           username=session.get('username'),
                           parent_dir=os.path.dirname(path))
    except PermissionError:
        abort(403)

@app.route('/edit/<path:path>', methods=['GET', 'POST'])
@login_required
def edit_file(path):
    full_path = os.path.join(BASE_DIR, path)
    
    if not is_safe_path(BASE_DIR, full_path) or not os.path.isfile(full_path):
        abort(404)
    
    if request.method == 'POST':
        try:
            with open(full_path, 'w') as f:
                f.write(request.form['content'])
            return redirect(url_for('browse', path=os.path.dirname(path)))
        except PermissionError:
            abort(403)
    
    try:
        with open(full_path, 'r') as f:
            content = f.read()
        return render_template('edit.html',
                             content=content,
                             path=path,
                             filename=os.path.basename(path))
    except (PermissionError, UnicodeDecodeError):
        abort(403)

@app.route('/create_file', methods=['POST'])
@login_required
def create_file():
    file_path = request.form.get('path')
    if not file_path:
        abort(400)
    
    full_path = os.path.join(BASE_DIR, file_path)
    
    if not is_safe_path(BASE_DIR, full_path):
        abort(403)
    
    try:
        with open(full_path, 'w') as f:
            f.write('')
        return redirect(url_for('browse', path=os.path.dirname(file_path)))
    except PermissionError:
        abort(403)

@app.route('/delete/<path:path>', methods=['POST'])
@login_required
def delete(path):
    full_path = os.path.join(BASE_DIR, path)
    
    if not is_safe_path(BASE_DIR, full_path):
        abort(403)
    
    try:
        if os.path.isfile(full_path):
            os.remove(full_path)
        elif os.path.isdir(full_path):
            os.rmdir(full_path)
        return redirect(url_for('browse', path=os.path.dirname(path)))
    except (PermissionError, OSError):
        abort(403)

@app.route('/images')
@login_required
def images():
    try:
        files = os.listdir(PICTURES_DIR)
        image_files = [f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))]
        return render_template('images.html', image_files=image_files)
    except PermissionError:
        abort(403)

@app.route('/images/<filename>')
@login_required
def serve_image(filename):
    file_path = os.path.join(PICTURES_DIR, filename)
    
    if not is_safe_path(PICTURES_DIR, file_path) or not os.path.isfile(file_path):
        abort(404)
    
    return send_from_directory(PICTURES_DIR, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8084, debug=True)
