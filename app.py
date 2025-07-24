# Requisitos:
# pip install flask flask_sqlalchemy pandas openpyxl

from flask import Flask, render_template, request, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from math import pow
import os
import pandas as pd

app = Flask(__name__)
base_dir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(base_dir, 'credito.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Contrato(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(50), nullable=False)
    cliente = db.Column(db.String(100), nullable=False)
    data = db.Column(db.Date, nullable=False)
    valor = db.Column(db.Float, nullable=False)
    custas = db.Column(db.Float, nullable=False)
    juros = db.Column(db.Float, nullable=False)
    prazo = db.Column(db.Integer, nullable=False)
    forma_pagamento = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='Ativo')
    tipo_contrato = db.Column(db.String(50))
    baixa_acima_48_meses = db.Column(db.Boolean, default=False)
    valor_abatido = db.Column(db.Float)
    ganho = db.Column(db.Float)
    custas_deduzidas = db.Column(db.Float)
    protesto = db.Column(db.Boolean, default=False)
    protesto_deduzido = db.Column(db.Float)
    honorario = db.Column(db.Float)
    honorario_repassado = db.Column(db.Float)
    alvara = db.Column(db.Float)
    alvara_recebido = db.Column(db.Float)
    valor_entrada = db.Column(db.Float)
    vencimento_entrada = db.Column(db.Date)
    parcelas_restantes = db.Column(db.Integer)
    qtd_boletos_emitidos = db.Column(db.Integer)
    valor_pago_com_boleto = db.Column(db.Float)
    data_pagamento_boleto = db.Column(db.Date)
    data_baixa = db.Column(db.Date)
    obs_contabilidade = db.Column(db.Text)
    obs_contas_receber = db.Column(db.Text)
    valor_repassado_escritorio = db.Column(db.Float)

    parcelas = db.relationship('Parcela', backref='contrato', lazy=True)
    garantias = db.relationship('Garantia', backref='contrato', lazy=True)

class Parcela(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contrato_id = db.Column(db.Integer, db.ForeignKey('contrato.id'), nullable=False)
    numero = db.Column(db.Integer, nullable=False)
    vencimento = db.Column(db.Date, nullable=False)
    valor = db.Column(db.Float, nullable=False)
    pago = db.Column(db.Boolean, default=False)

class Garantia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contrato_id = db.Column(db.Integer, db.ForeignKey('contrato.id'), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    descricao = db.Column(db.String(200))
    valor = db.Column(db.Float)
    data_avaliacao = db.Column(db.Date)
    status = db.Column(db.String(20), default='Ativa')

@app.before_request
def criar_tabelas():
    db.create_all()

@app.route('/')
def index():
    contratos = Contrato.query.all()
    return render_template('index.html', contratos=contratos)

@app.route('/novo', methods=['GET', 'POST'])
def novo():
    if request.method == 'POST':
        contrato = Contrato(
            numero=request.form['numero'],
            cliente=request.form['cliente'],
            data=datetime.strptime(request.form['data'], '%Y-%m-%d'),
            valor=float(request.form['valor']),
            custas=float(request.form['custas']),
            juros=float(request.form['juros']),
            prazo=int(request.form['prazo']),
            forma_pagamento=request.form['forma_pagamento'],
            tipo_contrato=request.form.get('tipo_contrato'),
            obs_contabilidade=request.form.get('obs_contabilidade')
        )
        db.session.add(contrato)
        db.session.commit()

        valor = contrato.valor
        i = contrato.juros
        n = contrato.prazo
        pmt = (valor * i) / (1 - pow(1 + i, -n)) if i > 0 else valor / n
        for m in range(1, n+1):
            vencimento = contrato.data + timedelta(days=30*m)
            parcela = Parcela(
                contrato_id=contrato.id,
                numero=m,
                vencimento=vencimento,
                valor=round(pmt, 2)
            )
            db.session.add(parcela)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('novo.html')

@app.route('/contrato/<int:id>', methods=['GET', 'POST'])
def ver_contrato(id):
    contrato = Contrato.query.get_or_404(id)
    if request.method == 'POST':
        contrato.cliente = request.form['cliente']
        contrato.status = request.form['status']
        contrato.tipo_contrato = request.form.get('tipo_contrato')
        contrato.obs_contabilidade = request.form.get('obs_contabilidade')
        db.session.commit()
        return redirect(url_for('ver_contrato', id=id))
    return render_template('contrato.html', contrato=contrato)

@app.route('/exportar')
def exportar():
    contratos = Contrato.query.all()
    dados = [c.__dict__ for c in contratos]
    for d in dados:
        d.pop('_sa_instance_state', None)
    df = pd.DataFrame(dados)
    export_path = os.path.join(base_dir, 'contratos_exportados.xlsx')
    df.to_excel(export_path, index=False)
    return send_file(export_path, as_attachment=True)

@app.route('/parcela/pagar/<int:id>')
def pagar_parcela(id):
    parcela = Parcela.query.get_or_404(id)
    parcela.pago = True
    db.session.commit()
    return redirect(url_for('ver_contrato', id=parcela.contrato_id))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)