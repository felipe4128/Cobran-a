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

# Modelo atualizado com todos os campos e nullable=True
class Contrato(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data_contrato = db.Column(db.Date, nullable=True)
    cliente = db.Column(db.String(100), nullable=True)
    numero = db.Column(db.String(50), nullable=True)
    tipo_contrato = db.Column(db.String(50), nullable=True)
    garantia = db.Column(db.String(100), nullable=True)
    valor = db.Column(db.Float, nullable=True)
    parcelas = db.Column(db.Integer, nullable=True)
    parcelas_restantes = db.Column(db.Integer, nullable=True)
    vencimento_parcelas = db.Column(db.Date, nullable=True)

    baixa_48_meses = db.Column(db.Float, nullable=True)
    valor_abatido = db.Column(db.Float, nullable=True)
    ganho = db.Column(db.Float, nullable=True)
    custas = db.Column(db.Float, nullable=True)
    custas_deduzidas = db.Column(db.Float, nullable=True)
    protesto = db.Column(db.Float, nullable=True)
    protesto_deduzido = db.Column(db.Float, nullable=True)
    honorario = db.Column(db.Float, nullable=True)
    honorario_repassado = db.Column(db.Float, nullable=True)
    alvara = db.Column(db.Float, nullable=True)
    alvara_recebido = db.Column(db.Float, nullable=True)
    valor_entrada = db.Column(db.Float, nullable=True)
    vencimento_entrada = db.Column(db.Date, nullable=True)
    valor_parcelas = db.Column(db.Float, nullable=True)
    qtd_boletos = db.Column(db.Integer, nullable=True)
    valor_pg_boleto = db.Column(db.Float, nullable=True)
    data_pg_boleto = db.Column(db.Date, nullable=True)
    data_baixa = db.Column(db.Date, nullable=True)
    obs_contabilidade = db.Column(db.Text, nullable=True)
    obs_contas_receber = db.Column(db.Text, nullable=True)
    valor_repassado_escritorio = db.Column(db.Float, nullable=True)

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
def novo_contrato():
    if request.method == 'POST':
        try:
            data_contrato = request.form.get('data_contrato')
            data_contrato = datetime.strptime(data_contrato, '%Y-%m-%d') if data_contrato else None

            parcelas = int(request.form.get('parcelas')) if request.form.get('parcelas') else None
            valor = float(request.form.get('valor')) if request.form.get('valor') else None

            vencimento_parcelas = request.form.get('vencimento_parcelas')
            vencimento_parcelas = datetime.strptime(vencimento_parcelas, '%Y-%m-%d') if vencimento_parcelas else None

            contrato = Contrato(
                data_contrato=data_contrato,
                cliente=request.form.get('cliente') or None,
                numero=request.form.get('numero') or None,
                tipo_contrato=request.form.get('tipo_contrato') or None,
                garantia=request.form.get('garantia') or None,
                valor=valor,
                parcelas=parcelas,
                parcelas_restantes=parcelas,
                vencimento_parcelas=vencimento_parcelas,
                baixa_48_meses=request.form.get('baixa_48_meses') or None,
                valor_abatido=request.form.get('valor_abatido') or None,
                ganho=request.form.get('ganho') or None,
                custas=request.form.get('custas') or None,
                custas_deduzidas=request.form.get('custas_deduzidas') or None,
                protesto=request.form.get('protesto') or None,
                protesto_deduzido=request.form.get('protesto_deduzido') or None,
                honorario=request.form.get('honorario') or None,
                honorario_repassado=request.form.get('honorario_repassado') or None,
                alvara=request.form.get('alvara') or None,
                alvara_recebido=request.form.get('alvara_recebido') or None,
                valor_entrada=request.form.get('valor_entrada') or None,
                vencimento_entrada=datetime.strptime(request.form.get('vencimento_entrada'), '%Y-%m-%d') if request.form.get('vencimento_entrada') else None,
                valor_parcelas=request.form.get('valor_parcelas') or None,
                qtd_boletos=request.form.get('qtd_boletos') or None,
                valor_pg_boleto=request.form.get('valor_pg_boleto') or None,
                data_pg_boleto=datetime.strptime(request.form.get('data_pg_boleto'), '%Y-%m-%d') if request.form.get('data_pg_boleto') else None,
                data_baixa=datetime.strptime(request.form.get('data_baixa'), '%Y-%m-%d') if request.form.get('data_baixa') else None,
                obs_contabilidade=request.form.get('obs_contabilidade') or None,
                obs_contas_receber=request.form.get('obs_contas_receber') or None,
                valor_repassado_escritorio=request.form.get('valor_repassado_escritorio') or None
            )

            db.session.add(contrato)
            db.session.commit()

            # gera parcelas, se houver
            if parcelas and valor:
                valor_parcela = round(valor / parcelas, 2)
                for i in range(1, parcelas + 1):
                    vencimento = (vencimento_parcelas or data_contrato or datetime.today()) + timedelta(days=30 * (i - 1))
                    parcela = Parcela(
                        contrato_id=contrato.id,
                        numero=i,
                        valor=valor_parcela,
                        vencimento=vencimento,
                        quitada=False
                    )
                    db.session.add(parcela)
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
                elif field in ['valor', 'baixa_48_meses', 'valor_abatido', 'ganho', 'custas', 'custas_deduzidas',
                               'protesto', 'protesto_deduzido', 'honorario', 'honorario_repassado',
                               'alvara', 'alvara_recebido', 'valor_entrada', 'valor_parcelas',
                               'valor_pg_boleto', 'valor_repassado_escritorio']:
                    setattr(contrato, field, float(value))
                elif field in ['parcelas', 'parcelas_restantes', 'qtd_boletos']:
                    setattr(contrato, field, int(value))
                elif field in ['data_contrato', 'vencimento_parcelas', 'vencimento_entrada',
                               'data_pg_boleto', 'data_baixa']:
                    setattr(contrato, field, datetime.strptime(value, '%Y-%m-%d'))
                else:
                    setattr(contrato, field, value)
        db.session.commit()
        return redirect(url_for('ver_contrato', id=id))

    return render_template('contrato.html', contrato=contrato, parcelas=parcelas, timedelta=timedelta)

@app.route('/parcela/<int:id>/quitar', methods=['POST'])
def quitar_parcela(id):
    parcela = Parcela.query.get_or_404(id)
    parcela.quitada = True
    contrato = Contrato.query.get(parcela.contrato_id)
    if contrato.parcelas_restantes and contrato.parcelas_restantes > 0:
        contrato.parcelas_restantes -= 1
    db.session.commit()
    return redirect(url_for('ver_contrato', id=parcela.contrato_id))

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