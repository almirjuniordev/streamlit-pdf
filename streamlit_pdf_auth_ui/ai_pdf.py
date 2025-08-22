import streamlit as st
from pdf2image import convert_from_bytes
import pytesseract
from PIL import Image
import io
import re
import os
import time

# Configuração do Tesseract para Docker (Linux)
# pytesseract.pytesseract.tesseract_cmd = r"C:/Program Files/Tesseract-OCR/tesseract.exe"  # Windows
# No Docker, o Tesseract está instalado no PATH do sistema

def run_ai_pdf():
    """Função principal do AI PDF Scanner"""
    # CONFIGURAÇÃO
    st.set_page_config(page_title="AI BOT Scanner", layout="wide")
    col1, col2 = st.columns([10, 2])
    with col1:
        st.title("📄 AI para PDFs Escaneados")
    with col2:
        # st.image("logo.png", width=280)  # Comentado pois não temos logo no Docker
        pass

    # Obter nome do usuário logado
    username = st.session_state.get('USERNAME', 'unknown_user')
    
    protocolo = st.text_input("Informe o número do protocolo!")
    
    # Armazenar arquivos processados na sessão
    if "processed_files" not in st.session_state:
        st.session_state["processed_files"] = []
    
    if "protocolo_atual" not in st.session_state:
        st.session_state["protocolo_atual"] = ""
    
    if "nome_pasta" not in st.session_state:
        st.session_state["nome_pasta"] = ""
    
    if "timestamp_pasta" not in st.session_state:
        st.session_state["timestamp_pasta"] = ""

    # Botão para criar diretório/nomear pasta
    if st.button("📁 Criar Nome da Pasta"):
        if protocolo:
            # Gerar timestamp único para este processamento
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            nome_pasta = f"protocolo_{protocolo}_{username}"
            timestamp_pasta = f"{timestamp}_{username}_{protocolo}"
            
            st.session_state["nome_pasta"] = nome_pasta
            st.session_state["protocolo_atual"] = protocolo
            st.session_state["timestamp_pasta"] = timestamp_pasta
            
            st.success(f"✅ Pasta criada: '{nome_pasta}'")
            st.info(f"🕒 Timestamp único: {timestamp_pasta}")
            st.info("Agora você pode fazer upload dos PDFs. Os arquivos serão organizados em uma pasta única com timestamp.")
        else:
            st.error("⚠️ Por favor, insira o número do protocolo antes de criar a pasta.")

    uploaded_files = st.file_uploader("Faça upload de PDFs escaneados", type=["pdf"], accept_multiple_files=True)
    
    # Aviso sobre uso simultâneo
    st.info("💡 **Dica**: Para melhor performance, evite processar múltiplos PDFs simultaneamente em diferentes abas.")

    # FUNÇÕES
    def preprocess_variants(image):
        """Retorna uma lista de variações da imagem pré-processada para OCR"""
        variants = []

        # Versão 1: Mais clara
        gray1 = image.convert("L")
        bin1 = gray1.point(lambda x: 0 if x < 180 else 255)
        variants.append(bin1)

        # Versão 2: Mais escura/adaptativa
        gray2 = image.convert("L")
        bin2 = gray2.point(lambda x: 0 if x < 160 else 255)
        variants.append(bin2)

        return variants

    def extract_card_number(text):
        pattern = r"(?:Nº|No|Número|Guia)\s*(?:Guia)?\s*(?:no|nº|número)?\s*Prestador[:\s]*([0-9]{6,})"
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1) if match else None

    def reduzir_ou_dividir_pdf(pdf_bytes, max_mb=200, max_partes=10, dpi_inicial=300, dpi_min=100, qualidade_jpeg=95):
        """
        Divide o PDF em partes de até `max_mb` MB (padrão: 200MB).
        Gera apenas o número necessário de partes, com máximo de `max_partes`.
        Reduz qualidade automaticamente se necessário.
        """
        dpi_atual = dpi_inicial
        qualidade_atual = qualidade_jpeg

        while dpi_atual >= dpi_min:
            imagens = convert_from_bytes(pdf_bytes, dpi=dpi_atual)
            partes = []
            paginas_atual = []
            tamanho_atual = 0

            for imagem in imagens:
                buffer_temp = io.BytesIO()
                imagem.save(buffer_temp, format="PDF", quality=qualidade_atual)
                tamanho_pagina = len(buffer_temp.getvalue())

                if (tamanho_atual + tamanho_pagina) > (max_mb * 1024 * 1024):
                    if paginas_atual:
                        buffer_parte = io.BytesIO()
                        paginas_atual[0].save(
                            buffer_parte, format="PDF", save_all=True,
                            append_images=paginas_atual[1:], quality=qualidade_atual
                        )
                        partes.append(buffer_parte.getvalue())

                    paginas_atual = [imagem]
                    tamanho_atual = tamanho_pagina
                else:
                    paginas_atual.append(imagem)
                    tamanho_atual += tamanho_pagina

            # Salvar a última parte
            if paginas_atual:
                buffer_parte = io.BytesIO()
                paginas_atual[0].save(
                    buffer_parte, format="PDF", save_all=True,
                    append_images=paginas_atual[1:], quality=qualidade_atual
                )
                partes.append(buffer_parte.getvalue())

            # ✅ Aqui está o controle correto: só retorna se o número de partes está dentro do limite
            if len(partes) <= max_partes:
                return partes

            # Se ultrapassou, reduz a qualidade e tenta novamente
            dpi_atual -= 50
            qualidade_atual = max(50, qualidade_atual - 10)

        # Se não foi possível dividir com qualidade reduzida
        raise ValueError("Não foi possível dividir o PDF em até 10 partes de 3MB, mesmo com qualidade reduzida.")

    def preprocess_image(image):
        gray = image.convert("L")  # Grayscale
        # Binarização com threshold adaptativo
        return gray.point(lambda x: 0 if x < 160 else 255)

    # Função para criar estrutura de diretórios
    def criar_estrutura_diretorios():
        """Cria a estrutura de diretórios para organizar os arquivos processados"""
        try:
            # Criar diretório base se não existir
            base_dir = "/app/processed_pdfs"
            if not os.path.exists(base_dir):
                os.makedirs(base_dir, exist_ok=True)
            
            # Criar diretório específico para este processamento
            if st.session_state.get("timestamp_pasta"):
                timestamp_dir = os.path.join(base_dir, st.session_state["timestamp_pasta"])
                if not os.path.exists(timestamp_dir):
                    os.makedirs(timestamp_dir, exist_ok=True)
                return timestamp_dir
        except Exception as e:
            st.warning(f"⚠️ Não foi possível criar estrutura de diretórios: {str(e)}")
        return None

    # NOVA LÓGICA: OCR antes da compressão com otimizações
    def encontrar_numero_guia(pdf_bytes):
        try:
            # Reduzir DPI para economizar memória e CPU
            imagens = convert_from_bytes(pdf_bytes, dpi=200)  # Era 300, agora 200
            
            # Limitar a busca apenas na primeira página para velocidade
            for page_index, imagem in enumerate(imagens[:1]):  # Só primeira página
                angles = [0, 90, -90, 180]
                for angle in angles:
                    rotated = imagem.rotate(angle, expand=True)

                    for variant in preprocess_variants(rotated):
                        # Configuração otimizada para velocidade
                        config = r'--oem 1 --psm 6'  # Mais rápido que oem 3
                        text = pytesseract.image_to_string(variant, lang="por+eng", config=config)
                        numero = extract_card_number(text)
                        if numero:
                            return numero, len(imagens)
            
            # Se não encontrou na primeira página, tenta segunda (com timeout)
            if len(imagens) > 1:
                import signal
                
                def timeout_handler(signum, frame):
                    raise TimeoutError("OCR timeout")
                
                # Timeout de 30 segundos para evitar travamento
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(30)
                
                try:
                    imagem = imagens[1]
                    angles = [0, 90, -90, 180]
                    for angle in angles:
                        rotated = imagem.rotate(angle, expand=True)
                        for variant in preprocess_variants(rotated):
                            config = r'--oem 1 --psm 6'
                            text = pytesseract.image_to_string(variant, lang="por+eng", config=config)
                            numero = extract_card_number(text)
                            if numero:
                                signal.alarm(0)  # Cancelar timeout
                                return numero, len(imagens)
                except TimeoutError:
                    st.warning("⚠️ Timeout no OCR da segunda página. Continuando...")
                finally:
                    signal.alarm(0)  # Cancelar timeout
                    
        except Exception as e:
            st.error(f"❌ Erro no OCR: {str(e)}")
            
        return None, len(imagens)

    # PROCESSAMENTO PRINCIPAL
    if uploaded_files and st.session_state["nome_pasta"]:
        # Verificar se a pasta foi criada
        if not st.session_state["nome_pasta"]:
            st.error("⚠️ Crie o nome da pasta antes de processar os arquivos.")
            return
        
        # VERIFICAR SE JÁ EXISTEM ARQUIVOS PROCESSADOS - EVITAR REPROCESSAMENTO
        if st.session_state.get("processed_files", []):
            st.info("✅ **Arquivos já processados!** Use a seção de download abaixo para baixar os arquivos.")
            
            # Botão para forçar reprocessamento se necessário
            if st.button("🔄 Reprocessar Arquivos (substituirá os arquivos atuais)"):
                st.session_state["processed_files"] = []
                st.session_state["timestamp_pasta"] = ""  # Resetar timestamp para gerar novo
                st.session_state["processing_lock"] = False
                st.rerun()
            return
        
        # Controle de concorrência - verificar se já está processando
        if "processing_lock" not in st.session_state:
            st.session_state["processing_lock"] = False
        
        if st.session_state["processing_lock"]:
            st.warning("⚠️ Processamento em andamento. Aguarde a conclusão antes de iniciar outro.")
            return
        
        # Ativar lock de processamento
        st.session_state["processing_lock"] = True
        
        # Verificar tamanho total dos arquivos antes do processamento
        total_upload_size = sum(len(file.read()) for file in uploaded_files)
        total_upload_size_mb = total_upload_size / (1024 * 1024)
        
        if total_upload_size_mb > 1000:  # Mais de 1GB
            st.error(f"❌ Arquivos muito grandes detectados. Tamanho total: {total_upload_size_mb:.1f} MB. Recomendamos processar arquivos menores.")
            return
        
        # Resetar arquivos para leitura
        for file in uploaded_files:
            file.seek(0)
        
        start_time = time.time()
        sucesso = 0
        compactados = 0
        nao_encontrados = 0
        processed_files = []

        for uploaded_file in uploaded_files:
            st.divider()
            st.subheader(f"📄 Processando: {uploaded_file.name}")

            original_pdf_bytes = uploaded_file.read()
            tamanho_mb = len(original_pdf_bytes) / (1024 * 1024)

            # EXTRAIR NÚMERO ANTES DE VERIFICAR TAMANHO
            with st.spinner("🔍 Realizando a leitura do arquivo..."):
                numero_guia, total_paginas = encontrar_numero_guia(original_pdf_bytes)

            st.info(f"Total de páginas no PDF: {total_paginas}")

            if numero_guia:
                st.success(f"🔢 Número da guia encontrado: {numero_guia}")
            else:
                st.warning("⚠️ Número 'Nº Guia no Prestador:' não encontrado na primeira página.")
            
                                # REDUZIR SE NECESSÁRIO
            if tamanho_mb > 200:
                st.warning(f"⚠️ Arquivo excede 200MB ({tamanho_mb:.2f} MB). Tentando dividir e reduzir qualidade automaticamente...")

                try:
                    partes_pdf = reduzir_ou_dividir_pdf(original_pdf_bytes, max_mb=200, max_partes=10)
                    compactados += 1
                except ValueError as e:
                    st.error(f"❌ Erro ao processar PDF: {e}")
                    continue
            else:
                partes_pdf = [original_pdf_bytes]

            # Processar e armazenar arquivos na sessão
            if numero_guia:
                for idx, parte in enumerate(partes_pdf):
                    sufixo_parte = f"_GUIA_DOC{idx+1}.pdf"
                    nome_arquivo = f"{numero_guia}{sufixo_parte}"
                    
                    processed_files.append({
                        'nome': nome_arquivo,
                        'dados': parte,
                        'tipo': 'com_guia',
                        'numero_guia': numero_guia
                    })
                st.success(f"✅ PDF processado: {numero_guia}_GUIA_DOC*.pdf")
                sucesso += 1
            else:
                for idx, parte in enumerate(partes_pdf):
                    sufixo_parte = f"_SEM_GUIA_DOC{idx+1}.pdf"
                    nome_arquivo = f"SEM_GUIA_{uploaded_file.name.replace('.pdf', '')}{sufixo_parte}"
                    
                    processed_files.append({
                        'nome': nome_arquivo,
                        'dados': parte,
                        'tipo': 'sem_guia',
                        'numero_guia': None
                    })

                st.info(f"📂 PDF sem número processado: {nome_arquivo}")
                nao_encontrados += 1

        # Armazenar arquivos processados na sessão
        st.session_state["processed_files"] = processed_files

        # RESUMO
        total = len(uploaded_files)
        st.divider()
        st.header("📊 Resumo do processamento")
        st.markdown(f"""
        - 📂 Arquivos processados: **{total}**
        - ✅ Arquivos com número da guia encontrado: **{sucesso}**
        - 📉 Arquivos compactados (reduzidos/divididos): **{compactados}**
        - ❌ Arquivos sem número da guia: **{nao_encontrados}**
        """)
        elapsed_time = time.time() - start_time
        minutes, seconds = divmod(int(elapsed_time), 60)
        st.info(f"🕒 Tempo total de execução: **{minutes} min {seconds} seg**")
        
        # Liberar lock de processamento
        st.session_state["processing_lock"] = False

    elif uploaded_files and not st.session_state["nome_pasta"]:
        st.error("⚠️ Crie o nome da pasta antes de processar os arquivos.")
    elif uploaded_files and not protocolo:
        st.error("⚠️ Informe o número do protocolo antes de criar a pasta.")

    # SEÇÃO DE DOWNLOAD DOS ARQUIVOS PROCESSADOS
    # Verificar se há arquivos processados disponíveis para download
    if st.session_state.get("processed_files", []):
        st.divider()
        st.header("💾 Download dos Arquivos Processados")
        st.info(f"📁 Pasta: {st.session_state['nome_pasta']}")
        st.info(f"🕒 Timestamp: {st.session_state.get('timestamp_pasta', 'N/A')}")
        st.success("✅ **Arquivos já processados!** Clique nos botões abaixo para fazer download (sem reprocessamento).")
        
        # Informações sobre a estrutura de diretórios
        with st.expander("📋 **Informações sobre Organização dos Arquivos**", expanded=False):
            st.markdown(f"""
            ### 🗂️ **Estrutura de Organização:**
            
            **Diretório Base:** `/app/processed_pdfs/`
            
            **Seu Processamento:** `{st.session_state.get('timestamp_pasta', 'N/A')}/`
            
            **Estrutura Completa:**
            ```
            /app/processed_pdfs/
            └── {st.session_state.get('timestamp_pasta', 'timestamp_user_protocolo')}/
                ├── arquivo1.pdf
                ├── arquivo2.pdf
                └── ...
            ```
            
            **Benefícios:**
            - ✅ **Isolamento**: Cada processamento fica em pasta única
            - ✅ **Concorrência**: Múltiplos usuários podem processar simultaneamente
            - ✅ **Rastreabilidade**: Timestamp identifica quando foi processado
            - ✅ **Sem Conflitos**: Evita sobrescrita de arquivos
            """)
        
        # Calcular tamanho total dos arquivos
        total_size = sum(len(file_info['dados']) for file_info in st.session_state["processed_files"])
        total_size_mb = total_size / (1024 * 1024)
        
        st.info(f"📏 Tamanho total: {total_size_mb:.2f} MB")
        
        # Aviso para arquivos grandes
        if total_size_mb > 100:  # Mais de 100MB
            st.warning("⚠️ Arquivos muito grandes detectados. Recomendamos download individual para melhor performance.")
        
        # Opções de download baseadas no tamanho
        col1, col2 = st.columns(2)
        
        with col1:
            # Download rápido (sem compressão) para arquivos menores
            if total_size_mb < 100:  # Menos de 100MB
                if st.button("⚡ Download Rápido (ZIP sem compressão)"):
                    import zipfile
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    try:
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_STORED) as zip_file:  # Sem compressão
                            total_files = len(st.session_state["processed_files"])
                            
                            for i, file_info in enumerate(st.session_state["processed_files"]):
                                progress = (i + 1) / total_files
                                progress_bar.progress(progress)
                                status_text.text(f"Adicionando arquivo {i+1}/{total_files}: {file_info['nome']}")
                                zip_file.writestr(file_info['nome'], file_info['dados'])
                        
                        zip_buffer.seek(0)
                        progress_bar.progress(1.0)
                        status_text.text("✅ ZIP criado com sucesso!")
                        
                        st.download_button(
                            label="💾 Download ZIP Rápido",
                            data=zip_buffer.getvalue(),
                            file_name=f"{st.session_state['nome_pasta']}_rapido.zip",
                            mime="application/zip"
                        )
                        
                    except Exception as e:
                        st.error(f"❌ Erro ao criar ZIP: {str(e)}")
                    finally:
                        progress_bar.empty()
                        status_text.empty()
        
        with col2:
            # Download comprimido para arquivos maiores
            if total_size_mb < 500:  # Limite de 500MB para ZIP
                if st.button("📦 Download de Todos os Arquivos (ZIP)"):
                    import zipfile
                    
                    # Mostrar progresso detalhado
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    try:
                        # Criar arquivo ZIP em memória com compressão otimizada
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zip_file:
                            total_files = len(st.session_state["processed_files"])
                            
                            for i, file_info in enumerate(st.session_state["processed_files"]):
                                # Atualizar progresso
                                progress = (i + 1) / total_files
                                progress_bar.progress(progress)
                                status_text.text(f"Adicionando arquivo {i+1}/{total_files}: {file_info['nome']}")
                                
                                # Adicionar arquivo ao ZIP
                                zip_file.writestr(file_info['nome'], file_info['dados'])
                        
                        zip_buffer.seek(0)
                        progress_bar.progress(1.0)
                        status_text.text("✅ ZIP criado com sucesso!")
                        
                        # Botão de download do ZIP
                        st.download_button(
                            label="💾 Download ZIP Completo",
                            data=zip_buffer.getvalue(),
                            file_name=f"{st.session_state['nome_pasta']}_processados.zip",
                            mime="application/zip"
                        )
                        
                    except Exception as e:
                        st.error(f"❌ Erro ao criar ZIP: {str(e)}")
                    finally:
                        # Limpar indicadores de progresso
                        progress_bar.empty()
                        status_text.empty()
            else:
                st.error("❌ Arquivo muito grande para download ZIP. Use download individual.")
        
        # Download individual de cada arquivo
        st.subheader("📄 Download Individual")
        for i, file_info in enumerate(st.session_state["processed_files"]):
            file_size_mb = len(file_info['dados']) / (1024 * 1024)
            
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.write(f"**{file_info['nome']}**")
                if file_info['tipo'] == 'com_guia':
                    st.success(f"Guia: {file_info['numero_guia']}")
                else:
                    st.warning("Sem número de guia")
            
            with col2:
                st.write(f"📏 {file_size_mb:.1f} MB")
            
            with col3:
                st.download_button(
                    label="💾 Download",
                    data=file_info['dados'],
                    file_name=file_info['nome'],
                    mime="application/pdf",
                    key=f"download_{i}"
                )
        
        # Botão para limpar arquivos processados
        if st.button("🗑️ Limpar Arquivos Processados"):
            # Limpar arquivos da memória
            st.session_state["processed_files"] = []
            st.session_state["protocolo_atual"] = ""
            st.session_state["nome_pasta"] = ""
            st.session_state["timestamp_pasta"] = ""
            st.session_state["processing_lock"] = False
            
            # Forçar limpeza de memória mais agressiva
            import gc
            gc.collect()
            
            # Limpar cache do Streamlit
            st.cache_data.clear()
            st.cache_resource.clear()
            
            st.success("✅ Arquivos removidos da memória com sucesso!")
            # Removido st.rerun() para evitar reprocessamento desnecessário

    # RODAPÉ
    footer_html = """
    <div style='text-align: center;'>
    <p>Developed by EDS Tecnologia da Informação - <small>v8 18/08/2025</small></p>
    </div>
    """
    st.markdown(footer_html, unsafe_allow_html=True)

# Executar a função principal
if __name__ == "__main__":
    run_ai_pdf()
