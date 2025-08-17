# vdem_dashboard
import streamlit as st
import altair as alt
import pandas as pd
import time
import numpy as np
from pathlib import Path
from natsort import natsorted

# C:\PROJECTS\.venv10\Scripts\Activate.ps1
# cd C:\PROJECTS\P1-VDEM_dashboard
# streamlit run vdem_dashboard.py --server.runOnSave true

# ==========================
# CONFIG & ESTILO
# ==========================
st.set_page_config(page_title="Democracias no Mundo", layout="wide")
st.markdown("""
<style>
/* remove padding topo */
.block-container {padding-top: 1.2rem;}
/* títulos mais elegantes */
h1, h2, h3 { font-weight: 700; }
[data-testid="stMetricValue"] { font-size: 1.4rem; }
</style>
""", unsafe_allow_html=True)

st.title("Democracias no Mundo")
st.write("O desenvolvimento dos direitos civis e institucionais de cada país ao longo do século XIX e XX")

# ==========================
# HELPERS
# ==========================
DATA_PATH = Path("C:/PROJECTS/P1-VDEM_dashboard/UNdem-All.csv")

def load_data():
    if DATA_PATH.exists():
        df = pd.read_csv(DATA_PATH)
    else:
        # ---- fallback de demonstração (mock) ----
        np.random.seed(7)
        years = np.arange(1900, 2021)
        countries = ["Brazil","Argentina","Chile","United States","Canada","France","Germany","United Kingdom","Japan","China","India","South Africa"]
        recs = []
        for c in countries:
            base = np.linspace(0.2, 0.8, len(years)) + np.random.normal(0, 0.05, len(years))
            recs.append(pd.DataFrame({
                "country_name": c,
                "year": years,
                "v2x_polyarchy": np.clip(base, 0, 1),
                "e_gdppc": np.clip(500 + 20*(years-1900) + np.random.normal(0, 500, len(years)), 300, None),
                "e_peaveduc": np.clip(2 + 0.03*(years-1900) + np.random.normal(0, 0.2, len(years)), 0, 15),
                "e_civil_war": (np.random.rand(len(years))>0.97).astype(int),
            }))
        df = pd.concat(recs, ignore_index=True)
        st.info("⚠️ Base real não encontrada. Exibindo dados de demonstração.")
    # garante tipos
    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    return df

def exists_cols(df, cols):
    return all(c in df.columns for c in cols)

def line_chart_altair(df, x, y, color=None, title=None):
    """Linha com Altair e eixos limpos para ano."""
    enc = alt.Chart(df).mark_line().encode(
        x=alt.X(f"{x}:Q", axis=alt.Axis(format="d")),
        y=alt.Y(f"{y}:Q"),
        color=color
    )
    return enc.properties(title=title).interactive()

def group_mean_over_time(df, group_col, value_col, year_col="year"):
    g = (df
         .groupby([year_col, group_col], as_index=False)[value_col]
         .mean(numeric_only=True))
    return g


# ==========================
# 1) MAPAS DE CLASSE E GRUPO (TOC → PT-BR)
# ==========================
CLASS_MAP = {
    "1": "Identificadores",
    "2": "Índices de Democracia do V-Dem",
    "3": "Indicadores V-Dem",
    "4": "V-Dem Histórico",
    "5": "Outros Índices Criados pelo V-Dem",
    "6": "Sistemas Partidários",
    "7": "Digital Society Survey",
    "8": "Variedades de Doutrinação",
    "9": "Outros Índices e Indicadores de Democracia",
    "10": "Fatores de Contexto (E)",
}

