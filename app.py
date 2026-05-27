import streamlit as st
import requests
import yfinance as yf
import numpy as np
import pandas as pd

# Configuração da página
st.set_page_config(
    page_title="Calculadora de Pegada de Carbono",
    page_icon="🌍",
    layout="centered"
)

# ============================================
# FUNÇÕES DE COTAÇÃO EM TEMPO REAL
# ============================================

def obter_cotacao_carbono():
    """Obtém a cotação do carbono via Yahoo Finance (ticker CO2.L)."""
    try:
        ticker = yf.Ticker("CO2.L")
        data = ticker.history(period="1d")
        if not data.empty:
            preco = data['Close'].iloc[-1]
            # Validação básica: preço entre 10 e 200 euros
            if 10 < preco < 200:
                return preco, "€", "Carbon Futures (CO2.L)", True, "Yahoo Finance (CO2.L)"
        return 85.50, "€", "Carbon Emissions (Referência)", False, "Referência"
    except Exception:
        return 85.50, "€", "Carbon Emissions (Referência)", False, "Referência"

def obter_cotacao_euro_real():
    """Obtém a cotação EUR/BRL usando API AwesomeAPI ou fallback."""
    try:
        url = "https://economia.awesomeapi.com.br/last/EUR-BRL"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return float(data['EURBRL']['bid']), "R$", True, "AwesomeAPI"
    except:
        pass
    try:
        url = "https://api.exchangerate-api.com/v4/latest/EUR"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data['rates']['BRL'], "R$", True, "ExchangeRate-API"
    except:
        pass
    return 5.50, "R$", False, "Referência"

def inicializar_cotacoes():
    """Inicializa as variáveis de cotação no session_state."""
    if 'preco_carbono' not in st.session_state:
        preco, moeda, nome, ok, fonte = obter_cotacao_carbono()
        st.session_state.preco_carbono = preco
        st.session_state.moeda_carbono = moeda
        st.session_state.fonte_carbono = fonte
    if 'taxa_cambio' not in st.session_state:
        taxa, moeda_real, ok, fonte = obter_cotacao_euro_real()
        st.session_state.taxa_cambio = taxa
        st.session_state.moeda_real = moeda_real
        st.session_state.fonte_cambio = fonte
    if 'cotacao_atualizada' not in st.session_state:
        st.session_state.cotacao_atualizada = False

# ============================================
# PARÂMETROS AVANÇADOS (EDITÁVEIS PELO USUÁRIO)
# ============================================

def inicializar_parametros_avancados():
    """Define os valores padrão (IPCC/referência) e permite que o usuário os altere via session_state."""
    if 'parametros' not in st.session_state:
        st.session_state.parametros = {
            # Diesel
            'densidade_diesel': 0.84,          # kg/L
            'pci_diesel': 0.043,               # TJ/t
            'fe_co2_diesel': 74.1,             # t CO₂/TJ
            'fe_ch4_diesel': 0.0039,           # t CH₄/TJ
            'fe_n2o_diesel': 0.0039,           # t N₂O/TJ

            # Gás natural
            'pci_gas': 0.0000386,              # TJ/m³
            'fe_co2_gas': 56.1,                # t CO₂/TJ
            'fe_ch4_gas': 0.005,               # t CH₄/TJ
            'fe_n2o_gas': 0.0001,              # t N₂O/TJ

            # GWPs (AR6 20 anos)
            'gwp_ch4': 82.5,
            'gwp_n2o': 273
        }

def resetar_parametros():
    """Restaura os valores padrão."""
    st.session_state.parametros = {
        'densidade_diesel': 0.84,
        'pci_diesel': 0.043,
        'fe_co2_diesel': 74.1,
        'fe_ch4_diesel': 0.0039,
        'fe_n2o_diesel': 0.0039,
        'pci_gas': 0.0000386,
        'fe_co2_gas': 56.1,
        'fe_ch4_gas': 0.005,
        'fe_n2o_gas': 0.0001,
        'gwp_ch4': 82.5,
        'gwp_n2o': 273
    }

