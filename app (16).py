
import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os

PRODUTOS_FILE = "produtos.json"
HISTORICO_FILE = "historico_vendas.csv" # Added for persistence of sales history

# Carregar cadastro de produtos
def carregar_produtos():
    if os.path.exists(PRODUTOS_FILE):
        try:
            with open(PRODUTOS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            st.error("Erro ao carregar dados de produtos. O arquivo JSON pode estar corrompido.")
            return {} # Retorna um dicionário vazio em caso de erro
    else:
        # Cadastro de produtos inicial (código interno: nome e preço por kg)
        return {
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

# Salvar cadastro de produtos
def salvar_produtos(produtos_data):
    with open(PRODUTOS_FILE, "w", encoding="utf-8") as f:
        json.dump(produtos_data, f, indent=4)

# Carregar histórico de vendas
def carregar_historico():
    if os.path.exists(HISTORICO_FILE):
        try:
            df_historico = pd.read_csv(HISTORICO_FILE)
            # Ensure 'Data' column is datetime objects
            df_historico['Data'] = pd.to_datetime(df_historico['Data'])
            return df_historico
        except Exception as e:
            st.error(f"Erro ao carregar histórico de vendas: {e}")
            return pd.DataFrame() # Return empty DataFrame in case of error
    else:
        return pd.DataFrame() # Return empty DataFrame if file doesn't exist

# Salvar histórico de vendas
def salvar_historico(df_historico):
    df_historico.to_csv(HISTORICO_FILE, index=False)


# Função para remover item da venda
def remover_item(index):
    if 0 <= index < len(st.session_state.vendas):
        st.session_state.vendas.pop(index)
        st.rerun()

# Função para processar código de barras e adicionar item
def processar_codigo_barras(codigo_barras, peso_manual, produtos_data):
    if not codigo_barras:
        return # Do nothing if input is empty

    try:
        peso = None
        produto_cod = None

        # Caso 1: Código da balança (13 dígitos) - Decodifica padrão Toledo Prix
        # Assumindo estrutura: 2 + PP PP + G GGGG + D
        # Onde:
        # 2: Prefixo indicando produto variável (peso ou preço)
        # PPP P: Código do produto (4 dígitos) - Posições 2 a 5 (índices 1 a 4)
        # G GGGG: Peso em gramas (5 dígitos) - Posições 6 a 10 (índices 5 a 9)
        # D: Dígito verificador da balança (1 dígito) - Posição 11 (índice 10)
        # DD: Dígitos verificadores finais (2 dígitos) - Posições 12 a 13 (índices 11 a 12)

        if len(codigo_barras) == 13 and codigo_barras.startswith('2'):
            # Código do produto: 4 dígitos, posições 3 a 6 (índices 2 a 5)
            produto_cod = codigo_barras[2:6]
            # Peso em Gramas: 5 dígitos, posições 7 a 11 (índices 6 a 10)
            peso_raw = codigo_barras[6:11] # Peso em gramas (5 dígitos)

            # Converte para kg dividindo por 1000.0 (leitura em gramas)
            # Ajustado para dividir por 1000.0 para converter gramas para kg
            peso = int(peso_raw) / 1000.0 # Converte para kg

            # Note: A validação completa dos dígitos verificadores não está implementada.
            # A lógica assume que os dígitos do produto e peso estão nas posições esperadas.

        # Caso 2: Código fixo (usuário informa peso manual) - Assumindo código de 4 dígitos para produtos cadastrados
        elif len(codigo_barras) == 4 and codigo_barras in produtos_data:
            produto_cod = codigo_barras
            peso = peso_manual # Use the manually entered weight

        else:
            st.error("⚠️ Código de barras inválido ou não suportado!")
            produto_cod = None # Garante que não tente buscar produto com código inválido


        # Se produto encontrado e peso válido
        if produto_cod and produto_cod in produtos_data and peso is not None and peso > 0:
            produto = produtos_data[produto_cod]
            subtotal = produto["preco"] * peso

            st.session_state.vendas.append({
                "Produto": produto["nome"],
                "Peso (kg)": round(peso, 3), # Exibe em kg arredondado para 3 casas
                "Preço/kg": produto["preco"],
                "Subtotal": round(subtotal, 2),
                "Data": datetime.now().strftime("%Y-%m-%d") # Adiciona a data
            })
            #st.rerun() # Rerun to update the sales table immediately

        elif produto_cod and produto_cod not in produtos_data: # Verifica se havia um produto_cod extraído, mas não encontrado nos produtos cadastrados
             st.warning("⚠️ Produto não cadastrado!")
        elif produto_cod and (peso is None or peso <= 0):
             st.warning("⚠️ Peso inválido para o produto.")


    except Exception as e:
        st.error(f"Erro ao processar código: {e}")

# Função para excluir produtos selecionados
def excluir_produtos_selecionados():
    if st.session_state.produtos_selecionados_excluir:
        for codigo in st.session_state.produtos_selecionados_excluir:
            if codigo in st.session_state.produtos:
                del st.session_state.produtos[codigo]
        salvar_produtos(st.session_state.produtos)
        st.success(f"{len(st.session_state.produtos_selecionados_excluir)} produto(s) excluído(s) com sucesso!")
        st.session_state.produtos_selecionados_excluir = [] # Clear selection after deletion
        st.rerun() # Rerun to update the displayed list
    else:
        st.warning("Nenhum produto selecionado para exclusão.")


if "vendas" not in st.session_state:
    st.session_state.vendas = []
if "historico" not in st.session_state:
    st.session_state.historico = carregar_historico() # Load history on startup
if "produtos" not in st.session_state:
    st.session_state.produtos = carregar_produtos() # Load products on startup
if "produtos_selecionados_excluir" not in st.session_state:
    st.session_state.produtos_selecionados_excluir = []


st.title("🛒 PDV Açougue - Código de Barras Inteligente")

with st.expander("🛒 PDV"):
    codigo_barras = st.text_input("Passe o código de barras", key="codigo_barras_input")
    peso_manual = st.number_input("Peso manual (kg)", min_value=0.01, step=0.01, value=1.0, key="peso_manual_input")

    # Process barcode automatically when input changes
    if codigo_barras:
         # Check if the input has changed since the last processing
        if "last_processed_barcode" not in st.session_state or st.session_state.last_processed_barcode != codigo_barras:
            processar_codigo_barras(codigo_barras, peso_manual, st.session_state.produtos)
            st.session_state.last_processed_barcode = codigo_barras # Store the processed barcode
            #st.rerun() # Rerun to update the sales table immediately

    # Mostrar tabela de vendas com botão de exclusão
    if st.session_state.vendas:
        st.subheader("Venda Atual")
        df = pd.DataFrame(st.session_state.vendas)

        # Display table with remove buttons
        # Use columns for better layout
        cols = st.columns([2, 1, 1, 1, 1, 0.5]) # Adjust column widths
        cols[0].write("**Produto**")
        cols[1].write("**Peso (kg)**") # Header em kg
        cols[2].write("**Preço/kg**")
        cols[3].write("**Subtotal**")
        cols[4].write("**Data**")
        cols[5].write("**Excluir**") # Header for the remove button column

        for index, row in df.iterrows():
            col1, col2, col3, col4, col5, col6 = st.columns([2, 1, 1, 1, 1, 0.5]) # Adjust column widths
            col1.write(row['Produto'])
            col2.write(row['Peso (kg)']) # Exibe o peso em kg
            col3.write(row['Preço/kg'])
            col4.write(row['Subtotal'])
            col5.write(row['Data'])
            # Use a trash icon for the remove button
            if col6.button("🗑️", key=f"remove_item_{index}"):
                remover_item(index)


        total = df["Subtotal"].sum()
        st.subheader(f"💰 Total: R$ {total:.2f}")

        if st.button("Finalizar Venda"):
            # Before adding to history, ensure weight column is consistent for aggregation later if needed.
            # For now, we'll save as is. If daily report needs total kg, it will need adjustment.
            st.session_state.historico = pd.concat([st.session_state.historico, df], ignore_index=True)
            salvar_historico(st.session_state.historico) # Save history

            # Gerar CSV da venda atual
            hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="⬇️ Baixar Nota da Venda (CSV)",
                data=csv,
                file_name=f"venda_{hora.replace(':','-').replace(' ','_')}.csv",
                mime="text/csv"
            )

            st.success(f"Venda finalizada! Total R$ {total:.2f}")
            st.session_state.vendas = []
            st.session_state.last_processed_barcode = None # Reset processed barcode
            st.rerun()


with st.expander("📊 Relatório Diário de Vendas"):
    data_relatorio = st.date_input("Selecione a data do relatório", datetime.today())

    if st.button("Gerar Relatório"):
        if not st.session_state.historico.empty:
            # Ensure 'Data' column is datetime objects for filtering
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

                 # Generate CSV for download
                csv_relatorio = relatorio_diario.to_csv(index=False).encode("utf-8")

                # Add download button
                st.download_button(
                    label="⬇️ Baixar Relatório Diário (CSV)",
                    data=csv_relatorio,
                    file_name=f"relatorio_diario_{data_selecionada_str}.csv",
                    mime="text/csv"
                )
            else:
                st.info(f"Nenhuma venda registrada para {data_selecionada_str}.")
        else:
            st.warning("Não há histórico de vendas para gerar o relatório.")

with st.expander("⬆️ Gerenciar Produtos"):
    st.subheader("⬆️ Atualizar Preços de Produtos")

    # Create a list of product names and codes for the selectbox
    produto_options = {v["nome"]: k for k, v in st.session_state.produtos.items()}
    # Add a check if produto_options is empty
    if not produto_options:
        st.info("Nenhum produto cadastrado. Por favor, cadastre um novo produto primeiro.")
    else:
        selected_produto_name = st.selectbox("Selecione o produto", list(produto_options.keys()), key="update_preco_selectbox")

        # Get the current price of the selected product
        selected_produto_code = produto_options[selected_produto_name]
        current_price = st.session_state.produtos[selected_produto_code]["preco"]

        novo_preco = st.number_input("Novo Preço por Kg", min_value=0.01, step=0.10, value=current_price, key="update_preco_input")

        if st.button("Atualizar Preço", key="update_preco_button"):
            # Get the product code from the selected product name
            produto_cod_to_update = produto_options[selected_produto_name]

            # Update the price in the session state products dictionary
            st.session_state.produtos[produto_cod_to_update]["preco"] = novo_preco

            # Save the updated products to the JSON file
            salvar_produtos(st.session_state.produtos)

            st.success(f"Preço do {selected_produto_name} atualizado para R$ {novo_preco:.2f} por Kg!")
            st.rerun() # Rerun to update the displayed current price

    st.markdown("---") # Separator

    st.subheader("➕ Cadastrar Novo Produto")

    novo_produto_codigo = st.text_input("Código do Produto (4 dígitos)", max_chars=4, key="novo_codigo")
    novo_produto_nome = st.text_input("Nome do Produto", key="novo_nome")
    novo_produto_preco = st.number_input("Preço por Kg do Novo Produto", min_value=0.01, step=0.10, key="novo_preco")

    if st.button("Cadastrar Produto", key="cadastrar_produto_button"):
        if not novo_produto_codigo or not novo_produto_nome or novo_produto_preco is None:
            st.warning("Por favor, preencha todos os campos para cadastrar o produto.")
        elif len(novo_produto_codigo) != 4:
            st.warning("O código do produto deve ter exatamente 4 dígitos.")
        elif novo_produto_codigo in st.session_state.produtos:
            st.warning(f"O código de produto '{novo_produto_codigo}' já está em uso.")
        else:
            # Add the new product
            st.session_state.produtos[novo_produto_codigo] = {
                "nome": novo_produto_nome,
                "preco": novo_produto_preco
            }
            # Save the updated products to the JSON file
            salvar_produtos(st.session_state.produtos)

            st.success(f"Produto '{novo_produto_nome}' (Código: {novo_produto_codigo}) cadastrado com sucesso!")

            # Clear input fields (optional)
            st.session_state.novo_codigo = ""
            st.session_state.novo_nome = ""
            st.session_state.novo_preco = 0.01 # Reset to minimum value
            st.rerun() # Rerun to update the product list in the selectbox

    st.markdown("---") # Separator

    st.subheader("📜 Produtos Cadastrados")
    if st.session_state.produtos:
        # Use columns for layout
        cols = st.columns([1, 2, 1, 1]) # Checkbox | Código | Nome | Preço/kg
        cols[0].write("**Selecionar**")
        cols[1].write("**Código**")
        cols[2].write("**Nome**")
        cols[3].write("**Preço/kg**")

        # Create a list to store selected product codes
        produtos_selecionados_excluir_temp = []

        for codigo, produto in st.session_state.produtos.items():
            col1, col2, col3, col4 = st.columns([1, 2, 1, 1])
            # Use a unique key for each checkbox
            checkbox_state = col1.checkbox("", key=f"select_produto_{codigo}")
            col2.write(codigo)
            col3.write(produto["nome"])
            col4.write(f"R$ {produto['preco']:.2f}")

            if checkbox_state:
                produtos_selecionados_excluir_temp.append(codigo)

        # Store the selected items in session state
        st.session_state.produtos_selecionados_excluir = produtos_selecionados_excluir_temp

        # Add the delete button
        if st.button("Excluir Produtos Selecionados", key="excluir_produtos_button"):
            excluir_produtos_selecionados()


    else:
        st.info("Nenhum produto cadastrado ainda.")