GROUP_MAP = {
    # 2.x
    "2.1": "Índices de Democracia Agregados (High-Level)",
    "2.2": "Componentes de Democracia (Mid-Level)",
    # 3.x
    "3.1": "Eleições",
    "3.2": "Partidos Políticos",
    "3.3": "Democracia Direta",
    "3.4": "Poder Executivo",
    "3.5": "Poder Legislativo",
    "3.6": "Deliberação",
    "3.7": "Judiciário",
    "3.8": "Liberdades Civis",
    "3.9": "Soberania/Estado",
    "3.10": "Sociedade Civil",
    "3.11": "Mídia",
    "3.12": "Igualdade Política",
    "3.13": "Exclusão",
    "3.14": "Legitimação",
    "3.15": "Espaço Cívico e Acadêmico",
    # 4.x (Histórico)
    "4.1": "Eleições (Hist.)",
    "4.2": "Partidos Políticos (Hist.)",
    "4.3": "Poder Legislativo (Hist.)",
    "4.4": "Judiciário (Hist.)",
    "4.5": "Liberdades Civis (Hist.)",
    "4.6": "Soberania/Estado (Hist.)",
    "4.7": "Igualdade Política (Hist.)",
    "4.8": "V-Dem Histórico Modificado",
    "4.9": "Sobreposições/Discrepâncias (Hist.)",
    # 5.x
    "5.1": "Regimes do Mundo (RoW)",
    "5.2": "Accountability",
    "5.3": "Bases de Poder do Executivo",
    "5.4": "Neopatrimonialismo",
    "5.5": "Liberdades Civis",
    "5.6": "Exclusão",
    "5.7": "Corrupção",
    "5.8": "Empoderamento das Mulheres",
    "5.9": "Estado de Direito",
    "5.10": "Democracia Direta",
    "5.11": "Sociedade Civil",
    "5.12": "Eleições",
    "5.13": "Institucionalização Partidária",
    "5.14": "Dimensões de Democracia Consensual",
    "5.15": "Liberdade Acadêmica",
    # 6.x
    "6.1": "Índices de Democracia do Sistema Partidário",
    "6.2": "Democracia da Coalizão de Governo",
    "6.3": "Democracia dos Partidos de Oposição",
    "6.4": "Religião do Sistema Partidário",
    "6.5": "Religião da Coalizão de Governo",
    "6.6": "Religião dos Partidos de Oposição",
    "6.7": "Exclusão no Sistema Partidário",
    "6.8": "Exclusão — Coalizão de Governo",
    "6.9": "Exclusão — Oposição",
    "6.10": "Esquerda–Direita do Sistema Partidário",
    "6.11": "Esquerda–Direita — Governo",
    "6.12": "Esquerda–Direita — Oposição",
    # 7.x
    "7.1": "Operações Coordenadas de Informação",
    "7.2": "Liberdade de Mídia Digital",
    "7.3": "Capacidade e Abordagem Estatal de Regulação Online",
    "7.4": "Polarização na Mídia Online",
    "7.5": "Clivagens Sociais",
    # 8.x
    "8.1": "Índices de Doutrinação",
    "8.2": "Currículo Geral",
    "8.3": "Currículo por Disciplinas",
    "8.4": "Professores",
    "8.5": "Escolas",
    "8.6": "Mídia (Doutrinação)",
    # 9.x
    "9.1": "Versões Ordinais de Índices",
    "9.2": "Regimes Políticos",
    "9.3": "Freedom House",
    "9.4": "World Bank Governance Indicators",
    "9.5": "Índice Lexical de Democracia Eleitoral",
    "9.6": "Unified Democracy Score",
    "9.7": "Instituições/ Eventos Políticos",
    "9.8": "Polity5",
    "9.9": "Outros",
    # 10.x
    "10.1": "Educação (E)",
    "10.2": "Geografia (E)",
    "10.3": "Economia (E)",
    "10.4": "Riqueza de Recursos Naturais (E)",
    "10.5": "Infraestrutura (E)",
    "10.6": "Demografia (E)",
    "10.7": "Conflito (E)",
}

# ==========================
# 2) CARREGAR DADOS
# ==========================
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("C:/PROJECTS/P1-VDEM_dashboard/UNdem-All.csv")
        time.sleep(1.5)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados principais: {e}")

df = load_data()

# Filtra colunas úteis (remove estatísticas auxiliares)
heads = df.columns.to_list()
head = [c for c in heads if not c.endswith(('_sd', '_osp', '_codelow', '_codehigh', '_ord', '_mean', '_nr'))]

# ==========================
# 3) LER NOVO CSV (3 colunas) E RECONSTRUIR CLASSE/GRUPO
# ==========================
def read_indicadores_csv(path):
    try:
        return pd.read_csv(path, sep=None, engine="python")
    except Exception:
        for sep in [",", ";", "\t", "|"]:
            try:
                return pd.read_csv(path, sep=sep)
            except Exception:
                continue
        raise

