# Consulta de Submalhas

Aplicacao simples em Streamlit para consultar dados de SBs a partir de uma malha ferroviaria exportada.

O objetivo e manter a consulta rapida e direta, sem precisar substituir manualmente arquivos dentro do projeto toda vez que uma nova malha for exportada. A malha e carregada pelo usuario na tela do app.

## Funcionalidades

- Upload da malha exportada diretamente pela interface.
- Suporte a arquivos `.txt`, `.csv`, `.xlsx` e `.xls`.
- Consulta de uma ou varias SBs de uma vez.
- Busca flexivel, aceitando variacoes como `LIDP` para encontrar `LID___P`.
- Resumo com KM inicial, KM final, submalhas e quantidade de linhas encontradas.
- Visualizacao das linhas encontradas.
- Download dos resultados em CSV.
- Visualizacao geral da malha carregada.

## Estrutura do projeto

```text
.
|-- app_streamlit.py     # Aplicacao principal em Streamlit
|-- malha_core.py        # Leitura, indexacao e consulta da malha
|-- requirements.txt     # Dependencias do projeto
|-- app_flask.py         # Versao Flask antiga, mantida como referencia
```

## Como rodar localmente

Crie e ative um ambiente virtual:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Instale as dependencias:

```powershell
pip install -r requirements.txt
```

Execute a aplicacao:

```powershell
streamlit run app_streamlit.py
```

Depois disso, acesse o endereco exibido no terminal, normalmente:

```text
http://localhost:8501
```

## Como usar

1. Abra a aplicacao.
2. Carregue a malha exportada no menu lateral.
3. Digite uma ou mais SBs no campo de consulta.
4. Separe multiplas SBs por espaco, virgula ou ponto e virgula.
5. Clique em **Buscar**.
6. Confira o resumo e, se necessario, baixe as linhas encontradas em CSV.

Exemplo de consulta:

```text
LID___P, LID___D
```

## Publicacao no Streamlit Community Cloud

Para publicar a aplicacao:

1. Suba o projeto para um repositorio no GitHub.
2. Garanta que `app_streamlit.py`, `malha_core.py` e `requirements.txt` estejam no repositorio.
3. Acesse o Streamlit Community Cloud: https://share.streamlit.io
4. Clique em **Create app**.
5. Selecione o repositorio, a branch e informe o arquivo principal:

```text
app_streamlit.py
```

6. Clique em **Deploy**.

Documentacao oficial:

- Deploy no Community Cloud: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
- Organizacao dos arquivos: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/file-organization
- Dependencias do app: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies

## Observacao sobre arquivos de malha

Nao e necessario publicar a malha junto com o codigo. A aplicacao foi feita para receber a malha por upload.

Se a malha for grande, interna ou sensivel, nao inclua arquivos como estes no repositorio:

```text
Malha__exportado.txt
Malha_formatada.csv
uploads/
```

Cada usuario deve carregar a malha atualizada diretamente na interface do Streamlit.

## Dependencias principais

- Streamlit
- Pandas
- OpenPyXL
- xlrd

## Autor

Desenvolvido por Henrique Ortiz.
