import sqlite3
import os
from dotenv import load_dotenv
from flask import Flask, render_template, redirect, url_for, request

# Carrega a senha escondida do arquivo .env
load_dotenv()

app = Flask(__name__)
DB_NAME = 'metrics.db'

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        
        # Tabela de métricas (cliques e visualizações)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY,
                views INTEGER DEFAULT 0,
                clicks INTEGER DEFAULT 0
            )
        ''')
        cursor.execute('''
            INSERT OR IGNORE INTO metrics (id, views, clicks) 
            VALUES (1, 0, 0)
        ''')
        
        # Tabela para salvar APENAS os nomes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS captured_names (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL
            )
        ''')
        conn.commit()

def increment_metric(field):
    if field not in ['views', 'clicks']:
        return
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(f'UPDATE metrics SET {field} = {field} + 1 WHERE id = 1')
        conn.commit()

def get_metrics():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT views, clicks FROM metrics WHERE id = 1')
        row = cursor.fetchone()
        return row if row else (0, 0)

# --- ROTAS DO SISTEMA ---

@app.route('/')
def index():
    increment_metric('views')
    return render_template('index.html')

@app.route('/form')
def form_page():
    return render_template('form.html')

@app.route('/submit', methods=['POST'])
def submit():
    nome = request.form.get('nome')
    
    # Ignora CPF e Telefone. Salva apenas o nome no banco de dados.
    if nome:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO captured_names (nome) VALUES (?)', (nome,))
            conn.commit()
            
    # Contabiliza +1 clique (envio de formulário)
    increment_metric('clicks')
    
    return redirect(url_for('awareness'))

@app.route('/reset')
def reset_metrics():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE metrics SET views = 0, clicks = 0 WHERE id = 1')
        cursor.execute('DELETE FROM captured_names')
        conn.commit()
    # Redireciona de volta para os stats usando a senha atual
    senha_verdadeira = os.getenv('SENHA_ADMIN')
    return redirect(url_for('stats', key=senha_verdadeira))

@app.route('/awareness')
def awareness():
    return render_template('awareness.html')

@app.route('/stats')
def stats():
    # Puxa a senha da URL e a senha do arquivo .env
    senha_digitada = request.args.get('key')
    senha_verdadeira = os.getenv('SENHA_ADMIN')
    
    # Bloqueia o acesso se a senha estiver errada
    if senha_digitada != senha_verdadeira:
        return "ACESSO NEGADO: Apenas o administrador pode ver esta página. Insira a chave correta na URL.", 403

    views, clicks = get_metrics()
    conversion_rate = (clicks / views * 100) if views > 0 else 0.0
    
    return render_template(
        'stats.html', 
        views=views, 
        clicks=clicks, 
        conversion_rate=conversion_rate
    )

if __name__ == '__main__':
    init_db()
    senha_verdadeira = os.getenv('SENHA_ADMIN')
    print("Servidor iniciado com sucesso!")
    print("Acesse a simulação em: http://127.0.0.1:5000")
    print(f"Acesse as estatísticas em: http://127.0.0.1:5000/stats?key={senha_verdadeira}")
    app.run(debug=True, port=5000)