csv_path = "C:/PROJECTS/P1-VDEM_dashboard/indicadores_vdem.csv"
df_indicadores = read_indicadores_csv(csv_path)
df_indicadores = df_indicadores.rename(columns={
    'titulo': 'titulo',
    'variavel': 'variavel',
    'id': 'id'
})[['id', 'titulo', 'variavel']]

# Decompõe id → partes e extrai classe/grupo
df_indicadores["partes"]    = df_indicadores["id"].astype(str).str.split(".")
df_indicadores["classe_id"] = df_indicadores["partes"].apply(lambda p: p[0] if len(p) >= 1 else None)
df_indicadores["grupo_id"]  = df_indicadores["partes"].apply(lambda p: ".".join(p[:2]) if len(p) >= 2 else None)
df_indicadores["Classe"]    = df_indicadores["classe_id"].map(CLASS_MAP)
df_indicadores["Grupo"]     = df_indicadores["grupo_id"].map(GROUP_MAP)

def define_nivel(partes):
    if len(partes) == 1: return "Classe"
    if len(partes) == 2: return "Grupo"
    return "Variavel"

df_indicadores["nivel"] = df_indicadores["partes"].apply(define_nivel)

# Catálogo final de variáveis existentes no df principal
variaveis = (
    df_indicadores[df_indicadores["nivel"] == "Variavel"]
    .query("variavel in @df.columns")
    .copy()
)

# ====================================
# 4) SIDEBAR – PAÍS / REGIÃO / PERÍODO
# ====================================
st.sidebar.header("Filtros")
# País (pré-seleção Brazil se existir)
paises_all = natsorted(df["country_name"].dropna().unique())
default_index = paises_all.index("Brazil") if "Brazil" in paises_all else 0
selected_country = st.sidebar.selectbox("Selecione um país:", paises_all, index=default_index)