# ============================================
# FUNÇÕES DE CÁLCULO DA PEGADA (USANDO PARÂMETROS AVANÇADOS)
# ============================================

def calcular_pegada_gas(m3_gas, params):
    """Retorna (total_tco2e, detalhes_dict) para gás natural."""
    pci = params['pci_gas']
    consumo_tj = m3_gas * pci

    fe_co2 = params['fe_co2_gas']
    fe_ch4 = params['fe_ch4_gas']
    fe_n2o = params['fe_n2o_gas']

    m_co2 = consumo_tj * fe_co2
    m_ch4 = consumo_tj * fe_ch4
    m_n2o = consumo_tj * fe_n2o

    gwp_ch4 = params['gwp_ch4']
    gwp_n2o = params['gwp_n2o']

    co2e_co2 = m_co2 * 1
    co2e_ch4 = m_ch4 * gwp_ch4
    co2e_n2o = m_n2o * gwp_n2o

    total = co2e_co2 + co2e_ch4 + co2e_n2o

    detalhes = {
        "Consumo (m³)": m3_gas,
        "Energia (TJ)": consumo_tj,
        "CO₂ (t)": m_co2,
        "CH₄ (t)": m_ch4,
        "N₂O (t)": m_n2o,
        "CO₂e CO₂": co2e_co2,
        "CO₂e CH₄": co2e_ch4,
        "CO₂e N₂O": co2e_n2o,
        "Total (tCO₂e)": total
    }
    return total, detalhes

def calcular_pegada_diesel(litros_diesel, params):
    """Retorna (total_tco2e, detalhes_dict) para diesel S10."""
    densidade = params['densidade_diesel']
    massa_kg = litros_diesel * densidade
    massa_t = massa_kg / 1000

    pci = params['pci_diesel']
    consumo_tj = massa_t * pci

    fe_co2 = params['fe_co2_diesel']
    fe_ch4 = params['fe_ch4_diesel']
    fe_n2o = params['fe_n2o_diesel']

    m_co2 = consumo_tj * fe_co2
    m_ch4 = consumo_tj * fe_ch4
    m_n2o = consumo_tj * fe_n2o

    gwp_ch4 = params['gwp_ch4']
    gwp_n2o = params['gwp_n2o']

    co2e_co2 = m_co2 * 1
    co2e_ch4 = m_ch4 * gwp_ch4
    co2e_n2o = m_n2o * gwp_n2o

    total = co2e_co2 + co2e_ch4 + co2e_n2o

    detalhes = {
        "Diesel (L)": litros_diesel,
        "Massa (t)": massa_t,
        "Energia (TJ)": consumo_tj,
        "CO₂ (t)": m_co2,
        "CH₄ (t)": m_ch4,
        "N₂O (t)": m_n2o,
        "CO₂e CO₂": co2e_co2,
        "CO₂e CH₄": co2e_ch4,
        "CO₂e N₂O": co2e_n2o,
        "Total (tCO₂e)": total
    }
    return total, detalhes

def formatar_br(numero):
    """Formata número no padrão brasileiro (ponto milhar, vírgula decimal)."""
    if pd.isna(numero):
        return "N/A"
    numero = round(numero, 2)
    return f"{numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# ============================================
# INICIALIZAÇÕES (COTAÇÕES + PARÂMETROS)
# ============================================

inicializar_cotacoes()
inicializar_parametros_avancados()

# ============================================
# BARRA LATERAL COM COTAÇÕES E PARÂMETROS AVANÇADOS
# ============================================

