# --- Crash shield: mostra traceback na página em vez de derrubar o processo ---
import traceback
try:
    import streamlit as st
    import pandas as pd
    from pathlib import Path
    import fastparquet as fp

    st.set_page_config(page_title="V-Dem Dashboard", layout="wide")

    # 1) Caminho robusto: raiz do repo (onde está este arquivo .py)
    REPO_ROOT = Path(__file__).resolve().parent
    # Se seus .parquet estão na raiz, use REPO_ROOT; se estiverem em "data/", troque abaixo:
    VDEM_PARQ  = (REPO_ROOT / "vdem_all.parquet").resolve()
    INDIC_PARQ = (REPO_ROOT / "indicadores_vdem.parquet").resolve()

    # 2) Validador: garante que é Parquet real (não LFS pointer / corrompido)
    def assert_is_real_parquet(path: Path):
        if not path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {path}")
        head_txt = path.read_bytes()[:200].decode("utf-8", errors="ignore")
        if head_txt.startswith("version https://git-lfs.github.com/spec/v1"):
            raise RuntimeError(
                f"{path.name} é um pointer do Git LFS (texto). Suba o binário real ou hospede fora do git."
            )
        with path.open("rb") as f:
            start = f.read(4)
            try:
                f.seek(-4, 2)
                end = f.read(4)
            except OSError:
                end = b""
        if start != b"PAR1" or end != b"PAR1":
            raise RuntimeError(
                f"{path.name} não tem assinatura PAR1 (início/fim). Pode estar corrompido/incompleto."
            )

    # 3) Leitura com fastparquet e mensagens claras
    @st.cache_data(show_spinner="Lendo Parquet…")
    def read_parquet_fast(path: Path) -> pd.DataFrame:
        assert_is_real_parquet(path)
        try:
            # Caminho A: via pandas
            return pd.read_parquet(path, engine="fastparquet")
        except Exception:
            # Caminho B (diagnóstico): via fastparquet direto
            try:
                pf = fp.ParquetFile(path)
                return pf.to_pandas()
            except Exception as e:
                raise RuntimeError(f"Falha ao ler {path.name} com fastparquet: {e}") from e

    def load_data():
        df  = read_parquet_fast(VDEM_PARQ)
        dfi = read_parquet_fast(INDIC_PARQ)
        return df, dfi

    # 4) App: nada pesado no import; botão para carregar
    def main():
        st.title("V-Dem Dashboard (Parquet)")
        with st.expander("⚙️ Carregamento de dados", expanded=True):
            st.markdown(f"**Arquivos**:\n- {VDEM_PARQ}\n- {INDIC_PARQ}")
            if st.button("Carregar Parquet", type="primary"):
                df, dfi = load_data()
                st.success(f"OK! V-Dem={len(df):,} | Indicadores={len(dfi):,}".replace(",", "."))
                st.dataframe(df.head(20))
                st.dataframe(dfi.head(20))

    try:
        main()
    except Exception:
        print("FATAL during main():", flush=True)
        traceback.print_exc()

except Exception:
    # Se quebrar no import/boot, mostramos na UI
    import streamlit as st, traceback
    st.set_page_config(page_title="V-Dem Dashboard (erro no boot)", layout="centered")
    st.error("Falha ao iniciar o app.")
    st.code(traceback.format_exc())