# REGIÕES → adiciona países ao comparativo
REGION_MAP = {
    "America do Norte & Caribe": [
        "United States","Canada","Mexico", "Bahamas","Barbados","Cuba","Dominican Republic",
        "Haiti","Jamaica","Trinidad and Tobago","Antigua and Barbuda","Dominica",
        "Grenada","Saint Kitts and Nevis","Saint Lucia","Saint Vincent and the Grenadines"
    ],

    "America Latina": [
        "Mexico","Belize","Costa Rica","El Salvador","Guatemala","Honduras","Nicaragua","Panama",
        "Argentina","Bolivia","Brazil","Chile","Colombia","Ecuador","Guyana",
        "Paraguay","Peru","Suriname","Uruguay","Venezuela"
    ],

    "América do Sul": [
        "Argentina","Bolivia","Brazil","Chile","Colombia","Ecuador",
        "Guyana","Paraguay","Peru","Suriname","Uruguay","Venezuela"
    ],

    "Oeste Europeu": [
        "Austria", "Belgium", "Denmark", "Finland", "France", "Germany", "Ireland", "Italy",
        "Luxembourg", "Netherlands", "Norway", "Portugal", "Spain", "Sweden", "Switzerland",
        "United Kingdom"
    ],

    "Zona do Euro": [
        "Austria","Belgium","Cyprus","Estonia","Finland","France","Germany","Greece","Ireland",
        "Italy","Latvia","Lithuania","Luxembourg","Malta","Netherlands","Portugal","Slovakia",
        "Slovenia","Spain"
    ],

    "Leste Europeu": [
        "Albania","Bosnia and Herzegovina","Bulgaria","Croatia","Czech Republic","Hungary", "Slovakia", "Slovenia"
        "Kosovo","Montenegro","North Macedonia","Poland","Romania","Serbia","Belarus","Moldova","Ukraine","Russia"
    ],

    "Ásia (Centro-Sul)": [
        "Afghanistan","Armenia","Azerbaijan","Bangladesh","Bhutan","Georgia","India",
        "Kazakhstan","Kyrgyzstan","Maldives","Nepal","Pakistan","Sri Lanka",
        "Tajikistan","Turkmenistan","Uzbekistan"
    ],

    "Ásia (Leste)": [
        "China","Japan","Mongolia","North Korea","South Korea","Taiwan"
    ],

    "Ásia": [
        "Afghanistan","Armenia","Azerbaijan","Bahrain","Bangladesh","Bhutan","Brunei","Cambodia",
        "China","Georgia","India","Indonesia","Iran","Iraq","Israel","Japan","Jordan","Kazakhstan",
        "Kuwait","Kyrgyzstan","Laos","Lebanon","Malaysia","Maldives","Mongolia","Myanmar","Nepal",
        "North Korea","Oman","Pakistan","Philippines","Qatar","Saudi Arabia","Singapore","South Korea",
        "Sri Lanka","Syria","Tajikistan","Thailand","Timor-Leste","Turkey","Turkmenistan","United Arab Emirates",
        "Uzbekistan","Vietnam","Yemen"
    ],

    "Oriente Médio": [
        "Bahrain","Cyprus","Egypt","Iran","Iraq","Israel","Jordan","Kuwait","Lebanon",
        "Oman","Palestine","Qatar","Saudi Arabia","Syria","Turkey","United Arab Emirates","Yemen"
    ],

    "África": [
        "Algeria","Angola","Benin","Botswana","Burkina Faso","Burundi","Cabo Verde","Cameroon",
        "Central African Republic","Chad","Comoros","Congo","Democratic Republic of the Congo",
        "Djibouti","Egypt","Equatorial Guinea","Eritrea","Eswatini","Ethiopia","Gabon","Gambia",
        "Ghana","Guinea","Guinea-Bissau","Ivory Coast","Kenya","Lesotho","Liberia","Libya",
        "Madagascar","Malawi","Mali","Mauritania","Mauritius","Morocco","Mozambique","Namibia",
        "Niger","Nigeria","Rwanda","São Tomé and Príncipe","Senegal","Seychelles","Sierra Leone",
        "Somalia","South Africa","South Sudan","Sudan","Tanzania","Togo","Tunisia","Uganda",
        "Zambia","Zimbabwe"
    ],

    "Oceania & Pacífico": [
        "Australia","New Zealand","Fiji","Kiribati","Marshall Islands","Micronesia","Nauru",
        "Palau","Papua New Guinea","Samoa","Solomon Islands","Tonga","Tuvalu","Vanuatu"
    ],
    
    "Conselho de Segurança (ONU)": [
        "United States","United Kingdom","France","Russia","China"
    ],

    "G7": [
        "United States","United Kingdom","France","Germany","Italy","Canada","Japan"
    ],

    "G20": [
        "Argentina","Australia","Brazil","Canada","China","France","Germany","India","Indonesia",
        "Italy","Japan","Mexico","Russia","Saudi Arabia","South Africa","South Korea",
        "Turkey","United Kingdom","United States","European Union"
    ],

    "BRICS": [
        "Brazil","Russia","India","China","South Africa","Egypt","Ethiopia",
        "Iran","Saudi Arabia","United Arab Emirates"
    ]
}
available_countries = paises_all  # já ordenado acima

# Inicializa estado do comparativo uma única vez
if "selected_countries" not in st.session_state:
    st.session_state["selected_countries"] = (
        [selected_country] if selected_country in available_countries else []
    )

# Se o usuário mudar o país principal, garante que ele fique na lista
if selected_country not in st.session_state["selected_countries"]:
    st.session_state["selected_countries"] = natsorted(
        list(set(st.session_state["selected_countries"]) | {selected_country})
    )

# UI de regiões (sem botão extra, atualização automática)
selected_regions = st.sidebar.multiselect(
    "Selecione a região (opcional):",
    options=list(REGION_MAP.keys())
)

# Atualiza lista de países automaticamente
if "None" in selected_regions:
    # Zera e deixa só o país principal
    st.session_state["selected_countries"] = [selected_country]
else:
    to_add = {selected_country}
    for reg in selected_regions:
        for c in REGION_MAP.get(reg, []):
            if c in available_countries:
                to_add.add(c)
    st.session_state["selected_countries"] = natsorted(list(to_add))

# PERÍODO
min_year, max_year = int(df["year"].min()), int(df["year"].max())
year_range = st.sidebar.slider("Intervalo de anos:", min_year, max_year, (min_year, max_year))
st.sidebar.markdown("---")