with st.sidebar:
    st.header("💰 Mercado de Carbono e Câmbio")

    # Botão para atualizar cotações manualmente
    if st.button("🔄 Atualizar Cotações", key="atualizar"):
        with st.spinner("Obtendo cotações..."):
            preco, moeda, _, _, fonte = obter_cotacao_carbono()
            st.session_state.preco_carbono = preco
            st.session_state.moeda_carbono = moeda
            st.session_state.fonte_carbono = fonte
            taxa, moeda_real, _, fonte_cambio = obter_cotacao_euro_real()
            st.session_state.taxa_cambio = taxa
            st.session_state.moeda_real = moeda_real
            st.session_state.fonte_cambio = fonte_cambio
            st.session_state.cotacao_atualizada = True
            st.rerun()

    # Exibe as cotações atuais
    st.metric(
        label="Preço do Carbono (tCO₂e)",
        value=f"{st.session_state.moeda_carbono} {formatar_br(st.session_state.preco_carbono)}",
        help=f"Fonte: {st.session_state.fonte_carbono}"
    )
    st.metric(
        label="Euro (EUR/BRL)",
        value=f"{st.session_state.moeda_real} {formatar_br(st.session_state.taxa_cambio)}",
        help=f"Fonte: {st.session_state.fonte_cambio}"
    )
    preco_carbono_reais = st.session_state.preco_carbono * st.session_state.taxa_cambio
    st.metric(
        label="Carbono em Reais (tCO₂e)",
        value=f"R$ {formatar_br(preco_carbono_reais)}",
        help="Preço do carbono convertido para Reais Brasileiros"
    )

    with st.expander("ℹ️ Sobre as cotações"):
        st.markdown("""
        **📊 Fontes:**
        - **Carbono:** Futuros da ICE (CO2.L) – EU ETS
        - **Euro:** API AwesomeAPI / ExchangeRate-API
        - Valores são atualizados automaticamente ao abrir o app.
        - Clique em "Atualizar Cotações" para obter o último preço.
        - Em caso de falha, são usados valores de referência (€85,50 e R$5,50).
        """)

    # ============================================
    # PARÂMETROS AVANÇADOS (EDITÁVEIS)
    # ============================================
    with st.expander("⚙️ Parâmetros avançados (opcional)"):
        st.markdown("Ajuste os valores caso possua dados mais precisos (laudo do fornecedor, fatura de gás, etc.).")
        params = st.session_state.parametros

        st.subheader("Diesel S10")
        params['densidade_diesel'] = st.number_input("Densidade (kg/L)", value=params['densidade_diesel'], step=0.01, format="%.3f")
        params['pci_diesel'] = st.number_input("PCI diesel (TJ/t)", value=params['pci_diesel'], step=0.001, format="%.5f")
        params['fe_co2_diesel'] = st.number_input("FE CO₂ diesel (t/TJ)", value=params['fe_co2_diesel'], step=0.1)
        params['fe_ch4_diesel'] = st.number_input("FE CH₄ diesel (t/TJ)", value=params['fe_ch4_diesel'], step=0.0001, format="%.5f")
        params['fe_n2o_diesel'] = st.number_input("FE N₂O diesel (t/TJ)", value=params['fe_n2o_diesel'], step=0.0001, format="%.5f")

        st.subheader("Gás Natural")
        params['pci_gas'] = st.number_input("PCI gás natural (TJ/m³)", value=params['pci_gas'], step=1e-7, format="%.8f")
        params['fe_co2_gas'] = st.number_input("FE CO₂ gás (t/TJ)", value=params['fe_co2_gas'], step=0.1)
        params['fe_ch4_gas'] = st.number_input("FE CH₄ gás (t/TJ)", value=params['fe_ch4_gas'], step=0.0001, format="%.5f")
        params['fe_n2o_gas'] = st.number_input("FE N₂O gás (t/TJ)", value=params['fe_n2o_gas'], step=0.00001, format="%.6f")

        st.subheader("GWPs (Potencial de Aquecimento Global)")
        params['gwp_ch4'] = st.number_input("GWP CH₄ (horizonte 20 anos)", value=params['gwp_ch4'], step=1.0)
        params['gwp_n2o'] = st.number_input("GWP N₂O (horizonte 20 anos)", value=params['gwp_n2o'], step=1.0)

        if st.button("🔄 Restaurar valores padrão"):
            resetar_parametros()
            st.rerun()

        st.caption("Valores padrão: IPCC AR6 para GWPs; fatores de emissão IPCC 2006; densidade e PCI de referência.")

