# Requisitos:
# pip install flask flask_sqlalchemy pandas openpyxl

from flask import Flask, render_template, request, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os
import pandas as pd

app = Flask(__name__)
base_dir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(base_dir, 'credito.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

@app.context_processor
def inject_colors():
    return dict(
        cor_primaria="#00AE9D",
        cor_escura="#003641",
        cor_secundaria="#C9D200"
    )

db = SQLAlchemy(app)

# Modelo com todos os campos do layout novo
class Contrato(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cooperado = db.Column(db.String(100))
    contrato = db.Column(db.String(50))
    tipo = db.Column(db.String(50))
    garantia = db.Column(db.String(100))
    valor_contrato_sistema = db.Column(db.Float)
    baixa_48_meses = db.Column(db.String(10))
    valor_abatido = db.Column(db.Float)
    ganho = db.Column(db.Float)
    custas = db.Column(db.Float)
    custas_deduzidas = db.Column(db.Float)
    protesto = db.Column(db.Float)
    protesto_deduzido = db.Column(db.Float)
    honorario = db.Column(db.Float)
    honorario_repassado = db.Column(db.Float)
    alvara = db.Column(db.Float)
    alvara_recebido = db.Column(db.Float)
    valor_entrada = db.Column(db.Float)
    vencimento_entrada = db.Column(db.Date)
    valor_parcelas = db.Column(db.Float)
    parcelas = db.Column(db.Integer)
    parcelas_restantes = db.Column(db.Integer)
    vencimento_parcelas = db.Column(db.Date)
    qtd_boletos_emitidos = db.Column(db.Integer)
    valor_pg_boleto = db.Column(db.Float)
    data_pg_boleto = db.Column(db.Date)
    data_baixa = db.Column(db.Date)
    obs_contabilidade = db.Column(db.Text)
    obs_contas_receber = db.Column(db.Text)
    valor_repassado_escritorio = db.Column(db.Float)

class Parcela(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contrato_id = db.Column(db.Integer, db.ForeignKey('contrato.id'))
    numero = db.Column(db.Integer)
    valor = db.Column(db.Float)
    vencimento = db.Column(db.Date)
    quitada = db.Column(db.Boolean, default=False)

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
        try:
            contrato = Contrato(
                cooperado=request.form.get('cooperado'),
                contrato=request.form.get('contrato'),
                tipo=request.form.get('tipo'),
                garantia=request.form.get('garantia'),
                valor_contrato_sistema=float(request.form.get('valor_contrato_sistema') or 0),
                baixa_48_meses=request.form.get('baixa_48_meses'),
                valor_abatido=float(request.form.get('valor_abatido') or 0),
                ganho=float(request.form.get('ganho') or 0),
                custas=float(request.form.get('custas') or 0),
                custas_deduzidas=float(request.form.get('custas_deduzidas') or 0),
                protesto=float(request.form.get('protesto') or 0),
                protesto_deduzido=float(request.form.get('protesto_deduzido') or 0),
                honorario=float(request.form.get('honorario') or 0),
                honorario_repassado=float(request.form.get('honorario_repassado') or 0),
                alvara=float(request.form.get('alvara') or 0),
                alvara_recebido=float(request.form.get('alvara_recebido') or 0),
                valor_entrada=float(request.form.get('valor_entrada') or 0),
                vencimento_entrada=datetime.strptime(request.form.get('vencimento_entrada'), '%Y-%m-%d') if request.form.get('vencimento_entrada') else None,
                valor_parcelas=float(request.form.get('valor_parcelas') or 0),
                parcelas=int(request.form.get('parcelas') or 0),
                parcelas_restantes=int(request.form.get('parcelas_restantes') or 0),
                vencimento_parcelas=datetime.strptime(request.form.get('vencimento_parcelas'), '%Y-%m-%d') if request.form.get('vencimento_parcelas') else None,
                qtd_boletos_emitidos=int(request.form.get('qtd_boletos_emitidos') or 0),
                valor_pg_boleto=float(request.form.get('valor_pg_boleto') or 0),
                data_pg_boleto=datetime.strptime(request.form.get('data_pg_boleto'), '%Y-%m-%d') if request.form.get('data_pg_boleto') else None,
                data_baixa=datetime.strptime(request.form.get('data_baixa'), '%Y-%m-%d') if request.form.get('data_baixa') else None,
                obs_contabilidade=request.form.get('obs_contabilidade'),
                obs_contas_receber=request.form.get('obs_contas_receber'),
                valor_repassado_escritorio=float(request.form.get('valor_repassado_escritorio') or 0)
            )
            db.session.add(contrato)
            db.session.commit()

            return redirect(url_for('index'))
        except Exception as e:
            return f"Erro ao salvar contrato: {e}", 400

    return render_template('novo.html')

@app.route('/contrato/<int:id>', methods=['GET', 'POST'])
def ver_contrato(id):
    contrato = Contrato.query.get_or_404(id)
    parcelas = Parcela.query.filter_by(contrato_id=id).all()

    if request.method == 'POST':
        for field in request.form:
            if hasattr(Contrato, field):
                value = request.form.get(field)
                if value == '':
                    setattr(contrato, field, None)
                elif field in ['valor_contrato_sistema','valor_abatido','ganho','custas','custas_deduzidas',
                               'protesto','protesto_deduzido','honorario','honorario_repassado',
                               'alvara','alvara_recebido','valor_entrada','valor_parcelas','valor_pg_boleto',
                               'valor_repassado_escritorio']:
                    setattr(contrato, field, float(value))
                elif field in ['parcelas','parcelas_restantes','qtd_boletos_emitidos']:
                    setattr(contrato, field, int(value))
                elif field in ['vencimento_entrada','vencimento_parcelas','data_pg_boleto','data_baixa']:
                    setattr(contrato, field, datetime.strptime(value, '%Y-%m-%d'))
                else:
                    setattr(contrato, field, value)
        db.session.commit()
        return redirect(url_for('ver_contrato', id=id))

    return render_template('contrato.html', contrato=contrato, parcelas=parcelas, timedelta=timedelta)

@app.route('/deletar', methods=['POST'])
def deletar():
    ids = request.form.getlist('ids')
    if ids:
        for id_str in ids:
            contrato = Contrato.query.get(int(id_str))
            if contrato:
                Parcela.query.filter_by(contrato_id=contrato.id).delete()
                db.session.delete(contrato)
        db.session.commit()
    return redirect(url_for('index'))

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
