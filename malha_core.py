import io
import re
from pathlib import Path

import pandas as pd


HEADERS = [
    "M",
    "Lat",
    "Long",
    "altura",
    "raio",
    "direcao",
    "pto_notaveis",
    "KM_esq",
    "vel_esq_s",
    "vel_esq_d",
    "KM_pri",
    "vel_pri_s",
    "vel_pri_d",
    "KM_dir",
    "vel_dir_s",
    "vel_dir_d",
    "Nome_SB",
    "Nome_SB_dir",
    "Nome_SB_esq",
    "Estado",
    "Vel1_cre",
    "Vel1_decre",
    "Vel2_cre",
    "Vel2_decre",
    "Vel3_decre",
    "Vel3_cre",
    "Vel4_decre",
    "Vel4_cre",
    "Vel5_decre",
    "Vel5_cre",
    "Vel6_decre",
    "Vel6_cre",
    "Vel7_decre",
    "Vel7_cre",
    "Estado_via",
    "Acao_via",
    "Tempo_sub",
    "Tempo_desc",
]

SB_COLUMNS = ["Nome_SB", "Nome_SB_dir", "Nome_SB_esq"]
KM_COLUMNS = ["KM_esq", "KM_pri", "KM_dir"]
INVALID_SB_VALUES = {"", "-", "0", "NAN", "NONE"}
SUMMARY_COLUMNS = [
    "Consulta",
    "Status",
    "SB",
    "KM_inicio",
    "KM_fim",
    "Submalhas",
    "Linhas",
]


def normalize_sb_name(nome):
    return re.sub(r"[^A-Z0-9]", "", str(nome).upper())


def parse_consultas(input_text):
    if not input_text:
        return []

    consultas = []
    seen = set()
    for item in re.split(r"[\s,;]+", input_text):
        item = item.strip()
        normalized = item.upper()
        if item and normalized not in seen:
            consultas.append(item)
            seen.add(normalized)
    return consultas


def is_valid_sb(value):
    value = str(value).strip()
    return value.upper() not in INVALID_SB_VALUES


def load_malha_from_bytes(file_name, file_bytes):
    suffix = Path(file_name).suffix.lower()

    if suffix in {".xlsx", ".xls"}:
        df, stats = _read_excel(file_bytes)
    elif suffix == ".csv":
        df, stats = _read_csv(file_bytes)
    else:
        df, stats = _read_text_export(file_bytes)

    if df.empty:
        raise ValueError("Nenhuma linha valida com 38 colunas foi encontrada.")

    return df, stats


def build_sb_index(df):
    index = {}

    for column in SB_COLUMNS:
        if column not in df.columns:
            continue

        values = df[column].map(lambda value: str(value).strip())
        valid_values = values[values.map(is_valid_sb)]
        for sb, row_indexes in valid_values.groupby(valid_values).groups.items():
            index.setdefault(sb, set()).update(row_indexes.tolist())

    return index


def search_sbs(input_text, df, sb_index):
    available_sbs = sorted(sb_index)
    summary_rows = []
    detail_frames = []

    for consulta in parse_consultas(input_text):
        sb = find_sb_name(consulta, available_sbs)
        if not sb:
            summary_rows.append(
                {
                    "Consulta": consulta,
                    "Status": "Nao encontrada",
                    "SB": "",
                    "KM_inicio": "",
                    "KM_fim": "",
                    "Submalhas": "",
                    "Linhas": 0,
                }
            )
            continue

        rows = df.loc[sorted(sb_index[sb])].copy()
        summary_rows.append(_summarize_rows(consulta, sb, rows))

        detail = rows.copy()
        detail.insert(0, "Consulta", consulta)
        detail.insert(1, "SB", sb)
        detail_frames.append(detail)

    summary_df = pd.DataFrame(summary_rows, columns=SUMMARY_COLUMNS)
    detail_df = (
        pd.concat(detail_frames, ignore_index=True)
        if detail_frames
        else pd.DataFrame(columns=["Consulta", "SB"] + HEADERS)
    )
    return summary_df, detail_df


def find_sb_name(query, available_sbs):
    query = str(query).strip()
    if not query:
        return None

    if query in available_sbs:
        return query

    normalized_query = normalize_sb_name(query)

    for sb in available_sbs:
        if normalize_sb_name(sb) == normalized_query:
            return sb

    for sb in available_sbs:
        normalized_sb = normalize_sb_name(sb)
        if normalized_query in normalized_sb or normalized_sb in normalized_query:
            return sb

    return None