# ============================================
# TÍTULO PRINCIPAL
# ============================================

st.title("🌍 Pegada de Carbono")
st.subheader("Em busca da neutralidade corporativa")
st.markdown("Baseado na apresentação de Cássio Luiz Vellani | Fatores IPCC AR6 e metodologia 2006 GL")
st.markdown("---")

# ============================================
# INTERFACE DE CÁLCULO (abas)
# ============================================

tab1, tab2 = st.tabs(["⚡ Energia (Gás Natural)", "🚛 Transporte (Diesel S10)"])

with tab1:
    st.header("Exemplo prático 1 – Combustão estacionária")
    st.markdown("Usina termelétrica ou caldeira industrial a gás natural.")

    m3 = st.number_input("Consumo de gás natural (m³)", min_value=0.0, value=50000.0, step=1000.0, format="%.0f", key="gas")
    if st.button("Calcular pegada (gás)", key="btn_gas"):
        if m3 > 0:
            total, detalhes = calcular_pegada_gas(m3, st.session_state.parametros)
            st.success(f"🌿 Pegada de carbono total: **{formatar_br(total)} tCO₂e**")
            with st.expander("📊 Ver detalhes do cálculo"):
                detalhes_formatados = {k: formatar_br(v) if isinstance(v, (int, float)) else v for k, v in detalhes.items()}
                st.json(detalhes_formatados)
            # Custo de neutralização com cotações em tempo real
            preco_eur = st.session_state.preco_carbono
            taxa = st.session_state.taxa_cambio
            custo_eur = total * preco_eur
            custo_brl = custo_eur * taxa
            st.info(f"💶 Custo para neutralizar: **€ {formatar_br(custo_eur)}**  |  **R$ {formatar_br(custo_brl)}**")
            st.caption(f"Preço do carbono usado: € {formatar_br(preco_eur)}/tCO₂e | Euro = R$ {formatar_br(taxa)}")
        else:
            st.warning("Digite um consumo válido.")

with tab2:
    st.header("Exemplo prático 2 – Combustão móvel")
    st.markdown("Frota de caminhões rodando com diesel S10.")

    litros = st.number_input("Consumo de diesel S10 (litros)", min_value=0.0, value=30000.0, step=1000.0, format="%.0f", key="diesel")
    if st.button("Calcular pegada (diesel)", key="btn_diesel"):
        if litros > 0:
            total, detalhes = calcular_pegada_diesel(litros, st.session_state.parametros)
            st.success(f"🌿 Pegada de carbono total: **{formatar_br(total)} tCO₂e**")
            with st.expander("📊 Ver detalhes do cálculo"):
                detalhes_formatados = {k: formatar_br(v) if isinstance(v, (int, float)) else v for k, v in detalhes.items()}
                st.json(detalhes_formatados)
            preco_eur = st.session_state.preco_carbono
            taxa = st.session_state.taxa_cambio
            custo_eur = total * preco_eur
            custo_brl = custo_eur * taxa
            st.info(f"💶 Custo para neutralizar: **€ {formatar_br(custo_eur)}**  |  **R$ {formatar_br(custo_brl)}**")
            st.caption(f"Preço do carbono usado: € {formatar_br(preco_eur)}/tCO₂e | Euro = R$ {formatar_br(taxa)}")
        else:
            st.warning("Digite um consumo válido.")

st.markdown("---")
st.caption("Nota: Os fatores de emissão e GWP (20 anos) seguem o IPCC AR6 (2021) e as diretrizes IPCC 2006, a menos que alterados nos parâmetros avançados. As cotações são obtidas em tempo real via Yahoo Finance (CO2.L) e APIs de câmbio.")