# ==========================
# 5) SIDEBAR – CLASSE → GRUPO → VARIÁVEL (com preselect por sessão)
# ==========================
def _get_index_or_zero(seq, value):
    try:
        return max(0, seq.index(value))
    except Exception:
        return 0

# Classes (iniciar da 2 em diante)
classes_presentes = natsorted(
    [cid for cid in df_indicadores["classe_id"].dropna().unique().tolist() if int(str(cid).split('.')[0]) >= 2],
    alg=0
)
classe_labels = {cid: f"{cid} - {CLASS_MAP.get(cid, 'Classe desconhecida')}" for cid in classes_presentes}

pre_classe = st.session_state.get("selected_classe_id")
classe_index = _get_index_or_zero(classes_presentes, pre_classe) if pre_classe else 0
selected_classe_id = st.sidebar.selectbox(
    "🔹 Classe",
    classes_presentes,
    format_func=lambda cid: classe_labels[cid],
    index=classe_index
)
st.session_state["selected_classe_id"] = selected_classe_id  # mantém em sessão

# Grupos da classe
grupos_da_classe = natsorted(
    df_indicadores.loc[df_indicadores["classe_id"] == selected_classe_id, "grupo_id"]
    .dropna().unique().tolist(),
    alg=0
)
grupo_labels = {gid: f"{gid} - {GROUP_MAP.get(gid, 'Grupo sem nome (TOC)')}" for gid in grupos_da_classe}

pre_grupo = st.session_state.get("selected_grupo_id")
grupo_index = _get_index_or_zero(grupos_da_classe, pre_grupo) if pre_grupo and pre_grupo in grupos_da_classe else 0
selected_grupo_id = st.sidebar.selectbox(
    "🔹 Grupo",
    grupos_da_classe,
    format_func=lambda gid: grupo_labels[gid],
    index=grupo_index if grupos_da_classe else 0
) if grupos_da_classe else None
if selected_grupo_id:
    st.session_state["selected_grupo_id"] = selected_grupo_id

# Variáveis filtradas por grupo (ou por classe se não houver grupo)
if selected_grupo_id:
    variaveis_filtradas = variaveis[variaveis["grupo_id"] == selected_grupo_id].copy()
else:
    variaveis_filtradas = variaveis[variaveis["classe_id"] == selected_classe_id].copy()

descricao_variaveis = variaveis_filtradas.set_index("variavel")["titulo"].to_dict() if not variaveis_filtradas.empty else {}
variaveis_disponiveis = natsorted(list(descricao_variaveis.keys())) if descricao_variaveis else []

# Pré-seleção de variável (vinda do search)
pre_var1 = st.session_state.pop("graph_var1_from_search", None)
if pre_var1 and pre_var1 in variaveis_disponiveis:
    default_index = variaveis_disponiveis.index(pre_var1)
else:
    default_index = 0 if variaveis_disponiveis else 0

selected_variavel_id = st.sidebar.selectbox(
    "🔹 Variável",
    variaveis_disponiveis if variaveis_disponiveis else ["—"],
    index=default_index if variaveis_disponiveis else 0,
    format_func=lambda v: (
        f"{df_indicadores.loc[df_indicadores['variavel'] == v, 'id'].values[0]} - {v} - {descricao_variaveis.get(v, 'Sem descrição')}"
        if v != "—" and not df_indicadores.loc[df_indicadores['variavel'] == v, 'id'].empty
        else v
    )
) if variaveis_disponiveis else None

if selected_variavel_id:
    st.sidebar.caption(descricao_variaveis.get(selected_variavel_id, "Sem descrição disponível."))

# ==========================
# 6) BUSCA GLOBAL
# ==========================
st.sidebar.markdown("---")
st.sidebar.subheader("🔍 Buscar Variável")
pesquisa = st.sidebar.text_input("Parte do nome ou descrição:")

