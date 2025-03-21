from flask import Flask, request, render_template, redirect, url_for
import os

app = Flask(__name__)
BASE_DIR = os.path.expanduser("~")  # Dossier de départ (change si nécessaire)

@app.route('/')
def index():
    return redirect(url_for('browse', path=''))

@app.route('/browse/', defaults={'path': ''})
@app.route('/browse/<path:path>')
def browse(path):
    full_path = os.path.join(BASE_DIR, path)
    
    if not os.path.exists(full_path):
        return "Dossier introuvable", 404

    # Si c'est un fichier, vérifier s'il commence par un point
    if os.path.isfile(full_path):
        filename = os.path.basename(full_path)
        if filename.startswith('.'):
            return redirect(url_for('browse', path=os.path.dirname(path)))
        return redirect(url_for('edit_file', path=path))

    # Liste les fichiers et dossiers
    files = os.listdir(full_path)
    return render_template('index.html', files=files, path=path)

@app.route('/edit/<path:path>', methods=['GET', 'POST'])
def edit_file(path):
    full_path = os.path.join(BASE_DIR, path)

    # Vérifier si le fichier commence par un .
    filename = os.path.basename(full_path)
    if filename.startswith('.'):
        return redirect(url_for('browse', path=os.path.dirname(path)))

    if request.method == 'POST':
        with open(full_path, 'w') as f:
            f.write(request.form['content'])
        return redirect(url_for('browse', path=os.path.dirname(path)))

    with open(full_path, 'r') as f:
        content = f.read()
    return render_template('edit.html', content=content, path=path)

@app.route('/create', methods=['POST'])
def create_file():
    path = request.form['path']
    full_path = os.path.join(BASE_DIR, path)
    with open(full_path, 'w') as f:
        f.write('')
    return redirect(url_for('browse', path=os.path.dirname(path)))

@app.route('/delete/<path:path>', methods=['POST'])
def delete_file(path):
    full_path = os.path.join(BASE_DIR, path)
    os.remove(full_path)
    return redirect(url_for('browse', path=os.path.dirname(path)))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8084, debug=True)
