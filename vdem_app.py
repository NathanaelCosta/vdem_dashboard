import streamlit as st
import pandas as pd
import time
import re
from natsort import natsorted

st.set_page_config(layout="wide", page_title="Democracias no Mundo")

# Carregamento de dados
@st.cache_data
def load_data():
    try:
        df_dados = pd.read_csv("C:/PROJECTS/P1-VDEM_dashboard/UNdem-All.csv")
        df_indice = pd.read_csv("C:/PROJECTS/P1-VDEM_dashboard/indicadoresVDEM.csv")
        return df_dados, df_indice
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return None, None


# ========= CONTEINER DA SIDEBAR - SELEÇÕES ============
# Sidebar com os filtros hierárquicos
st.sidebar.header("Filtros")
df_dados, df_indice = load_data()


# Determinar os níveis corretamente
def determinar_nivel(row):
    partes = row["id"].split(".")
    if len(partes) == 1:
        return 1  # Índice
    elif len(partes) == 2:
        return 2  # Categoria
    elif len(partes) == 3:
        # Verifica se é um grupo ou uma variável diretamente vinculada à categoria
        if pd.notna(row["Grupo"]):
            return 3  # Grupo
        elif pd.notna(row["Elemento"]):
            return 4  # Variável diretamente vinculada à categoria
        else:
            return 3  # Grupo
    elif len(partes) == 4:
        return 4  # Variável vinculada a um grupo
    else:
        return None  # Caso inválido

df_indice["Nivel"] = df_indice.apply(determinar_nivel, axis=1)
df_filtro = df_indice[df_indice["id"].str.split(".").str[0].str.isdigit()]

# 1. ÍNDICE .dropna().iloc[0]
indice_options = natsorted(df_indice[(df_indice["Nivel"] == 1) & (df_filtro["id"].str.split(".").str[0].astype(int) <= 10)]["id"].tolist())
selected_indice = st.sidebar.selectbox(
    "🔹 Índice",
    indice_options,
    format_func=lambda x: f"{x} - {df_indice[df_indice['id'] == x]['Descricao'].values[0] if 'Descricao' in df_indice.columns else x}"
)

# 2. CATEGORIA
categoria_options = natsorted(
    df_indice[(df_indice["Nivel"] == 2) & (df_indice["id"].str.startswith(f"{selected_indice}."))]["id"].tolist()
)
selected_categoria = st.sidebar.selectbox(
    "🔹 Categoria",
    categoria_options,
    format_func=lambda x: f"{x} - {df_indice[df_indice['id'] == x]['Descricao'].values[0] if 'Descricao' in df_indice.columns else x}"
)

# 3. GRUPO
grupo_options = natsorted(df_indice[(df_indice["Nivel"] == 3) & (df_indice["id"].str.startswith(f"{selected_categoria}."))]["id"].tolist())


if grupo_options:
    # Verifica se o grupo tem descrição associada
    selected_grupo = st.sidebar.selectbox(
        "🔹 Grupo",
        grupo_options,
        format_func=lambda x: f"{x} - {df_indice[df_indice['id'] == x]['Descricao'].values[0] if 'Descricao' in df_indice.columns else x}"
    )
else:
    st.sidebar.markdown("🔸*Categoria sem grupos definidos.*")
    selected_grupo = None

# 4. VARIÁVEL
if selected_grupo:
    variavel_options = natsorted(df_indice[(df_indice["Nivel"] == 4) & (df_indice["id"].str.startswith(f"{selected_grupo}."))]["id"].tolist())
else:
    variavel_options = natsorted(df_indice[(df_indice["Nivel"] == 4) & (df_indice["id"].str.startswith(f"{selected_categoria}."))]["id"].tolist())

selected_variavel = st.sidebar.selectbox(
    "🔹 Variável",
    variavel_options,
    format_func=lambda x: f"{x} - {df_indice[df_indice['id'] == x]['Descricao'].values[0]}"
)
st.sidebar.markdown(f"{df_indice["Descricao"].get(selected_variavel, '')}")

