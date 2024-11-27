from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = '123'

# Configuração do MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'estoque'

mysql = MySQL(app)
bcrypt = Bcrypt(app)

db = SQLAlchemy()

# Definição da classe Produto
class Produto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.String(200), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    preco = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"<Produto {self.nome}>"

# Tela de Login
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        # Validação de campos vazios
        if not email or not senha:
            flash('E-mail e senha são obrigatórios!', 'danger')
            return render_template('login.html')

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM usuarios WHERE email = %s", [email])
        user = cur.fetchone()
        cur.close()

        if user and bcrypt.check_password_hash(user[3], senha):  # user[3] é a senha
            session['user_id'] = user[0]
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('estoque'))
        else:
            flash('E-mail ou senha inválidos!', 'danger')

    return render_template('login.html')

# Tela de Cadastro de Usuário
@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = bcrypt.generate_password_hash(request.form['senha']).decode('utf-8')
        cpf = request.form['cpf']
        telefone = request.form['telefone']

        # Verificação de campos obrigatórios
        if not nome or not email or not senha or not cpf or not telefone:
            flash('Todos os campos são obrigatórios!', 'danger')
            return render_template('cadastro.html')

        # Inserir no banco de dados
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO usuarios (nome, email, senha, cpf, telefone) VALUES (%s, %s, %s, %s, %s)",
                    (nome, email, senha, cpf, telefone))
        mysql.connection.commit()
        cur.close()

        flash('Usuário cadastrado com sucesso!', 'success')
        return redirect(url_for('login'))

    return render_template('cadastro.html')

# Rota para alteração de senha
@app.route('/alterar_senha', methods=['GET', 'POST'])
def alterar_senha():
    if request.method == 'POST':
        usuario_id = session['user_id']
        nova_senha = bcrypt.generate_password_hash(request.form['nova_senha']).decode('utf-8')

        # Atualizar a senha no banco
        cur = mysql.connection.cursor()
        cur.execute("UPDATE usuarios SET senha = %s WHERE id = %s", (nova_senha, usuario_id))
        mysql.connection.commit()
        cur.close()

        flash('Senha alterada com sucesso!', 'success')
        return redirect(url_for('estoque'))

    return render_template('alterar_senha.html')

# Tela de Logout
@app.route('/logout')
def logout():
    session.clear()  # Limpa a sessão
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('login'))

# Tela de Gerenciamento de Estoque
@app.route('/estoque', methods=['GET', 'POST'])
def estoque():
    # Verifica se o usuário está logado
    if 'user_id' not in session:
        flash('Você precisa estar logado para acessar esta página!', 'warning')
        return redirect(url_for('login'))  # Redireciona para a página de login

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM produtos")
    produtos = cur.fetchall()
    cur.close()

    if request.method == 'POST':
        nome = request.form['nome']
        quantidade = request.form['quantidade']
        preco = request.form['preco']
        validade = request.form['validade']

        # Verificação de campos obrigatórios
        if not nome or not quantidade or not preco or not validade:
            flash('Todos os campos são obrigatórios!', 'danger')
            return render_template('estoque.html', produtos=produtos)

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO produtos (nome, quantidade, preco, validade) VALUES (%s, %s, %s, %s)",
                    (nome, quantidade, preco, validade))
        mysql.connection.commit()
        cur.close()

        flash('Produto adicionado com sucesso!', 'success')
        return redirect(url_for('estoque'))

    return render_template('estoque.html', produtos=produtos)

# Rota para editar produto
@app.route('/editar_produto/<int:produto_id>', methods=['GET', 'POST'])
def editar_produto(produto_id):
    # Verifica se o usuário está logado
    if 'user_id' not in session:
        flash('Você precisa estar logado para editar produtos!', 'warning')
        return redirect(url_for('login'))

    # Conectando ao banco de dados
    conn = mysql.connection.cursor()

    # Buscar o produto pelo ID
    conn.execute("SELECT * FROM produtos WHERE id = %s", (produto_id,))
    produto = conn.fetchone()

    if produto is None:
        flash('Produto não encontrado', 'danger')
        return redirect(url_for('estoque'))

    if request.method == 'POST':
        # Atualiza o produto
        nome = request.form['nome']
        validade = request.form['validade']
        quantidade = request.form['quantidade']
        preco = request.form['preco']

        conn.execute(""" 
            UPDATE produtos
            SET nome = %s, quantidade = %s, preco = %s, validade = %s
            WHERE id = %s
        """, (nome, quantidade, preco, validade, produto_id))
        mysql.connection.commit()
        conn.close()

        flash('Produto atualizado com sucesso!', 'success')
        return redirect(url_for('estoque'))

    conn.close()
    return render_template('editar_produto.html', produto=produto)

# Rota para excluir produto
@app.route('/excluir_produto/<int:produto_id>', methods=['POST'])
def excluir_produto(produto_id):
    # Verifica se o usuário está logado
    if 'user_id' not in session:
        flash('Você precisa estar logado para excluir produtos!', 'warning')
        return redirect(url_for('login'))

    # Obter o cursor para executar a query
    conn = mysql.connection.cursor()

    try:
        # Executar a query para excluir o produto com o ID fornecido
        conn.execute("DELETE FROM produtos WHERE id = %s", (produto_id,))
        
        # Commitar a transação
        mysql.connection.commit()

        # Mensagem de sucesso
        flash('Produto excluído com sucesso', 'success')

    except Exception as e:
        # Caso haja erro, rollback e mensagem de erro
        mysql.connection.rollback()
        flash(f'Erro ao excluir produto: {e}', 'danger')
    
    finally:
        # Fechar o cursor
        conn.close()

    # Redirecionar de volta para a página de gestão de estoque
    return redirect(url_for('estoque'))

# Rota para adicionar produto
@app.route('/adicionar_produto', methods=['GET', 'POST'])
def adicionar_produto():
    # Verifica se o usuário está logado
    if 'user_id' not in session:
        flash('Você precisa estar logado para adicionar produtos!', 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Recupera os dados do formulário
        nome = request.form['nome']
        quantidade = request.form['quantidade']
        preco = request.form['preco']
        validade = request.form['validade']

        # Validação básica
        if not nome or not quantidade or not preco or not validade:
            flash('Todos os campos são obrigatórios!', 'danger')
            return render_template('adicionar_produto.html')

        # Conecta ao banco e insere o novo produto
        cur = mysql.connection.cursor()
        cur.execute(
            '''
            INSERT INTO produtos (nome, quantidade, preco, validade)
            VALUES (%s, %s, %s, %s)
            ''',
            (nome, quantidade, preco, validade)
        )
        mysql.connection.commit()
        cur.close()

        flash('Produto adicionado com sucesso!', 'success')
        return redirect(url_for('estoque'))

    return render_template('adicionar_produto.html')

# Rota para relatórios
@app.route('/relatorios')
def relatorios():
    cur = mysql.connection.cursor()

    # Consultas fictícias para demonstrar relatórios
    cur.execute("SELECT nome, quantidade, preco FROM produtos")
    produtos = cur.fetchall()
    cur.close()

    return render_template('relatorios.html', produtos=produtos)

if __name__ == '__main__':
    app.run(debug=True)
    