from flask import Flask, request, render_template_string
import re

app = Flask(__name__)

# Cabeçalhos baseados no Excel
headers = [
    'M', 'Lat', 'Long', 'altura', 'raio', 'direção', 'pto_notaveis',
    'KM_esq', 'vel_esq_s', 'vel_esq_d', 'KM_pri', 'vel_pri_s', 'vel_pri_d',
    'KM_dir', 'vel_dir_s', 'vel_dir_d', 'Nome_SB', 'Nome_SB_dir', 'Nome_SB_esq',
    'Estado', 'Vel1_cre', 'Vel1_decre', 'Vel2_cre', 'Vel2_decre', 'Vel3_decre',
    'Vel3_cre', 'Vel4_decre', 'Vel4_cre', 'Vel5_decre', 'Vel5_cre', 'Vel6_decre',
    'Vel6_cre', 'Vel7_decre', 'Vel7_cre', 'Estado_via', 'Acao_via', 'Tempo_sub', 'Tempo_desc'
]

# Carregar dados do TXT
def carregar_dados(arquivo):
    dados = {}
    with open(arquivo, 'r', encoding='utf-8') as f:
        for linha in f:
            campos = linha.strip().split()
            if len(campos) == 38:
                # Campos que podem conter o nome da SB: Nome_SB, Nome_SB_dir, Nome_SB_esq
                for i in [16, 17, 18]:
                    sb = campos[i].strip()
                    if sb and sb not in ['-', '0', '']:
                        if sb not in dados:
                            dados[sb] = []
                        dados[sb].append(campos)
                # Se nenhuma SB válida foi encontrada, mantém o comportamento anterior como fallback
                if not any(campos[i].strip() and campos[i].strip() not in ['-', '0', ''] for i in [16, 17, 18]):
                    for campo in campos:
                        if re.match(r'^[A-Z0-9]{1,20}(_*_[A-Z0-9]+)?$', campo):
                            sb = campo
                            if sb not in dados:
                                dados[sb] = []
                            dados[sb].append(campos)
                            break
    return dados

def consolidar_dados(linhas):
    """Consolida linhas idênticas exceto pela coluna M, agrupando M com vírgula"""
    if not linhas:
        return []
    
    # Estrutura: chave é a tupla de campos[1:] (todos exceto M), valor é lista de M
    consolidated = {}
    for linha in linhas:
        chave = tuple(linha[1:])  # Todos os campos exceto M
        if chave not in consolidated:
            consolidated[chave] = []
        consolidated[chave].append(linha[0])  # Adiciona M
    
    # Reconstrói as linhas consolidadas
    resultado = []
    for chave, m_values in consolidated.items():
        m_consolidado = ','.join(sorted(set(m_values)))  # Agrupa M com vírgula
        linha_consolidada = [m_consolidado] + list(chave)
        resultado.append(linha_consolidada)
    
    return resultado

def normalize_sb_name(nome):
    return re.sub(r'[^A-Z0-9]', '', nome.upper())


def resumo_sb(sb_nome):
    if not sb_nome:
        return None

    sb_normalizada = normalize_sb_name(sb_nome)
    sb_encontrada = None

    # Busca exata primeiro
    if sb_nome in dados_sbs:
        sb_encontrada = sb_nome
    else:
        # Busca por equivalência sem underscores/caracteres especiais
        for sb in dados_sbs.keys():
            if normalize_sb_name(sb) == sb_normalizada:
                sb_encontrada = sb
                break

        # Busca substring flexível (para casos parciais)
        if not sb_encontrada:
            for sb in dados_sbs.keys():
                nsb = normalize_sb_name(sb)
                if sb_normalizada in nsb or nsb in sb_normalizada:
                    sb_encontrada = sb
                    break

    if not sb_encontrada:
        return None

    linhas = dados_sbs.get(sb_encontrada, [])
    if not linhas:
        return None

    submalhas = sorted({linha[0] for linha in linhas})

    km_values = []
    for linha in linhas:
        for idx in [7, 10, 13]:  # KM_esq, KM_pri, KM_dir
            try:
                km_values.append(float(linha[idx]))
            except (ValueError, IndexError):
                pass

    km_inicio = min(km_values) if km_values else None
    km_fim = max(km_values) if km_values else None

    def format_km(km):
        if km is None:
            return None
        if float(km).is_integer():
            return int(km)
        return km

    return {
        'sb': sb_encontrada,
        'km_inicio': format_km(km_inicio),
        'km_fim': format_km(km_fim),
        'submalhas': ','.join(submalhas),
        'ocorrencias': len(linhas)
    }


def resumo_sbs(input_text):
    if not input_text:
        return []
    sb_lista = [x.strip() for x in re.split(r'[\s,;]+', input_text) if x.strip()]
    resultados = []
    for sb in sb_lista:
        info = resumo_sb(sb)
        if info:
            resultados.append(info)
    return resultados


dados_sbs = carregar_dados("Malha__exportado.txt")

# Template HTML simples
template = """
<!DOCTYPE html>
<html>
<head>
    <title>Consulta de SBs</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        form { margin-bottom: 20px; }
        input { padding: 5px; width: 200px; }
        button { padding: 5px 10px; }
        table { border-collapse: collapse; width: 100%; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; font-size: 12px; }
        th { background-color: #f2f2f2; position: sticky; top: 0; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        .scroll { max-height: 600px; overflow-y: auto; }
    </style>
</head>
<body>
    <h1>Consulta de Submalhas (SBs) - Malha Ferroviária</h1>
    <p>Consulte Km início, Km fim e submalhas associadas a SB de acordo com a última malha em produção
    (Lembre - se de colocar a malha exportada de produção para consulta)</p>
    <form method="post">
        <label for="sb">Digite o nome da SB (ex.: LID___P):</label>
        <input type="text" id="sb" name="sb" required>
        <button type="submit">Buscar</button>
    </form>
    {% if sb_resultados %}
        <h2>Resumo para SBs</h2>
        <p>SBs consultadas: {{ sb_resultados|length }}</p>
        <table>
            <tr>
                <th>SB</th>
                <th>KM Início</th>
                <th>KM Fim</th>
                <th>Submalhas</th>
            </tr>
            {% for r in sb_resultados %}
            <tr>
                <td>{{ r.sb }}</td>
                <td>{{ r.km_inicio }}</td>
                <td>{{ r.km_fim }}</td>
                <td>{{ r.submalhas }}</td>
            </tr>
            {% endfor %}
        </table>
    {% elif sb_nome %}
        <p>Nenhuma ocorrência encontrada para essa SB.</p>
    {% endif %}
    <footer>
        <p>Desenvolvido por Henrique Ortiz</p>
    </footer>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    sb_nome = None
    sb_resultados = []
    if request.method == 'POST':
        sb_nome = request.form.get('sb')
        sb_resultados = resumo_sbs(sb_nome)
    return render_template_string(template, sb_nome=sb_nome, sb_resultados=sb_resultados)


if __name__ == '__main__':
    app.run(debug=True)