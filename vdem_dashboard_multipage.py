# vdem_dashboard.py
import os
import streamlit as st
from streamlit_option_menu import option_menu
import streamlit.components.v1 as components
import numpy as np
import plotly.express as px
from PIL import Image
import pandas as pd
from pathlib import Path
from natsort import natsorted
import random
from math import ceil
import altair as alt

# C:\PROJECTS\.venv10\Scripts\Activate.ps1
# cd C:\PROJECTS\vdem_dashboard
# streamlit run vdem_dashboard_multipage.py --server.runOnSave true

st.set_page_config(layout="wide",
                   page_title="Democracias no Mundo",
                   initial_sidebar_state="collapsed")

# ==========================
# CARREGAR DADOS (cache)
# ==========================
# Use um dir seguro no Cloud (e localmente continua ok)
BASE_DATA_DIR = Path(os.environ.get("STREAMLIT_DATA_DIR", "/mount/data"))
DATA_DIR = BASE_DATA_DIR / "data_cache"
DATA_DIR.mkdir(parents=True, exist_ok=True)

@st.cache_data(show_spinner="Carregando dados do Parquet…")
def load_parquet(path: Path) -> pd.DataFrame:
    return pd.read_parquet(path, engine="fastparquet")

@st.cache_data(show_spinner="Carregando dados do CSV…")
def load_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, sep=",", low_memory=False)

def load_data():
    vdem_path  = Path("vdem_all.parquet")
    indic_path = Path("indicadores_vdem.csv")
    df = load_parquet(vdem_path)
    df_indicadores = load_csv(indic_path)
    return df, df_indicadores

# ==========================
# DADOS
# ==========================
df, df_indicadores = load_data()
# remove estatísticas auxiliares
heads = df.columns.to_list()
head = [c for c in heads if not c.endswith(('_sd', '_osp', '_codelow', '_codehigh', '_ord', '_mean', '_nr'))]


# decompõe id → classe/grupo (compatível com ids 2/3/4 níveis)
df_indicadores["partes"]    = df_indicadores["id"].astype(str).str.split(".")
df_indicadores["classe_id"] = df_indicadores["partes"].apply(lambda p: p[0] if len(p)>=1 else None)
df_indicadores["grupo_id"]  = df_indicadores["partes"].apply(lambda p: ".".join(p[:2]) if len(p)>=2 else None)

df_indicadores["Classe"] = df_indicadores["classe_id"].map(CLASS_MAP)
df_indicadores["Grupo"]  = df_indicadores["grupo_id"].map(GROUP_MAP)

# nível
def define_nivel(p):
    if len(p)==1: return "Classe"
    if len(p)==2: return "Grupo"
    return "Variavel"
df_indicadores["nivel"] = df_indicadores["partes"].apply(define_nivel)

# catálogo final (existentes no df principal)
variaveis = (
    df_indicadores[df_indicadores["nivel"] == "Variavel"]
    .query("variavel in @df.columns")
    .copy()
)

# ==========================
# MAPAS DE CLASSE / GRUPO / REGIÕES
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

