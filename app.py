import streamlit as st

# Configuração da página
st.set_page_config(
    page_title="Calculadora de Pegada de Carbono",
    page_icon="🌍",
    layout="centered"
)

# Título e introdução
st.title("🌍 Pegada de Carbono")
st.subheader("Em busca da neutralidade corporativa")
st.markdown("Baseado na apresentação de Cássio Luiz Vellani | Fatores IPCC AR6 e metodologia 2006 GL")

st.markdown("---")

# Sidebar com informações técnicas
with st.sidebar:
    st.header("📘 Referências técnicas")
    st.markdown("""
    - **IPCC 2006 GL** – Vol.2 (Combustão Estacionária e Móvel)
    - **PCI Gás Natural**: 0,0000386 TJ/m³ (≈38,6 MJ/m³)
    - **PCI Diesel**: 0,043 TJ/t (43,0 TJ/Gg)
    - **Densidade Diesel S10**: 0,84 kg/L
    - **GWP (20 anos – AR6)**:  
      CO₂ = 1 | CH₄ fóssil = 82,5 | N₂O = 273
    - **Preço do crédito de carbono**: € 78 / tCO₂e  
    - **Cotação Euro**: R$ 5,85 (exemplo)
    """)

    st.caption("Lei nº 15.042/2024 – Reservas técnicas para aquisição de créditos de carbono.")

# ============================================
# FUNÇÕES DE CÁLCULO
# ============================================

def calcular_pegada_gas(m3_gas):
    """Retorna (total_tco2e, detalhes_dict) para gás natural (combustão estacionária)"""
    pci = 0.0000386          # TJ/m³
    consumo_tj = m3_gas * pci

    # Fatores de emissão (t/TJ) – Tabela 2.4 IPCC
    fe_co2 = 56.1    # t CO₂/TJ
    fe_ch4 = 0.005   # t CH₄/TJ
    fe_n2o = 0.0001  # t N₂O/TJ

    # Massa emitida (t)
    m_co2 = consumo_tj * fe_co2
    m_ch4 = consumo_tj * fe_ch4
    m_n2o = consumo_tj * fe_n2o

    # GWP AR6 (20 anos)
    gwp_co2 = 1
    gwp_ch4 = 82.5
    gwp_n2o = 273

    co2e_co2 = m_co2 * gwp_co2
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


def calcular_pegada_diesel(litros_diesel):
    """Retorna (total_tco2e, detalhes_dict) para diesel S10 (combustão móvel)"""
    densidade = 0.84          # kg/L
    massa_kg = litros_diesel * densidade
    massa_t = massa_kg / 1000

    pci = 0.043               # TJ/t
    consumo_tj = massa_t * pci

    # Fatores de emissão (t/TJ) – Tabelas 3.2.1 e 3.2.2 (Mobile Combustion)
    fe_co2 = 74.1    # t CO₂/TJ
    fe_ch4 = 0.0039  # t CH₄/TJ
    fe_n2o = 0.0039  # t N₂O/TJ

    m_co2 = consumo_tj * fe_co2
    m_ch4 = consumo_tj * fe_ch4
    m_n2o = consumo_tj * fe_n2o

    gwp_co2 = 1
    gwp_ch4 = 82.5
    gwp_n2o = 273

    co2e_co2 = m_co2 * gwp_co2
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


def custo_neutralizacao(tco2e, preco_eur=78, cotacao_brl=5.85):
    custo_eur = tco2e * preco_eur
    custo_brl = custo_eur * cotacao_brl
    return custo_eur, custo_brl


# ============================================
# INTERFACE PRINCIPAL
# ============================================

tab1, tab2 = st.tabs(["⚡ Energia (Gás Natural)", "🚛 Transporte (Diesel S10)"])

with tab1:
    st.header("Exemplo prático 1 – Combustão estacionária")
    st.markdown("Usina termelétrica ou caldeira industrial a gás natural.")

    m3 = st.number_input("Consumo de gás natural (m³)", min_value=0.0, value=50000.0, step=1000.0, format="%.0f", key="gas")
    if st.button("Calcular pegada (gás)", key="btn_gas"):
        if m3 > 0:
            total, detalhes = calcular_pegada_gas(m3)
            st.success(f"🌿 Pegada de carbono total: **{total:.2f} tCO₂e**")
            with st.expander("📊 Ver detalhes do cálculo"):
                st.json(detalhes)
            # Custo de neutralização
            eur, brl = custo_neutralizacao(total)
            st.info(f"💶 Custo para neutralizar: **€ {eur:,.2f}**  |  **R$ {brl:,.2f}**")
        else:
            st.warning("Digite um consumo válido.")

with tab2:
    st.header("Exemplo prático 2 – Combustão móvel")
    st.markdown("Frota de caminhões rodando com diesel S10.")

    litros = st.number_input("Consumo de diesel S10 (litros)", min_value=0.0, value=30000.0, step=1000.0, format="%.0f", key="diesel")
    if st.button("Calcular pegada (diesel)", key="btn_diesel"):
        if litros > 0:
            total, detalhes = calcular_pegada_diesel(litros)
            st.success(f"🌿 Pegada de carbono total: **{total:.2f} tCO₂e**")
            with st.expander("📊 Ver detalhes do cálculo"):
                st.json(detalhes)
            eur, brl = custo_neutralizacao(total)
            st.info(f"💶 Custo para neutralizar: **€ {eur:,.2f}**  |  **R$ {brl:,.2f}**")
        else:
            st.warning("Digite um consumo válido.")

st.markdown("---")
st.caption("Nota: Os fatores de emissão e GWP (20 anos) seguem o IPCC AR6 (2021) e as diretrizes IPCC 2006. O preço do crédito de carbono é ilustrativo (€78/tCO₂e – fonte: apresentação).")