if pesquisa:
    catalogo_vars = (
        df_indicadores[["id", "titulo", "variavel", "classe_id", "grupo_id"]]
        .dropna(subset=["variavel"])
        .query("variavel in @df.columns")
        .copy()
    )
    mask = (
        catalogo_vars["variavel"].str.contains(pesquisa, case=False, na=False) |
        catalogo_vars["titulo"].str.contains(pesquisa, case=False, na=False) |
        catalogo_vars["id"].str.contains(pesquisa, case=False, na=False)
    )
    resultados = (
        catalogo_vars.loc[mask]
        .drop_duplicates(subset=["variavel"])
        .sort_values(by=["classe_id", "grupo_id", "variavel"])
    )

    if not resultados.empty:
        st.sidebar.caption(
            f"{len(resultados)} variável(is) encontrada(s). "
            "Clique no nome para ver detalhes ou no botão para selecionar."
        )
        for _, row in resultados.iterrows():
            var   = row["variavel"]
            desc  = row["titulo"] or ""
            rid   = str(row["id"])
            rcid  = str(row["classe_id"])
            rgid  = str(row["grupo_id"]) if pd.notna(row["grupo_id"]) else None

            # Linha com duas colunas: nome da variável (expander) e botão
            col1, col2 = st.sidebar.columns([5, 1])
            with col1:
                with st.expander(f"**{var}**", expanded=False):
                    st.caption(f"**ID:** {rid}")
                    st.caption(desc if desc else "Sem descrição.")
            with col2:
                if st.button("📌", key=f"pick_{var}"):
                    st.session_state["selected_classe_id"] = rcid
                    if rgid:
                        st.session_state["selected_grupo_id"] = rgid
                    else:
                        st.session_state.pop("selected_grupo_id", None)
                    st.session_state["graph_var1_from_search"] = var
                    st.rerun()
    else:
        st.sidebar.info("Nenhum resultado na base.")



# ==========================
# 7) GRÁFICO – COMPARAR PAÍSES
# ==========================
titulo_var = df_indicadores.loc[df_indicadores["variavel"] == selected_variavel_id, "titulo"].values
titulo_var = titulo_var[0] if len(titulo_var) > 0 else selected_variavel_id
st.subheader(f" 📈 Série Histórica: {titulo_var}")
st.write(f"Período: **{year_range[0]}–{year_range[1]}**")
paises = st.multiselect(
    "Selecione os países para comparar:",
    available_countries,  # mesma lista usada nas regiões
    default=st.session_state.get("selected_countries", [selected_country]),
    key="country_picker",
)

    # mantém o estado sincronizado caso o usuário ajuste manualmente
if paises != st.session_state.get("selected_countries", []):
    st.session_state["selected_countries"] = paises

if selected_variavel_id:
    if selected_variavel_id not in df.columns:
        st.warning(f"A variável '{selected_variavel_id}' não está na base.")
    else:
        df_plot = df[
            df["country_name"].isin(paises) &
            df["year"].between(year_range[0], year_range[1])
        ][["year", "country_name", selected_variavel_id]].sort_values(["year", "country_name"])
        if not df_plot.empty and pd.api.types.is_numeric_dtype(df[selected_variavel_id]):
            pivot = df_plot.pivot(index="year", columns="country_name", values=selected_variavel_id)
            # --- usa Altair para formatar o eixo dos anos sem vírgula ---
            # prepara dados long (um país por linha) a partir do pivot:
            pivot = df_plot.pivot(index="year", columns="country_name", values=selected_variavel_id).reset_index()
            long_df = pivot.melt(id_vars="year", var_name="country_name", value_name="valor").dropna()
            # define passo de ticks (10 em 10 anos; se período pequeno, usa 5)
            span = max(1, year_range[1] - year_range[0])
            tick_step = 10 if span >= 20 else 5
            tick_vals = list(range(int(year_range[0]), int(year_range[1]) + 1, tick_step))
            chart = (alt.Chart(long_df).mark_line().encode(
                x=alt.X("year:Q", axis=alt.Axis(format="d", values=tick_vals, title="Ano")),
                y=alt.Y("valor:Q", title=titulo_var),
                color=alt.Color("country_name:N", title="País")
            ).properties(width="container", height=420))
            st.altair_chart(chart, use_container_width=True)

        elif not pd.api.types.is_numeric_dtype(df[selected_variavel_id]):
            st.warning("A variável selecionada não é numérica.")
        else:
            st.info("Sem dados para o período/países selecionados.")
else:
    st.info("Selecione uma variável para visualizar o gráfico.")
