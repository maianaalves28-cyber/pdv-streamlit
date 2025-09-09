
import streamlit as st
import pandas as pd
from datetime import datetime

# Cadastro de produtos (código interno: nome e preço por kg)
produtos = {
    "0001": {"nome": "Lombinho", "preco": 39.90},
    "0002": {"nome": "Fraldinha", "preco": 42.50},
    "0003": {"nome": "Fato", "preco": 28.00},
    "0004": {"nome": "Coração", "preco": 29.90},
    "0005": {"nome": "Fígado", "preco": 22.00},
    "0006": {"nome": "Rins", "preco": 20.00},
    "0007": {"nome": "Bargada Grossa", "preco": 19.00},
    "0008": {"nome": "Bargada Fina", "preco": 18.50},
    "0009": {"nome": "Bargada Gorda", "preco": 17.00},
    "0010": {"nome": "Baço", "preco": 16.00},
    "0011": {"nome": "Sangria", "preco": 15.00},
    "0012": {"nome": "Costela", "preco": 24.90},
    "0013": {"nome": "Osso do Patinho", "preco": 12.00},
    "0014": {"nome": "Carne de Cabeça", "preco": 14.00},
    "0015": {"nome": "Língua", "preco": 33.00},
    "0016": {"nome": "Pé de Cipó", "preco": 19.50},
    "0017": {"nome": "Carne Moída", "preco": 35.00}
}

if "vendas" not in st.session_state:
    st.session_state.vendas = []
if "historico" not in st.session_state:
    st.session_state.historico = pd.DataFrame()

st.title("🛒 PDV Açougue - Código de Barras Inteligente")

codigo_barras = st.text_input("Passe o código de barras")
peso_manual = st.number_input("Peso manual (kg)", min_value=0.01, step=0.01, value=1.0)

if st.button("Adicionar Item") and codigo_barras:
    try:
        peso = None
        produto_cod = None

        # Caso 1: Código da balança (12 ou 13 dígitos) - Decodifica padrão Toledo Prix 4
        if len(codigo_barras) in [12, 13] and codigo_barras.startswith('2'):
            produto_cod = codigo_barras[1:5] # Código do produto (4 dígitos após o '2')
            peso_raw = codigo_barras[5:10] # Peso em gramas (5 dígitos)
            peso = int(peso_raw) / 1000.0 # Converte para kg

        # Caso 2: Código fixo (usuário informa peso manual) - Assumindo código de 4 dígitos para produtos cadastrados
        elif len(codigo_barras) == 4 and codigo_barras in produtos:
            produto_cod = codigo_barras
            peso = peso_manual

        else:
            st.error("⚠️ Código de barras inválido ou não suportado!")
            produto_cod = None # Garante que não tente buscar produto com código inválido


        # Se produto encontrado
        if produto_cod and produto_cod in produtos:
            produto = produtos[produto_cod]
            subtotal = produto["preco"] * peso
            st.session_state.vendas.append({
                "Produto": produto["nome"],
                "Peso (kg)": round(peso, 3),
                "Preço/kg": produto["preco"],
                "Subtotal": round(subtotal, 2),
                "Data": datetime.now().strftime("%Y-%m-%d") # Adiciona a data
            })
        elif produto_cod: # Verifica se havia um produto_cod extraído, mas não encontrado nos produtos cadastrados
             st.warning("⚠️ Produto não cadastrado!")


    except Exception as e:
        st.error(f"Erro ao processar código: {e}")

# Mostrar tabela de vendas
if st.session_state.vendas:
    df = pd.DataFrame(st.session_state.vendas)
    st.table(df)
    total = df["Subtotal"].sum()
    st.subheader(f"💰 Total: R$ {total:.2f}")

    if st.button("Finalizar Venda"):
        hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        # A coluna "Data" já foi adicionada ao adicionar itens
        st.session_state.historico = pd.concat([st.session_state.historico, df], ignore_index=True)

        # Gerar CSV da venda atual
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Baixar Nota da Venda (CSV)",
            data=csv,
            file_name=f"venda_{hora.replace(':','-').replace(' ','_')}.csv",
            mime="text/csv"
        )

        st.success(f"Venda finalizada! Total R$ {total:.2f}")
        st.session_state.vendas = []

# Histórico completo (opcional)
if not st.session_state.historico.empty:
    st.subheader("📜 Histórico de Vendas")
    st.dataframe(st.session_state.historico)
    csv_all = st.session_state.historico.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Baixar Histórico Completo",
        data=csv_all,
        file_name="historico_vendas.csv",
        mime="text/csv"
    )

# Seção de Relatório Diário
st.subheader("📊 Relatório Diário de Vendas")

data_relatorio = st.date_input("Selecione a data do relatório", datetime.today())

if st.button("Gerar Relatório"):
    if not st.session_state.historico.empty:
        # Convert 'Data' column to datetime objects
        st.session_state.historico['Data'] = pd.to_datetime(st.session_state.historico['Data'])

        # Filter sales by the selected date
        data_selecionada_str = data_relatorio.strftime("%Y-%m-%d")
        vendas_do_dia = st.session_state.historico[st.session_state.historico['Data'].dt.strftime("%Y-%m-%d") == data_selecionada_str]

        if not vendas_do_dia.empty:
            # Group by product and sum the weight
            relatorio_diario = vendas_do_dia.groupby("Produto")["Peso (kg)"].sum().reset_index()
            relatorio_diario.rename(columns={"Peso (kg)": "Total Vendido (kg)"}, inplace=True)

            st.subheader(f"Relatório de Vendas para {data_selecionada_str}")
            st.dataframe(relatorio_diario)
        else:
            st.info(f"Nenhuma venda registrada para {data_selecionada_str}.")
    else:
        st.warning("Não há histórico de vendas para gerar o relatório.")
