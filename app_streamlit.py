import streamlit as st

from malha_core import (
    build_sb_index,
    dataframe_to_csv_bytes,
    filter_by_sb,
    load_malha_from_bytes,
    search_sbs,
)


st.set_page_config(page_title="Consulta de SBs", layout="wide")


@st.cache_data(show_spinner=False)
def prepare_file(file_name, file_bytes):
    df, stats = load_malha_from_bytes(file_name, file_bytes)
    sb_index = build_sb_index(df)
    return df, stats, sb_index


def format_int(value):
    return f"{int(value):,}".replace(",", ".")


def main():
    st.title("Consulta de Submalhas")

    with st.sidebar:
        st.header("Arquivo")
        uploaded_file = st.file_uploader(
            "Malha exportada",
            type=["txt", "csv", "xlsx", "xls"],
        )

    if uploaded_file is None:
        st.info("Carregue uma malha exportada para iniciar.")
        st.stop()

    file_bytes = uploaded_file.getvalue()
    try:
        with st.spinner("Carregando malha..."):
            df, stats, sb_index = prepare_file(uploaded_file.name, file_bytes)
    except Exception as exc:
        st.error(f"Nao foi possivel carregar o arquivo: {exc}")
        st.stop()

    available_sbs = sorted(sb_index)
    st.caption(f"Arquivo: {uploaded_file.name} | Formato: {stats['formato']}")

    col_linhas, col_sbs, col_ignoradas = st.columns(3)
    col_linhas.metric("Linhas validas", format_int(stats["linhas_validas"]))
    col_sbs.metric("SBs encontradas", format_int(len(available_sbs)))
    col_ignoradas.metric("Linhas ignoradas", format_int(stats["linhas_ignoradas"]))

    consulta_tab, dados_tab = st.tabs(["Consulta", "Dados"])

    with consulta_tab:
        with st.form("consulta_sbs"):
            sb_text = st.text_area(
                "SBs",
                placeholder="LID___P, LID___D",
                height=90,
            )
            submitted = st.form_submit_button("Buscar", type="primary")

        if submitted and not sb_text.strip():
            st.warning("Informe pelo menos uma SB.")

        if sb_text.strip():
            summary_df, detail_df = search_sbs(sb_text, df, sb_index)

            st.subheader("Resumo")
            st.dataframe(summary_df, use_container_width=True, hide_index=True)

            if not detail_df.empty:
                st.subheader("Linhas encontradas")
                st.dataframe(detail_df, use_container_width=True, height=460)
                st.download_button(
                    "Baixar linhas encontradas",
                    data=dataframe_to_csv_bytes(detail_df),
                    file_name="consulta_sbs.csv",
                    mime="text/csv",
                )

    with dados_tab:
        selected_sb = st.selectbox(
            "SB",
            ["Todas"] + available_sbs,
            index=0,
        )
        row_limit = st.number_input(
            "Linhas na visualizacao",
            min_value=100,
            max_value=10000,
            value=1000,
            step=100,
        )

        if selected_sb == "Todas":
            view_df = df.head(int(row_limit))
        else:
            view_df = filter_by_sb(df, sb_index, selected_sb)

        st.dataframe(view_df, use_container_width=True, height=520)
        st.download_button(
            "Baixar CSV da malha",
            data=dataframe_to_csv_bytes(df),
            file_name="malha_formatada.csv",
            mime="text/csv",
        )

    st.caption("Desenvolvido por Henrique Ortiz")


if __name__ == "__main__":
    main()
