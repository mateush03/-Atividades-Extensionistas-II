import os

from flask import Flask, render_template, request, redirect, url_for, g
import sqlite3
from datetime import datetime



app = Flask(__name__)
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "relatos.db")

# ---------- BANCO DE DADOS ----------

def get_db():
    """Abre uma conexão com o banco (uma por requisição)."""
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row  # permite acessar colunas pelo nome
    return g.db


@app.teardown_appcontext
def close_db(exception):
    """Fecha a conexão ao final da requisição."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Cria a tabela se não existir."""
    db = sqlite3.connect(DATABASE)
    db.execute("""
        CREATE TABLE IF NOT EXISTS relatos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            categoria TEXT NOT NULL,
            prioridade TEXT NOT NULL,
            descricao TEXT NOT NULL,
            bairro TEXT NOT NULL,
            cidade TEXT NOT NULL,
            endereco TEXT,
            data TEXT NOT NULL,
            criado_em TEXT NOT NULL
        )
    """)
    db.commit()
    db.close()


# ---------- ROTAS ----------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/relatar", methods=["GET", "POST"])
def novo_relato():
    if request.method == "POST":
        titulo = request.form["titulo"]
        categoria = request.form["categoria"]
        prioridade = request.form["prioridade"]
        descricao = request.form["descricao"]
        email = request.form["email"]          # ← NOVO
        bairro = request.form["bairro"]
        cidade = request.form["cidade"]
        endereco = request.form["endereco"]
        data = request.form["data"]

        db = get_db()
        db.execute(
            """INSERT INTO relatos
               (titulo, categoria, prioridade, descricao,
                email, bairro, cidade, endereco, data, criado_em)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (titulo, categoria, prioridade, descricao,
             email, bairro, cidade, endereco, data,
             datetime.now().strftime("%d/%m/%Y %H:%M"))
        )
        db.commit()

        return redirect(url_for("sucesso"))

    return render_template("novo_relato.html")


@app.route("/relatos")
def relatos():
    db = get_db()

    # Filtros opcionais via query string: /relatos?categoria=Iluminação&cidade=Fortaleza
    categoria = request.args.get("categoria", "")
    cidade = request.args.get("cidade", "")
    busca = request.args.get("busca", "")

    query = "SELECT * FROM relatos WHERE 1=1"
    params = []

    if categoria:
        query += " AND categoria = ?"
        params.append(categoria)
    if cidade:
        query += " AND cidade LIKE ?"
        params.append(f"%{cidade}%")
    if busca:
        query += " AND (titulo LIKE ? OR descricao LIKE ?)"
        params.extend([f"%{busca}%", f"%{busca}%"])

    query += " ORDER BY id DESC"  # mais recentes primeiro

    relatos = db.execute(query, params).fetchall()

    # Lista de categorias para o filtro
    categorias = db.execute(
        "SELECT DISTINCT categoria FROM relatos ORDER BY categoria"
    ).fetchall()

    return render_template(
        "relatos.html",
        relatos=relatos,
        categorias=categorias,
        categoria=categoria,
        cidade=cidade,
        busca=busca
    )


@app.route("/relato/<int:relato_id>")
def detalhe_relato(relato_id):
    db = get_db()
    relato = db.execute(
        "SELECT * FROM relatos WHERE id = ?", (relato_id,)
    ).fetchone()

    if relato is None:
        return redirect(url_for("relatos"))

    return render_template("detalhe_relato.html", relato=relato)


@app.route("/sucesso")
def sucesso():
    return render_template("sucesso.html")


if __name__ == "__main__":
    init_db()  # cria o banco e a tabela na primeira execução
    app.run(debug=True)

from flask import Response
import csv
import io

@app.route("/relatos/exportar")
def exportar_relatos():
    db = get_db()
    relatos = db.execute("SELECT * FROM relatos ORDER BY id DESC").fetchall()

    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")  # ; para abrir direto no Excel BR
    writer.writerow(["ID", "Título", "Categoria", "Prioridade", "Descrição",
                     "Bairro", "Cidade", "Endereço", "Data", "Registrado em"])

    for r in relatos:
        writer.writerow([r["id"], r["titulo"], r["categoria"], r["prioridade"],
                         r["descricao"], r["bairro"], r["cidade"],
                         r["endereco"], r["data"], r["criado_em"]])

    return Response(
        output.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=relatos.csv"}
    )