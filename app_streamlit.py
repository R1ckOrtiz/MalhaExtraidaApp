import streamlit as st

from malha_core import (
    build_sb_index,
    build_submalha_index,
    dataframe_to_csv_bytes,
    filter_by_sb,
    filter_by_submalha,
    load_malha_from_bytes,
    search_sbs,
    search_submalhas,
)


st.set_page_config(page_title="Consulta de SBs", layout="wide")

COORDINATE_COLUMN_CONFIG = {
    "Lat_decimal": st.column_config.NumberColumn("Lat decimal", format="%.6f"),
    "Long_decimal": st.column_config.NumberColumn("Long decimal", format="%.6f"),
    "Google_Maps": st.column_config.LinkColumn("Google Maps"),
}


@st.cache_data(show_spinner=False)
def prepare_file(file_name, file_bytes):
    df, stats = load_malha_from_bytes(file_name, file_bytes)
    sb_index = build_sb_index(df)
    submalha_index = build_submalha_index(df)
    return df, stats, sb_index, submalha_index


def format_int(value):
    return f"{int(value):,}".replace(",", ".")


def build_map_data(source_df, max_points=5000):
    if source_df.empty:
        return source_df
    if "Lat_decimal" not in source_df.columns or "Long_decimal" not in source_df.columns:
        return source_df.iloc[0:0]

    map_df = source_df[["Lat_decimal", "Long_decimal"]].dropna().head(max_points)
    return map_df.rename(columns={"Lat_decimal": "lat", "Long_decimal": "lon"})


def sort_submalhas(values):
    def sort_key(value):
        try:
            return (0, float(value))
        except ValueError:
            return (1, str(value))

    return sorted(values, key=sort_key)


def show_search_results(summary_df, detail_df, download_file_name, download_key):
    st.subheader("Resumo")
    st.dataframe(
        summary_df,
        use_container_width=True,
        hide_index=True,
        column_config=COORDINATE_COLUMN_CONFIG,
    )

    if detail_df.empty:
        return

    map_df = build_map_data(detail_df)
    if not map_df.empty:
        st.subheader("Mapa")
        st.map(map_df, use_container_width=True)

    st.subheader("Linhas encontradas")
    st.dataframe(
        detail_df,
        use_container_width=True,
        height=460,
        column_config=COORDINATE_COLUMN_CONFIG,
    )
    st.download_button(
        "Baixar linhas encontradas",
        data=dataframe_to_csv_bytes(detail_df),
        file_name=download_file_name,
        mime="text/csv",
        key=download_key,
    )


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
            df, stats, sb_index, submalha_index = prepare_file(
                uploaded_file.name,
                file_bytes,
            )
    except Exception as exc:
        st.error(f"Nao foi possivel carregar o arquivo: {exc}")
        st.stop()

    available_sbs = sorted(sb_index)
    available_submalhas = sort_submalhas(submalha_index)
    st.caption(f"Arquivo: {uploaded_file.name} | Formato: {stats['formato']}")

    col_linhas, col_sbs, col_submalhas, col_ignoradas = st.columns(4)
    col_linhas.metric("Linhas validas", format_int(stats["linhas_validas"]))
    col_sbs.metric("SBs encontradas", format_int(len(available_sbs)))
    col_submalhas.metric("Submalhas", format_int(len(available_submalhas)))
    col_ignoradas.metric("Linhas ignoradas", format_int(stats["linhas_ignoradas"]))

    consulta_tab, dados_tab = st.tabs(["Consulta", "Dados"])

    with consulta_tab:
        sb_search_tab, submalha_search_tab = st.tabs(["SB", "Submalha"])

        with sb_search_tab:
            with st.form("consulta_sbs"):
                sb_text = st.text_area(
                    "SBs",
                    placeholder="LID___P, LID___D",
                    height=90,
                )
                submitted_sb = st.form_submit_button("Buscar", type="primary")

            if submitted_sb and not sb_text.strip():
                st.warning("Informe pelo menos uma SB.")

            if sb_text.strip():
                summary_df, detail_df = search_sbs(sb_text, df, sb_index)
                show_search_results(
                    summary_df,
                    detail_df,
                    "consulta_sbs.csv",
                    "download_consulta_sbs",
                )

        with submalha_search_tab:
            with st.form("consulta_submalhas"):
                submalha_text = st.text_area(
                    "Submalhas",
                    placeholder="10, 97",
                    height=90,
                )
                submitted_submalha = st.form_submit_button("Buscar", type="primary")

            if submitted_submalha and not submalha_text.strip():
                st.warning("Informe pelo menos uma submalha.")

            if submalha_text.strip():
                summary_df, detail_df = search_submalhas(
                    submalha_text,
                    df,
                    submalha_index,
                )
                show_search_results(
                    summary_df,
                    detail_df,
                    "consulta_submalhas.csv",
                    "download_consulta_submalhas",
                )

    with dados_tab:
        view_mode = st.radio(
            "Visualizar",
            ["Todas", "SB", "Submalha"],
            horizontal=True,
        )
        row_limit = st.number_input(
            "Linhas na visualizacao",
            min_value=100,
            max_value=10000,
            value=1000,
            step=100,
        )

        if view_mode == "Todas":
            view_df = df.head(int(row_limit))
        elif view_mode == "SB":
            selected_sb = st.selectbox(
                "SB",
                available_sbs,
                index=0,
            )
            view_df = filter_by_sb(df, sb_index, selected_sb)
        else:
            selected_submalha = st.selectbox(
                "Submalha",
                available_submalhas,
                index=0,
            )
            view_df = filter_by_submalha(df, submalha_index, selected_submalha)

        map_df = build_map_data(view_df)
        if not map_df.empty:
            st.map(map_df, use_container_width=True)

        st.dataframe(
            view_df,
            use_container_width=True,
            height=520,
            column_config=COORDINATE_COLUMN_CONFIG,
        )
        st.download_button(
            "Baixar CSV da malha",
            data=dataframe_to_csv_bytes(df),
            file_name="malha_formatada.csv",
            mime="text/csv",
        )

    st.caption("Desenvolvido por Henrique Ortiz")


if __name__ == "__main__":
    main()