def filter_by_sb(df, sb_index, sb):
    if not sb or sb not in sb_index:
        return pd.DataFrame(columns=df.columns)
    return df.loc[sorted(sb_index[sb])].copy()


def dataframe_to_csv_bytes(df):
    return df.to_csv(index=False, sep=";").encode("utf-8-sig")


def _summarize_rows(consulta, sb, rows):
    km_values = []
    for column in KM_COLUMNS:
        km_values.append(pd.to_numeric(rows[column], errors="coerce"))

    km_series = pd.concat(km_values, ignore_index=True).dropna()
    km_inicio = _format_number(km_series.min()) if not km_series.empty else ""
    km_fim = _format_number(km_series.max()) if not km_series.empty else ""

    submalhas = sorted(
        {str(value).strip() for value in rows["M"] if str(value).strip()},
        key=_natural_sort_key,
    )

    return {
        "Consulta": consulta,
        "Status": "Encontrada",
        "SB": sb,
        "KM_inicio": km_inicio,
        "KM_fim": km_fim,
        "Submalhas": ",".join(submalhas),
        "Linhas": len(rows),
    }


def _read_text_export(file_bytes):
    text = _decode_bytes(file_bytes)
    rows = []
    total_lines = 0

    for line in text.splitlines():
        if not line.strip():
            continue

        total_lines += 1
        fields = line.strip().split()
        if len(fields) == len(HEADERS):
            rows.append(fields)

    df = pd.DataFrame(rows, columns=HEADERS, dtype=str)
    stats = {
        "formato": "TXT",
        "linhas_origem": total_lines,
        "linhas_validas": len(df),
        "linhas_ignoradas": max(total_lines - len(df), 0),
    }
    return df, stats


def _read_csv(file_bytes):
    errors = []
    for sep in [None, ";", ",", "\t"]:
        for header in [0, None]:
            try:
                df = pd.read_csv(
                    io.BytesIO(file_bytes),
                    sep=sep,
                    engine="python",
                    dtype=str,
                    keep_default_na=False,
                    header=header,
                )
            except Exception as exc:
                errors.append(str(exc))
                continue

            if header == 0 and not _has_required_columns(df.columns):
                continue
            if df.shape[1] >= len(HEADERS):
                return _canonicalize_dataframe(df, "CSV")

    raise ValueError("Nao foi possivel ler o CSV no formato esperado.")


def _read_excel(file_bytes):
    try:
        df = pd.read_excel(
            io.BytesIO(file_bytes),
            dtype=str,
            keep_default_na=False,
        )
    except Exception as exc:
        raise ValueError(f"Nao foi possivel ler o Excel: {exc}") from exc

    if _has_required_columns(df.columns) and df.shape[1] >= len(HEADERS):
        return _canonicalize_dataframe(df, "Excel")

    try:
        df = pd.read_excel(
            io.BytesIO(file_bytes),
            dtype=str,
            keep_default_na=False,
            header=None,
        )
    except Exception as exc:
        raise ValueError(f"Nao foi possivel ler o Excel sem cabecalho: {exc}") from exc

    if df.shape[1] >= len(HEADERS):
        return _canonicalize_dataframe(df, "Excel")

    raise ValueError("A planilha precisa ter pelo menos 38 colunas.")


def _canonicalize_dataframe(df, formato):
    original_rows = len(df)
    df = df.iloc[:, : len(HEADERS)].copy()
    df.columns = HEADERS
    df = df.fillna("").astype(str)

    non_blank = df.apply(lambda column: column.str.strip().ne("")).any(axis=1)
    df = df.loc[non_blank].copy()
    df = df[df["M"].str.strip().str.upper() != "M"].copy()

    stats = {
        "formato": formato,
        "linhas_origem": original_rows,
        "linhas_validas": len(df),
        "linhas_ignoradas": max(original_rows - len(df), 0),
    }
    return df.reset_index(drop=True), stats


def _decode_bytes(file_bytes):
    for encoding in ["utf-8-sig", "utf-8", "latin-1"]:
        try:
            return file_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue
    return file_bytes.decode("utf-8", errors="replace")


def _has_required_columns(columns):
    names = {str(column).strip() for column in columns}
    return set(SB_COLUMNS).issubset(names)


def _format_number(value):
    value = float(value)
    if value.is_integer():
        return int(value)
    return round(value, 3)


def _natural_sort_key(value):
    try:
        return (0, float(value))
    except ValueError:
        return (1, str(value))
