import sqlite3
from flask import Flask, render_template, redirect, url_for

# Configuração da aplicação Flask
# Por padrão, o Flask busca os arquivos HTML dentro da pasta 'templates' 
# e os arquivos CSS/Imagens na pasta 'static'.
app = Flask(__name__)

DB_NAME = 'metrics.db'

def init_db():
    """Cria a tabela de métricas no banco SQLite caso ela ainda não exista."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY,
                views INTEGER DEFAULT 0,
                clicks INTEGER DEFAULT 0
            )
        ''')
        # Garante que o registro inicial com ID 1 exista
        cursor.execute('''
            INSERT OR IGNORE INTO metrics (id, views, clicks) 
            VALUES (1, 0, 0)
        ''')
        conn.commit()

def increment_metric(field):
    """Incrementa em +1 o campo informado ('views' ou 'clicks') sem salvar nenhum PII (dado pessoal)."""
    if field not in ['views', 'clicks']:
        return
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(f'UPDATE metrics SET {field} = {field} + 1 WHERE id = 1')
        conn.commit()

def get_metrics():
    """Retorna os totais de acessos e cliques registrados."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT views, clicks FROM metrics WHERE id = 1')
        row = cursor.fetchone()
        return row if row else (0, 0)

# --- ROTAS DO SISTEMA ---

@app.route('/')
def index():
    """
    Rota principal da simulação.
    A cada acesso, contabiliza +1 na métrica 'views' e exibe o formulário (index.html).
    """
    increment_metric('views')
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    """
    Rota acionada ao enviar o formulário.
    IMPORTANTE CONFORMIDADE LGPD:
    Não acessamos 'request.form' nem guardamos IPs/dados.
    Apenas contabilizamos +1 na métrica 'clicks' e redirecionamos.
    """
    increment_metric('clicks')
    return redirect(url_for('awareness'))

@app.route('/awareness')
def awareness():
    """Exibe a página educativa informando sobre a simulação de phishing (awareness.html)."""
    return render_template('awareness.html')

@app.route('/stats')
def stats():
    """Exibe o painel com o resultado consolidado e porcentagem de vulnerabilidade (stats.html)."""
    views, clicks = get_metrics()
    
    # Cálculo da taxa de vulnerabilidade (evita divisão por zero)
    conversion_rate = (clicks / views * 100) if views > 0 else 0.0
    
    return render_template(
        'stats.html', 
        views=views, 
        clicks=clicks, 
        conversion_rate=conversion_rate
    )

if __name__ == '__main__':
    # Inicializa o banco de dados antes de subir o servidor
    init_db()
    
    print("Servidor iniciado com sucesso!")
    print("Acesse a simulação em: http://127.0.0.1:5000")
    print("Acesse as estatísticas em: http://127.0.0.1:5000/stats")
    
    app.run(debug=True, port=5000)