# Tabela com as descrições
if not selected_variavel == None:
    with st.sidebar.expander("📑 Variáveis disponíveis", expanded=True):
        st.dataframe(
            df_indice[df_indice["id"].isin(variavel_options)][["variavel", "Descricao"]].drop_duplicates().set_index("variavel")
        )


# ========= CONTEINER DOS GRÁFICOS ============
# Configuração da página

st.title("Democracias no Mundo")
st.write("Veja o desenvolvimento dos direitos civis e institucionais de cada país ao longo do século XIX e XX!")

# Exibe seletor de variável apenas se houver opções
if not selected_variavel == None:
    variavel = df_indice[df_indice["id"] == selected_variavel]["variavel"].values[0]
    # Área principal - Exibição dos dados da variável selecionada
    st.header(f"Dados da variável: {variavel}")
    # Verifica se a variável existe no DataFrame de dados
    if variavel in df_dados.columns:
        selected_country = st.selectbox("Selecione um país:", sorted(df_dados["country_name"].dropna().unique()))
        df_filtrado = df_dados[df_dados["country_name"] == selected_country]
        
        if "year" in df_dados.columns:
            min_year, max_year = int(df_dados["year"].min()), int(df_dados["year"].max())
            year_range = st.slider("Intervalo de anos:", min_year, max_year, (min_year, max_year))
    else:
        st.warning(f"A variável '{variavel}' não está disponível na base de dados.")

# ========= GRÁFICO 1 ============
    st.subheader(f"📈 Evolução de '{variavel}' para {selected_country}")

    if variavel not in df_dados.columns:
        st.warning(f"A variável '{variavel}' não está disponível na base de dados.")
    else:
        df_chart = df_dados[
            (df_dados["country_name"] == selected_country) &
            (df_dados["year"] >= year_range[0]) &
            (df_dados["year"] <= year_range[1])
        ][["year", variavel]].sort_values("year")

        if not df_chart.empty and pd.api.types.is_numeric_dtype(df_dados[variavel]):
            st.line_chart(df_chart.set_index("year"), use_container_width=True)
        elif not df_chart.empty:
            st.warning(f"A variável '{variavel}' não é numérica.")
        else:
            st.info("Nenhum dado disponível para o gráfico.")

            
# ========= GRÁFICO 2 ============
    st.subheader(f"🌐 Comparativo para '{variavel}'")
    selected_countries = st.multiselect(
        "Selecione os países:", sorted(df_dados["country_name"].dropna().unique()), default=[selected_country]
    )

    if variavel not in df_dados.columns:
        st.warning(f"A variável '{variavel}' não está disponível na base de dados.")
    else:
        df_compare = df_dados[
            (df_dados["country_name"].isin(selected_countries)) &
            (df_dados["year"] >= year_range[0]) &
            (df_dados["year"] <= year_range[1])
        ]

        if pd.api.types.is_numeric_dtype(df_dados[variavel]):
            df_pivot = df_compare.pivot(index="year", columns="country_name", values=variavel)
            st.line_chart(df_pivot)
        else:
            st.warning("A variável selecionada para comparação não é numérica.")


# ========= GRÁFICO 3 ============
        # Exibe tabela com os dados
        st.subheader("Dados")
        st.dataframe(df_chart[[col for col in df_chart.columns if col in 
                                ["country_name", "year", variavel] or col == "year"]]
                    .sort_values(by="year" if "year" in df_chart.columns else df_chart.columns[0]))

# Tratamento de erros para variáveis não disponíveis
else:
    st.sidebar.warning("Nenhuma variável disponível para essa seleção.")
    st.warning("Selecione uma variáveis disponível para visualizar os gráficos.")

# Exibe informações sobre a estrutura hierárquica
with st.sidebar.expander("ℹ️ Informações"):
    st.write("""
    Este dashboard exibe dados com base na estrutura hierárquica:
    
    1. **Índice**: Nível superior da hierarquia
    2. **Categoria**: Subdivisão do Índice
    3. **Grupo**: (Opcional) Aparece apenas quando a Categoria possui subdivisões.
    4. **Variável**: Dado final a ser visualizado

    """)





# streamlit run vdem_app.py
# if len(df_indice["id"]) == 1 else ""