REGION_MAP = {
    "None": [],  # None para evitar erro de chave ausente

    "America do Norte & Caribe": [
        "United States of America","Canada","Mexico", "Bahamas","Barbados","Cuba","Dominican Republic",
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
        "Kosovo","Montenegro","North Macedonia","Poland","Romania","Serbia","Belarus","Moldova","Ukraine","Russia", 
        "Latvia","Lithuania","Malta","Cyprus","Estonia"
    ],

    "Ásia (Centro-Sul)": [
        "Afghanistan","Armenia","Azerbaijan","Bangladesh","Bhutan","Georgia","India",
        "Kazakhstan","Kyrgyzstan","Maldives","Nepal","Pakistan","Sri Lanka",
        "Tajikistan","Turkmenistan","Uzbekistan", "Laos", "Thailand", "Cambodia"
    ],

    "Ásia (norte-Leste)": [
        "China","Japan","Mongolia","North Korea","South Korea","Taiwan", "Russia", 
    ],

    "Ásia": [
        "Afghanistan", "Armenia","Azerbaijan","Bahrain","Bangladesh","Bhutan","Brunei","Cambodia",
        "China","Georgia","India","Japan","Kazakhstan", "Kuwait","Kyrgyzstan","Laos","Lebanon", 
        "Maldives","Mongolia","Myanmar","Nepal", "North Korea","Pakistan","Qatar", "Singapore","South Korea", 
        "Thailand", "Sri Lanka","Tajikistan", "Timor-Leste","Turkmenistan", "Uzbekistan","Vietnam", "Russia"
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
        "Palau","Papua New Guinea","Samoa","Solomon Islands","Tonga","Tuvalu","Vanuatu",
        "Malaysia", "Philippines", "Indonesia"
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

# ==========================
# HELPERS
# ==========================
def available_countries(df_):
    return natsorted(df_["country_name"].dropna().unique())

def get_titulo_by_var(var_name: str) -> str:
    vals = df_indicadores.loc[df_indicadores["variavel"] == var_name, "titulo"].values
    return vals[0] if len(vals)>0 else var_name

def get_id_by_var(var_name: str) -> str:
    vals = df_indicadores.loc[df_indicadores["variavel"] == var_name, "id"].values
    return vals[0] if len(vals)>0 else ""

def filtro_variaveis_por_grupo_robusto(dfv, selected_grupo_id, selected_classe_id):
    """Inclui variáveis de subgrupos (ids com 3º dígito como subgrupo)."""
    if selected_grupo_id:
        prefix = f"{selected_grupo_id}."
        return dfv[dfv["id"].str.startswith(prefix)].copy()
    return dfv[dfv["classe_id"] == selected_classe_id].copy()

def pick_default_var(df: pd.DataFrame) -> str:
    # prioriza variáveis "canônicas" de democracia; cai para a 1ª numérica se preciso
    prefs = ["v2x_libdem", "v2x_polyarchy", "e_v2x_polyarchy", "v2x_liberal"]
    for v in prefs:
        if v in df.columns and pd.api.types.is_numeric_dtype(df[v]):
            return v
    # fallback: primeira coluna numérica diferente de year
    for c in df.columns:
        if c != "year" and pd.api.types.is_numeric_dtype(df[c]):
            return c
    return None

def numeric_candidates(df: pd.DataFrame) -> list[str]:
    bad_suffix = ("_sd","_osp","_codelow","_codehigh","_ord","_mean","_nr")
    out = []
    for c in df.columns:
        if c == "year": 
            continue
        if any(c.endswith(s) for s in bad_suffix):
            continue
        if pd.api.types.is_numeric_dtype(df[c]):
            out.append(c)
    return sorted(out)

def generate_colors(n, seed=52):
    # Gera uma lista de cores HSL alternando saturação/claridade
    rng = random.Random(seed)

    # Cores base (hues aproximados em graus no círculo HSL)
    base_hues = [
        0,    # Vermelho
        240,  # Azul
        120,  # Verde
        30,   # Laranja
        59,   # Amarelo
        280   # Roxo
    ]

    vivid = [f"hsl({h}, 70%, 50%)" for h in base_hues]       # versões saturadas
    pastel = [f"hsl({h}, 40%, 70%)" for h in base_hues]      # versões pastéis

    # Intercalar saturado e pastel
    colors = []
    for v, p in zip(vivid, pastel):
        colors.append(v)
        colors.append(p)

    # Se precisar de mais que 12, repetir ciclo com variações de matiz
    extra_needed = n - len(colors)
    i = 0
    while extra_needed > 0:
        h = base_hues[i % len(base_hues)]
        jitter = rng.randint(-30, 30)  # pequena variação de hue
        if extra_needed % 2 == 0:
            colors.append(f"hsl({(h + jitter) % 360}, 75%, 52%)")  # versão saturada
        else:
            colors.append(f"hsl({(h + jitter) % 360}, 38%, 70%)")  # versão pastel
        i += 1
        extra_needed -= 1
    
    # Mantém as 2 primeiras fixas e embaralha o resto
    fixed = colors[:1]
    shuffled = colors[1:]
    rng.shuffle(shuffled)

    final_colors = fixed + shuffled

    return final_colors[:n]

def _safe_image(path, **kwargs):
    """Renderiza imagem se existir; caso contrário, mostra aviso."""
    p = Path(path)
    if p.exists():
        st.image(str(p), **kwargs)
    else:
        st.warning(f"Imagem não encontrada: `{p}`")

def _html_tabela_resultados() -> str:
    """Tabela HTML compacta (scroll, cabeçalho/1ª coluna fixos) baseada na Tabela 3."""
    return """
<style>
/* Container com rolagem e limite de altura/largura */
.table-wrap {
  max-height: 580px;           /* ajuste conforme a tela */
  overflow: off;              /* scroll x e y quando necessário */
  border: 1px solid #e6e6e6;
  border-radius: 6px;
  box-shadow: 0 0 0 1px rgba(0,0,0,0.02) inset;
}

/* Tabela compacta */
.table-res {
  width: 100%;
  border-collapse: separate;   /* permite sticky + espaçamento fino */
  border-spacing: 0;
  font-size: 14px;             /* fonte menor */
  line-height: 1;           /* altura compacta */
  table-layout: fixed;         /* colunas mais previsíveis */
  min-width: 580px;            /* garante espaço p/ ver tudo; ajustável */
}

/* Células */
.table-res th,
.table-res td {
  border-bottom: 1px solid #eee;
  padding: 4px 6px;            /* padding reduzido */
  text-align: center;
  white-space: nowrap;         /* números não quebram linha */
}

/* Primeira coluna: à esquerda e sticky */
.table-res td:first-child,
.table-res th:first-child {
  text-align: left;
  position: sticky;
  left: 0;
  z-index: 1;
  background: #fff;            /* fundo para sobrepor ao scroll */
}

/* Cabeçalho sticky */
.table-res thead th {
  position: sticky;
  top: 0;
  z-index: 2;
  background: #f8f9fb;
  font-weight: 600;
  border-bottom: 1px solid #ddd;
}

/* Subtítulos de seção (linhas com colspan) */
.table-res td[colspan="5"] {
  background: #fafafa;
  font-weight: 600;
  text-align: left !important;
}

/* Notas menores */
.note {
  font-size: 11px;
  color: #666;
  margin-top: 6px;
}

/* Truque para simular '—' branco do LaTeX */
.small { color: #fff; }

/* Superscripts menores */
.table-res sup { font-size: 11px; }

/* Colunas mais estreitas para (0)/(1) */
.col-narrow { width: 52px; }
</style>

<div class="table-wrap">
<table class="table-res">
  <colgroup>
    <col style="width: 34%;">
    <col class="col-narrow">
    <col>
    <col>
    <col>
  </colgroup>
  <thead>
    <tr>
      <th></th>
      <th></th>
      <th>eregress (1)</th>
      <th>eteffects (2)</th>
      <th>etregress (3)</th>
    </tr>
  </thead>
  <tbody>
    <tr><td colspan="2"><b>ATE</b></td><td><span class="small">-</span> 0,041804<sup>***</sup></td><td><span class="small">-</span> 0,062732<sup>***</sup></td><td><span class="small">-</span> 0,042014<sup>***</sup></td></tr>
    <tr><td colspan="2"><b>ATET</b></td><td><span class="small">-</span> 0,068997<sup>***</sup></td><td><span class="small">-</span> 0,087615<sup>***</sup></td><td><span class="small">-</span> 0,075839<sup>***</sup></td></tr>

    <tr><td colspan="5"><i><b>Índice de Democracia</b></i></td></tr>
    <tr><td>Renda per capita (gdppc)</td><td>(0)</td><td><span class="small">-</span> 0,009985<sup>***</sup></td><td><span class="small">-</span> 0,009507<sup>***</sup></td><td></td></tr>
    <tr><td></td><td>(1)</td><td><span class="small">-</span> 0,013508<sup>***</sup></td><td><span class="small">-</span> 0,013685<sup>***</sup></td><td><span class="small">-</span> 0,011899<sup>***</sup></td></tr>

    <tr><td>Anos de educação (educ)</td><td>(0)</td><td><span class="small">-</span> 0,043590<sup>***</sup></td><td><span class="small">-</span> 0,045000<sup>***</sup></td><td></td></tr>
    <tr><td></td><td>(1)</td><td><span class="small">-</span> 0,026653<sup>***</sup></td><td><span class="small">-</span> 0,026168<sup>***</sup></td><td><span class="small">-</span> 0,035569<sup>***</sup></td></tr>

    <tr><td>Guerra interestadual (war)</td><td>(0)</td><td>- 0,039245<sup>***</sup></td><td>- 0,037337<sup>***</sup></td><td></td></tr>
    <tr><td></td><td>(1)</td><td>- 0,041890<sup>*</sup></td><td>- 0,040993<sup>*</sup></td><td>- 0,040279<sup>*</sup></td></tr>

    <tr><td>Guerra civil (civil_war)</td><td>(0)</td><td>- 0,044039<sup>***</sup></td><td>- 0,042186<sup>***</sup></td><td></td></tr>
    <tr><td></td><td>(1)</td><td>- 0,065053<sup>***</sup></td><td>- 0,068302<sup>***</sup></td><td>- 0,058091<sup>***</sup></td></tr>

    <tr><td><i>Spillover</i> Democracia (reg_dem)</td><td>(0)</td><td><span class="small">-</span> 0,113009<sup>***</sup></td><td><span class="small">-</span> 0,132020<sup>***</sup></td><td></td></tr>
    <tr><td></td><td>(1)</td><td> 0,234143<sup>***</sup></td><td><span class="small">-</span> 0,252095<sup>***</sup></td><td><span class="small">-</span> 0,168378<sup>***</sup></td></tr>

    <tr><td>Membro da ONU (UN)</td><td>(0)</td><td>- 0,040620<sup>***</sup></td><td></td><td></td></tr>
    <tr><td></td><td>(1)</td><td><span class="small">-</span> 0,025383<sup>***</sup></td><td><span class="small">-</span> 0,041952<sup>***</sup></td><td></td></tr>

    <tr><td colspan="5"><i><b>Adesão à ONU</b></i></td></tr>
    <tr><td>Histórico colônial (colonized)</td><td></td><td><span class="small">-</span> 0,755868<sup>***</sup></td><td><span class="small">-</span> 0,730257<sup>***</sup></td><td><span class="small">-</span> 0,742427<sup>***</sup></td></tr>

    <tr><td>Fronteira c/ membro do CS (board)</td><td></td><td>- 0,322051<sup>***</sup></td><td>- 0,302819<sup>***</sup></td><td>- 0,311445<sup>***</sup></td></tr>

    <tr><td>Distância até a ONU (dist)</td><td></td><td><span class="small">-</span> 0,101256<sup>***</sup></td><td><span class="small">-</span> 0,100216<sup>***</sup></td><td><span class="small">-</span> 0,101836<sup>***</sup></td></tr>

    <tr><td>Guerra interestadual (war)</td><td></td><td>- 0,326579<sup>***</sup></td><td>- 0,341368<sup>***</sup></td><td>- 0,333000<sup>***</sup></td></tr>

    <tr><td>Guerra civil (civil_war)</td><td></td><td><span class="small">-</span> 0,163435<sup>***</sup></td><td><span class="small">-</span> 0,200093<sup>***</sup></td><td><span class="small">-</span> 0,168826<sup>***</sup></td></tr>

    <tr><td><b>Nº de Observações</b></td><td></td><td>8.753</td><td>8.753</td><td>8.753</td></tr>
  </tbody>
</table>
</div>

<div class="note">
  Nota: Níveis de significância — * p &lt; 0,10; ** p &lt; 0,05; *** p &lt; 0,01.
</div>
"""
def build_common_sidebar(enable_sidebar: bool = True):
    # Se a página quiser esconder a sidebar, apenas retorne None e não construa UI
    if not enable_sidebar:
        return None

    with st.sidebar:
        st.header("Filtros")

        # País (pré-seleção Brazil se existir)
        paises_all = natsorted(df["country_name"].dropna().unique())
        default_index = paises_all.index("Brazil") if "Brazil" in paises_all else 0
        selected_country = st.selectbox("Selecione um país:", paises_all, index=default_index)

        # Lista de países disponíveis (aqui é global, então usamos todos)
        available_countries = paises_all

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

        # Regiões (garanta que REGION_MAP tenha a chave "None": [])
        selected_regions = st.multiselect(
            "Selecione a região (opcional):",
            options=list(REGION_MAP.keys())
        )

        # Atualiza lista de países automaticamente
        if "None" in selected_regions:
            # Zera e deixa só o país principal
            selected_countries = [selected_country]
        else:
            to_add = {selected_country}
            for reg in selected_regions:
                for c in REGION_MAP.get(reg, []):
                    if c in available_countries:
                        to_add.add(c)
            selected_countries = natsorted(list(to_add))

        # Grava no estado e usa esse mesmo valor daqui pra frente
        st.session_state["selected_countries"] = selected_countries

        # PERÍODO
        min_year, max_year = int(df["year"].min()), int(df["year"].max())
        year_range = st.slider("Intervalo de anos:", min_year, max_year, (min_year, max_year))
        st.markdown("---")

        # UI DE VARIÁVEIS (Visualização dos Dados)
        # Classes (iniciar da 2 em diante)
        classes_presentes = natsorted(
            [cid for cid in df_indicadores["classe_id"].dropna().unique().tolist() if int(str(cid).split('.')[0]) >= 2],
            alg=0
        )
        classe_labels = {cid: f"{cid} - {CLASS_MAP.get(cid, 'Classe desconhecida')}" for cid in classes_presentes}

        pre_classe = st.session_state.get("selected_classe_id")
        classe_index = classes_presentes.index(pre_classe) if pre_classe in classes_presentes else 0
        selected_classe_id = st.selectbox(
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
        grupo_index = grupos_da_classe.index(pre_grupo) if pre_grupo in grupos_da_classe else 0
        selected_grupo_id = st.selectbox(
            "🔹 Grupo",
            grupos_da_classe if grupos_da_classe else ["—"],
            format_func=lambda gid: grupo_labels.get(gid, gid),
            index=(grupo_index if grupos_da_classe else 0)
        ) if grupos_da_classe else None

        if selected_grupo_id:
            st.session_state["selected_grupo_id"] = selected_grupo_id
        else:
            st.session_state.pop("selected_grupo_id", None)

        # Variáveis filtradas por grupo (ou por classe se não houver grupo)
        if selected_grupo_id:
            variaveis_filtradas = variaveis[variaveis["grupo_id"] == selected_grupo_id].copy()
        else:
            variaveis_filtradas = variaveis[variaveis["classe_id"] == selected_classe_id].copy()

        descricao_variaveis = (
            variaveis_filtradas.set_index("variavel")["titulo"].to_dict()
            if not variaveis_filtradas.empty else {}
        )
        variaveis_disponiveis = natsorted(list(descricao_variaveis.keys())) if descricao_variaveis else []

        # Pré-seleção de variável (vinda do search)
        pre_var1 = st.session_state.pop("graph_var1_from_search", None)
        if pre_var1 and pre_var1 in variaveis_disponiveis:
            var_index = variaveis_disponiveis.index(pre_var1)
        else:
            var_index = 0 if variaveis_disponiveis else 0

        selected_variavel_id = st.selectbox(
            "🔹 Variável",
            variaveis_disponiveis if variaveis_disponiveis else ["—"],
            index=(var_index if variaveis_disponiveis else 0),
            format_func=lambda v: (
                f"{df_indicadores.loc[df_indicadores['variavel'] == v, 'id'].values[0]} - {v} - {descricao_variaveis.get(v, 'Sem descrição')}"
                if v != "—" and not df_indicadores.loc[df_indicadores['variavel'] == v, 'id'].empty
                else v
            )
        ) if variaveis_disponiveis else None

        if selected_variavel_id:
            st.caption(descricao_variaveis.get(selected_variavel_id, "Sem descrição disponível."))

     # ====== BUSCA GLOBAL (ID / VARIÁVEL / TÍTULO) ======
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

    # Retorna TUDO que a página precisa usar
    return {
        "df": df,
        "df_indicadores": df_indicadores,
        "year_range": year_range,
        "selected_country": selected_country,
        "available_countries": available_countries,
        "selected_countries": selected_countries,
        "selected_variavel_id": selected_variavel_id,
    }

# ==========================
# PÁGINAS (funções)
# ==========================
def render_home(
    img_graph1="vdem_dashboard\graph1.png",  # Evolução da Democracia
    img_graph2="vdem_dashboard\graph2.png",  # Evolução da Renda e Educação
    img_graph3="vdem_dashboard\graph3.png",  # Adesão à ONU
    img_graph4="vdem_dashboard\graph4a.png",  # Nº de países observados
    img_table1="vdem_dashboard\table1.png",  # Tabela de Resultados (Table 3 do paper)
    img_scatter_regional="vdem_dashboard\graph5a.png"  # Dispersão Regional (wrapfigure no paper)
):
    st.title("O Papel da ONU na Democratização")
    st.caption("Sumário do estudo, estratégia causal e principais resultados")
    st.info("Acesse o paper completo [aqui](https://www.dropbox.com/scl/fi/g31ub00hgskpz9grwm28l/O-Papel-das-Na-es-Unidas-na-Democratiza-o_Identificado.pdf?rlkey=dvlmpjqm074kygbuebi4m64hb&st=fbyl0mct&dl=0)")

    st.markdown("""

### Resumo
<div style='text-align: justify;'>
                
 Este estudo analisa o impacto da adesão às Nações Unidas (ONU) na democratização de 128 países entre 1820 e 2000, utilizando modelos de 
efeito de tratamento endógeno. Os resultados indicam que ser membro da ONU aumenta o índice de democracia liberal entre 4,2% e 6,2% (ATE), 
chegando a 8,7% entre os membrs (ATET). Fatores internos, como escolaridade média e renda per capita, também influenciam positivamente, enquanto 
conflitos militares e guerras civis reduzem os níveis democráticos. O estudo contribui para a literatura ao quantificar a influência da
 ONU na difusão de valores democráticos e ao integrar variáveis socioeconômicas, geopolíticas e institucionais na compreensão do processo de democratização global.
</div>             

### Estratégia de Identificação (Efeitos de Tratamento Endógeno)
<div style='text-align: justify;'>
                
 Para estimar o efeito causal da adesão à Organização das Nações Unidas (ONU) sobre o nível
 de democracia dos países, assumimos a hipótese central de que o ingresso formal na ONU induz
 mudanças institucionais positivas ao conectar os países a mecanismos de cooperação multilateral,
 assistência técnica, suporte institucional e monitoramento eleitoral, promovendo, assim, maior
 estabilidade institucional e accountability política. No entanto, como a adesão à ONU não é
 aleatória, é necessário aplicar estratégias de identificação que permitam isolar o impacto dessa
 adesão de fatores internos que também influenciam a trajetória democrática.
                
A abordagem baseada em modelos de efeitos de tratamento endógeno considera a adesão à ONU como um tratamento com impacto
 sobre as instituições nacionais. Essa abordagem permite estimar o efeito causal da ONU mesmo quando a decisão de adesão
 não é aleatória. Para corrigir o viés de autosseleção e a endogeneidade do tratamento, utilizamos variáveis instrumentais
 geográficas e históricas, que afetam a probabilidade de adesão à ONU, mas não têm efeito direto sobre a democracia.
</div>
    """,
    unsafe_allow_html=True
    )
    st.latex(r"""
\begin{align}
UN^*_{it} = \alpha_0 + \alpha_1 \text{colonized}_i + \alpha_2 \text{board}_i + \alpha_3 \text{dist}_i + \alpha_4 \text{war}_{it-1} + \alpha_5 \text{civil\_war}_{it-1} + u_i \
\end{align}
\\         
\begin{align}
dem_{jit} = \beta_0 + \beta_1 \text{UN}_{it-1} + \beta_2 \text{gdppc}_{it-1} + \beta_3 \text{educ}_{it-1} + \beta_4 \text{war}_{it-1} + \beta_5 \text{civil\_war}_{it-1} + \beta_6 \text{reg\_dem}_{it-1} + \varepsilon_{jit} \
\end{align}
""")
    st.markdown(r"""
onde:
                
- $$ dem_{jit} $$: é o resultado observado do Índice de Democracia Liberal ($v2x\_libdem$), para o país $i$, no ano $t$ e grupo $j$ – sendo $j=0$ o grupo de controle e $j=1$ o grupo tratado;
- $$ UN^*_{it} $$: representa a propensão não observada do país $i$ tornar-se membro da ONU no ano $t$ (Variável Latente);
- $$ UN_{it} $$: é a variável binária do tratamento, que assume valor 1 se $UN^*_{it} > 0$ ou valor 0 se $UN^*_{it} \leq 0$;
- $$ reg\_dem_{it}: $$: representa a média regional de democracia;
- $$ gdppc_{it} $$: representa o Produto Interno Bruto *per capita* ajustado pelo poder de paridade de compra (*Purchasing Power Parity - PPP*) em dólares de 2014;
- $$ educ_{it} $$: é a média de anos de educação para maiores de 15 anos;
- $$ war_{it} $$: indica a ocorrência de guerra internacional do país $i$ com qualquer outro país no ano $t$;
- $$ civil\_war_{it} $$: indica a ocorrência de guerra civil do país $i$ no ano $t$;
- $$ colonized_i $$: indica se o país foi colônia em algum momento;
- $$ board_i $$: identifica se o país compartilha fronteira terrestre com ao menos um dos membros permanentes do Conselho de Segurança da ONU;
- $$ dist_i $$: mede a distância (em mil quilômetros) entre a capital do país, no ano de adesão, e a sede da ONU em Nova York, Estados Unidos
""")

    # -----------------------------
    # Figuras 1 a 4 — Lado a lado
    # -----------------------------
    st.markdown(
        """
### Principais Resultados

**Modernização institucional e socioeconômica**
- O processo de institucionalização internacional caminhou em paralelo a avanços no desenvolvimento humano.
- Houve crescimento conjunto da democracia (**Figura 1**), da renda per capita e da educação média (**Figura 2**).
- Esses padrões sugerem trajetórias de modernização interligadas entre o plano institucional e o socioeconômico.

**Expansão da ONU e dados internacionais**
- Aumento expressivo no número de países observados nas bases de dados a partir de 1900 (**Figura 3**), associado à criação do Instituto Internacional de Estatística (1885).
- Estrutura fortalecida posteriormente por organismos como ONU e Banco Mundial, promovendo padronização e comparabilidade de dados globais.
- Crescimento acelerado de membros da ONU após 1945 (**Figura 4**), impulsionado pela descolonização e pela consolidação do sistema internacional no pós-guerra.

        """,
        unsafe_allow_html=True
    )
    # Figuras
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.caption("Figura 1 — Evolução da Democracia")
        _safe_image(img_graph1, use_container_width=True)
    with c2:
        st.caption("Figura 2 — Evolução da Renda e Educação")
        _safe_image(img_graph2, use_container_width=True)
    with c3:
        st.caption("Figura 3 — Nº de Países Observados")
        _safe_image(img_graph4, use_container_width=True)
    with c4:
        st.caption("Figura 4 — Adesão à ONU")
        _safe_image(img_graph3, use_container_width=True)


    col1, col2 = st.columns([1.25, 1])
    with col1:
        st.markdown(
        """
**Determinantes internos (modernização)**
- **Renda per capita:** +US$ 1.000 → +0,9% a +1,3% no índice de democracia.
- **Educação:** +1 ano de escolaridade média → +2,6% a +4,5% na democracia.
- Indica que desenvolvimento econômico e educacional fortalece instituições e valores democráticos.

**Conflitos e adesão à ONU**
- **Guerras civis:** reduzem democracia (até –6,5%), mas aumentam probabilidade de adesão à ONU (busca de legitimidade, apoio externo e mediação).
- **Conflitos internacionais:** reduzem democracia e dificultam ingresso na ONU (possibilidade de veto no Conselho de
Segurança das Nações Unidas).

**Distância do país à sede da ONU**
- Relação positiva com adesão (não esperado).
- Países mais distantes, especialmente no Sul Global, podem buscar a ONU como canal de recursos estratégicos, ajuda e cooperação.
- Achado exige investigação futura para verificar se países do Sul Global de fato tem maior probabilidade de ingressarem na ONU mais cedo.

**Variáveis instrumentais e fatores de adesão à ONU**
- **Histórico colonial:** ser ex-colônia aumenta fortemente a chance de adesão (busca de reconhecimento internacional).
- **Distância à sede da ONU:** efeito positivo inesperado (integração e acesso a recursos).
- **Fronteira com membros do CSNU:** reduz a probabilidade de ingresso (pressões geopolíticas e rivalidades regionais).
        """,
        unsafe_allow_html=True
    )
    with col2:
        # Tabela de Resultados
        st.caption("Tabela 1 — Resultado das Estimações")
        html = _html_tabela_resultados()
        components.html(html, height=620, width=720, scrolling=True)


    col1, col2 = st.columns([1.25, 1])
    with col1:
        st.markdown(
        """
**Spillover regional de democracia**
- A média regional de democracia reflete em até 25% da composição do índice de um país membro da ONU.
- Sugere difusão institucional regional, reforçada por contextos democráticos vizinhos.
- Diferenças significativa entre regiões, com destaque para a Europa, América do Norte e Caribe e América Latina
 como regiões com maiores índices médios, em contraste com África, Ásia e Oriente Médio.
- Necessidade de análises aprofundadas para captar variações históricas e geopolíticas associados à difusão democrática.


### Conclusão
<div style='text-align: justify;'>
Em síntese, o estudo oferece evidências do papel significativo da ONU como catalisadora de avanços democráticos,
 com efeito médio positivo e robusto sobre o índice de democracia, ao mesmo tempo em que reforça a importância de
 fatores internos como renda per capita e anos de escolaridade, em linha com a teoria da modernização de Lipset (1959). 
 Esses achados não apenas corroboram a literatura, mas ampliam a compreensão sobre as interações entre crescimento econômico,
 democracia e engajamento internacional, apontando a necessidade de pesquisas futuras sobre o papel da localização
 geográfica e do envolvimento efetivo dos países nas instâncias multilaterais.
 </div>
        """,
        unsafe_allow_html=True
    )
    with col2:
    # Figura
        st.caption("Figura 5 — Dispersão Regional da Democracia")
        _safe_image(img_scatter_regional, use_container_width=False)

    st.markdown("""
### Referências
<div style='text-align: justify;'>
<p><b>Acemoglu, D.; Robinson, J. A.</b> <i>Why nations fail: the origins of power, prosperity, and poverty</i>. Nova York: Crown Publishers, 2012.</p>

<p><b>Acemoglu, D.; Johnson, S.; Robinson, J. A.</b> <i>The colonial origins of comparative development: an empirical investigation.</i> American Economic Review, v. 91, n. 5, p. 1369–1401, 2001.</p>

<p><b>Barro, R. J.</b> <i>Determinants of democracy.</i> Journal of Political Economy, v. 107, n. 6/2, p. 158–183, 1999.</p>

<p><b>Boutros-Ghali, B.</b> <i>An agenda for peace: preventive diplomacy, peacemaking and peace-keeping</i>. New York: United Nations, 1992.</p>

<p><b>Cameron, A. C.; Trivedi, P. K.</b> <i>Microeconometrics: methods and applications</i>. New York: Cambridge University Press, 2005.</p>

<p><b>Collier, P. et al.</b> <i>Breaking the conflict trap: civil war and development policy</i>. Washington, DC: World Bank, 2003.</p>

<p><b>Coppedge, M. et al.</b> <i>International influence: the hidden dimension.</i> Varieties of Democracy Institute, Working Paper n. 119, 2021.</p>

<p><b>Fittipaldi, R. B. G.; Araújo, C. M.; Costa, S. F.</b> <i>Crescimento econômico, democracia e instituições: quais as evidências dessas relações causais na América Latina?</i> Revista de Sociologia e Política, v. 25, n. 62, p. 115–129, 2017.</p>

<p><b>Keshk, O. M. G.</b> <i>Simultaneous equations models: what are they and how are they estimated.</i> Program in Statistics and Methodology, Department of Political Science, Ohio State University, 2003.</p>                

<p><b>Lipset, S. M.</b> <i>Some social requisites of democracy: economic development and political legitimacy.</i> American Political Science Review, v. 53, n. 1, p. 69–105, 1959.</p>

<p><b>StataCorp.</b> <i>Stata 18 - Causal Inference and Treatment-Effects Estimation Reference Manual: eteffects.</i> College Station, TX: Stata Press, 2023. p. 92–113.</p>

</div>          
<!-- você pode continuar inserindo os demais itens no mesmo padrão -->

                
    """,
    unsafe_allow_html=True)

# Pequenos destaques visuais
#    st.success("Resumo: a adesão à ONU está associada a aumentos de democracia, sobretudo em países mais pobres e em contextos regionais democráticos.")


def render_serie_historica():
    # Constrói a sidebar e captura os valores
    sidebar = build_common_sidebar(enable_sidebar=True)
    if sidebar is None:
        st.error("Sidebar não construída — verifique o parâmetro enable_sidebar.")
        return

    sel_var      = sidebar["selected_variavel_id"]
    sel_year_r   = sidebar["year_range"]
    main_country = sidebar["selected_country"]
    all_options  = sidebar["available_countries"]
    paises       = st.multiselect(
        "Selecione os países para comparar:",
        options=all_options,
        default=[c for c in st.session_state.get("selected_countries", [main_country]) if c in all_options],
        key="country_picker",
    )

    # Garante que o país principal fique como 1º na legenda/cores
    paises_ordenados = [c for c in [main_country] + [p for p in paises if p != main_country] if c in all_options]

    # Sincroniza estado se usuário mudou manualmente
    if paises != st.session_state.get("selected_countries", []):
        st.session_state["selected_countries"] = paises

    # Título da variável
    if sel_var:
        titulo_var = df_indicadores.loc[df_indicadores["variavel"] == sel_var, "titulo"].values
        titulo_var = titulo_var[0] if len(titulo_var) > 0 else sel_var
    else:
        titulo_var = "—"

    st.subheader(f" 📈 Série Histórica: {titulo_var}")
    st.write(f"Período: **{sel_year_r[0]}–{sel_year_r[1]}**")

    # Plot
    if sel_var:
        if sel_var not in df.columns:
            st.warning(f"A variável '{sel_var}' não está na base.")
            return

        df_plot = (
            df[df["country_name"].isin(paises) & df["year"].between(sel_year_r[0], sel_year_r[1])]
            [["year", "country_name", sel_var]]
            .sort_values(["year", "country_name"])
        )

        if df_plot.empty:
            st.info("Sem dados para o período/países selecionados.")
            return

        if not pd.api.types.is_numeric_dtype(df[sel_var]):
            st.warning("A variável selecionada não é numérica.")
            return

        # prepara dados long
        pivot = df_plot.pivot(index="year", columns="country_name", values=sel_var).reset_index()
        long_df = pivot.melt(id_vars="year", var_name="country_name", value_name="valor").dropna()
        num_paises = long_df["country_name"].nunique()

        # Ticks do eixo X
        span = max(1, sel_year_r[1] - sel_year_r[0])
        tick_step = 10 if span >= 20 else 5
        tick_vals = list(range(int(sel_year_r[0]), int(sel_year_r[1]) + 1, tick_step))

        # Cores — assegura 1ª cor para o país principal
        base_colors = generate_colors(num_paises, seed=52)
        # Reordena cores para bater com paises_ordenados
        # (mantém 1ª cor para main_country)
        legend_order = paises_ordenados
        color_map = dict(zip(legend_order, base_colors[:len(legend_order)]))

        chart = (
            alt.Chart(long_df)
            .mark_line()
            .encode(
                x=alt.X("year:Q", axis=alt.Axis(format="d", values=tick_vals, title="Ano")),
                y=alt.Y("valor:Q", title=titulo_var),
                color=alt.Color(
                    "country_name:N",
                    title="País",
                    sort=legend_order,
                    scale=alt.Scale(domain=list(color_map.keys()), range=list(color_map.values()))
                )
            )
            .properties(width="container", height=420)
        )
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("Selecione uma variável para visualizar o gráfico.")
            

def render_mapas(ctx: dict):
    """
    Página 'Mapas & GIF' reaproveitando o estado/variáveis da sidebar comum.
    ctx deve ser o dict retornado por build_common_sidebar(enable_sidebar=True).
    Espera chaves: df, df_indicadores, year_range, selected_country, selected_variavel_id
    E usa st.session_state["selected_countries"] para países selecionados.
    """
    df                = ctx["df"]
    df_indicadores    = ctx["df_indicadores"]
    year_range        = ctx["year_range"]
    selected_var      = ctx["selected_variavel_id"]
    selected_country  = ctx["selected_country"]
    selected_countries = st.session_state.get("selected_countries", [selected_country])

    st.title("🗺️ Mapa Interativo")
    # ==============================
    # Checagens de variável e período
    # ==============================
    if not selected_var:
        st.warning("Selecione uma variável na sidebar para visualizar o mapa.")
        return
    if selected_var not in df.columns:
        st.error(f"A variável selecionada (‘{selected_var}’) não existe na base.")
        return

    # Nome/título “bonito” da variável
    titulo_var = df_indicadores.loc[df_indicadores["variavel"] == selected_var, "titulo"].values
    titulo_var = titulo_var[0] if len(titulo_var) > 0 else selected_var

    # ==============================
    # Controles locais da página de mapas
    # ==============================
    c1, c2, c3 = st.columns([1.2, 1, 1])
    with c1:
        modo_agg = st.selectbox(
            "Agregação no período selecionado:",
            ["Média", "Mediana", "Último ano do período"]
        )
    with c2:
        animar = st.checkbox("🎬 Animação por ano", value=False, help="Exibe o mapa ano a ano no período selecionado.")
    with c3:
        show_only_selected = st.checkbox("Filtrar países selecionados", value=False,
                                         help="Se marcado, mostra apenas os países escolhidos na sidebar.")

    # ==============================
    # Filtra dados do período e (opcionalmente) países selecionados
    # ==============================
    mask_periodo = df["year"].between(year_range[0], year_range[1])
    dff = df.loc[mask_periodo, ["country_name", "year", selected_var]].copy()

    if show_only_selected and len(selected_countries) > 0:
        dff = dff[dff["country_name"].isin(selected_countries)]

    # ==============================
    # Construção do DataFrame de mapa
    # ==============================
    if animar:
        # Mapa animado: um frame por ano dentro do período
        # (se desejar reduzir frames, pode amostrar anos aqui)
        df_map = dff.dropna(subset=[selected_var]).copy()
        # Mantém apenas linhas com valores numéricos
        if not pd.api.types.is_numeric_dtype(df[selected_var]):
            st.warning("A variável selecionada não é numérica — impossível mapear.")
            return

        # Escala contínua vermelho→azul (RdBu com reverso=True dá vermelho=baixa; azul=alta)
        fig = px.choropleth(
            df_map,
            locations="country_name",
            locationmode="country names",
            color=selected_var,
            hover_name="country_name",
            animation_frame="year",
            color_continuous_scale="RdBu",
            range_color=(float(df_map[selected_var].min()), float(df_map[selected_var].max())),
            title=f"{titulo_var} — {year_range[0]}–{year_range[1]} (animação)"
        )
        fig.update_layout(
            margin=dict(l=0, r=0, t=40, b=0),
            updatemenus=[{
                "buttons": [
                    {"args": [None, {"frame": {"duration": 100, "redraw": True}, "fromcurrent": True}],
                    "label": "Play", "method": "animate"},
                    {"args": [[None], {"frame": {"duration": 0, "redraw": True}, "mode": "immediate"}],
                    "label": "Pause", "method": "animate"}
                ],
                "type": "buttons"
            }]
        )
        st.plotly_chart(fig, use_container_width=True)

    else:
        # Mapa estático: agrega por país dentro do período
        if not pd.api.types.is_numeric_dtype(df[selected_var]):
            st.warning("A variável selecionada não é numérica — impossível mapear.")
            return
        
        if modo_agg == "Média":
            df_map = dff.groupby("country_name", as_index=False)[selected_var].mean()
        elif modo_agg == "Mediana":
            df_map = dff.groupby("country_name", as_index=False)[selected_var].median()
        else:  # "Último ano do período"
            last_year = year_range[1]
            df_map = dff[dff["year"] == last_year].dropna(subset=[selected_var]).copy()

        if df_map.empty:
            st.info("Sem dados para o período/seleção atual.")
            return
        fig = px.choropleth(
            df_map,
            locations="country_name",
            locationmode="country names",
            color=selected_var,
            hover_name="country_name",
            color_continuous_scale="RdBu",  # vermelho (baixo) → azul (alto)
            range_color=(float(df_map[selected_var].min()), float(df_map[selected_var].max())),
            title=f"{titulo_var} — {modo_agg} ({year_range[0]}–{year_range[1]})"
        )
        fig.update_layout(margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig, use_container_width=True)

    # ==============================
    # Notas e tips
    # ==============================
    st.caption(
        "Dica: use a mesma sidebar da Série Histórica para trocar **país**, **período** e **variável**. "
        "Ative a animação para ver a evolução ano a ano."
    )

 
# ==========================
# CONFIG / TÍTULO
# ==========================
# ---- NAV BAR (topo) ----
selected = option_menu(
    None,
    ["Apresentação","Série Histórica","Mapa VDEM"],
    icons=["house","graph-up","map"],
    menu_icon="cast",
    default_index=0,
    orientation="horizontal",
    styles={
        "container": {"padding": "0!important", "background-color": "white",
                      "position": "sticky", "top": "0", "z-index": "1000"},
        "nav-link": {"padding":"0.5rem 1rem", "font-size":"0.9rem"},
        "nav-link-selected": {"background-color":"#656668"}
    }
)

# ---- Conteúdo + filtros específicos por página ----
if selected == "Apresentação":
    render_home()
elif selected == "Série Histórica":
    render_serie_historica()
elif selected == "Mapa VDEM":
    ctx = build_common_sidebar(enable_sidebar=True)
    render_mapas(ctx)
# …e assim por diante…
