'''
Instruções de utilização:

1. Abrir o terminal
2. Mudar para a diretoria onde está guardada o ficheiro app.py usando o comando: cd "C:\...\app.py"
3. Instalar os packages gradio e openai
4. Copiar .env.example para .env e preencher AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY
   e AZURE_OPENAI_ASSISTANT_ID (ou definir estas variáveis de ambiente no terminal)
5. Correr a seguinte instrução no terminal: python app.py
6. Clicar no link após a execução do código no terminal (http://127.0.0.1:7860)

Nota adicional: É necessário o Python estar instalado para iniciar a aplicação.
'''


# ========== Importar livrarias ==========
import gradio as gr
import os
import re
import time
from openai import AzureOpenAI

# ========== Azure OpenAI Configurações ==========
# Carregar variáveis do ficheiro .env local (não versionado), se existir
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(env_path):
    with open(env_path, encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if linha and not linha.startswith("#") and "=" in linha:
                chave, valor = linha.split("=", 1)
                os.environ.setdefault(chave.strip(), valor.strip())

variaveis_em_falta = [v for v in ("AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ASSISTANT_ID")
                      if not os.environ.get(v)]
if variaveis_em_falta:
    raise RuntimeError(f"Defina as variáveis de ambiente {', '.join(variaveis_em_falta)} antes de correr a aplicação.")

azure_endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]
api_key = os.environ["AZURE_OPENAI_API_KEY"]
assistant_id = os.environ["AZURE_OPENAI_ASSISTANT_ID"]

client = AzureOpenAI(
    azure_endpoint=azure_endpoint,
    api_key=api_key,
    api_version="2024-05-01-preview"
)

conversations = {}

# ========== Funções Utilitárias ==========

def limpar_anotacoes(texto):
    return re.sub(r"【.*?†source】", "", texto)

def filtrar_respostas_por_fonte(messages):
    """
    Dá prioridade a respostas com fontes de .txt. Usa PDFs apenas se não houver .txt.
    """
    conversation = []
    user_msg = None
    prioridade_txt = []
    secundario_pdf = []

    for msg in reversed(messages.data):
        if msg.role == "user":
            user_msg = msg.content[0].text.value
        elif msg.role == "assistant" and user_msg:
            resposta = msg.content[0].text.value
            fontes = re.findall(r"【.*?source: (.*?)】", resposta)
            if any(".txt" in fonte.lower() for fonte in fontes):
                prioridade_txt.append((user_msg, limpar_anotacoes(resposta)))
            else:
                secundario_pdf.append((user_msg, limpar_anotacoes(resposta)))
            user_msg = None

    return prioridade_txt if prioridade_txt else secundario_pdf

# ========== Função Principal de Chat ==========

def chat_with_azure(thread_id, history, user_input, convo_selector):
    history = history or []

    # Enviar mensagem do utilizador
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=user_input
    )

    # Executar assistente
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id
    )

    while run.status in ["queued", "in_progress", "cancelling"]:
        time.sleep(1)
        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)

    if run.status == "completed":
        messages = client.beta.threads.messages.list(thread_id=thread_id)
        conversation = filtrar_respostas_por_fonte(messages)

        # Dar nome à conversa com base na primeira resposta do assistente
        if not convo_selector or convo_selector == "None":
            assistant_messages = [msg for msg in messages.data if msg.role == "assistant"]
            if assistant_messages:
                first_response = assistant_messages[-1].content[0].text.value.strip()
                title = re.split(r'[.\n]', first_response)[0][:80].strip()
                title = title or f"Conversa {len(conversations) + 1}"
                convo_selector = title
                conversations[convo_selector] = {"thread_id": thread_id, "history": conversation}
        else:
            conversations[convo_selector]["history"] = conversation

        history = conversation
    else:
        error_msg = f"Erro: status da execução {run.status}"
        history.append((user_input, error_msg))

    return history, thread_id, "", gr.update(choices=list(conversations.keys()), value=convo_selector)

# ========== Nova Conversa ==========

def new_chat():
    new_thread_id = client.beta.threads.create().id
    return [], new_thread_id, "", gr.update(choices=list(conversations.keys()), value=None)

def load_conversation(selected):
    data = conversations.get(selected, {"thread_id": client.beta.threads.create().id, "history": []})
    return data["history"], data["thread_id"]

# ========== Interface Gradio ==========

with gr.Blocks(css="""
    body { background-color: #fff5f5; margin: 0; }
    .gradio-container {
        font-family: 'Segoe UI', sans-serif;
        color: #7c1c1c;
        padding: 1rem 1.5rem;
    }
    #app-banner img {
        width: 100% !important;
        height: auto !important;
        display: block;
        border-radius: 8px 8px 0 0;
        object-fit: cover;
        max-height: 150px;
    }
    .chat-input-wrapper {
        position: relative;
        width: 100%;
        display: flex;
        align-items: center;
        min-height: 3.5rem;
    }
    .chat-textbox textarea {
        padding-right: 3rem !important;
        resize: none !important;
        border-radius: 8px;
        border: 1px solid #ffcccc;
        font-size: 1rem;
        line-height: 1.3rem;
        flex-grow: 1;
    }
    .send-btn {
        position: absolute;
        right: 1.1rem;
        top: 65%;
        transform: translateY(-50%);
        background-color: transparent;
        color: #b30000;
        border: none;
        cursor: pointer;
        font-size: 1.4rem;
        padding: 0;
        width: 1.8rem;
        height: 1.8rem;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: color 0.2s ease;
        z-index: 10;
    }
    .send-btn:hover { color: #ff4d4d; }
    .sidebar {
        background-color: #eb3434;
        padding: 1rem;
        border-radius: 8px;
        height: 100%;
    }
    .sidebar-title {
        font-weight: bold;
        color: #FFFFFF;
        margin-bottom: 0.5rem;
    }
""") as demo:

    sidebar_visible = gr.State(True)

    with gr.Column(elem_id="app-banner", scale=12):
        gr.Image(value="banner.png", show_label=False, interactive=False)

    with gr.Row():
        with gr.Column(scale=1, elem_classes="sidebar", visible=True) as sidebar_col:
            gr.Markdown("### Conversas", elem_classes="sidebar-title")
            convo_selector = gr.Dropdown(choices=[], label=None, interactive=True)
            new_chat_btn = gr.Button("Nova Conversa", elem_id="new-chat")

        with gr.Column(scale=5):
            toggle_sidebar_btn = gr.Button("☰ Mostrar/Ocultar Conversas", elem_id="toggle-sidebar-btn")
            chatbot = gr.Chatbot(label="MySavings", show_copy_button=True)
            state = gr.State([])
            thread_id = gr.State(client.beta.threads.create().id)

            with gr.Row():
                with gr.Column(elem_classes="chat-input-wrapper"):
                    msg = gr.Textbox(placeholder="Escreve aqui...", label=None, lines=2, elem_classes="chat-textbox")
                    send_btn = gr.Button("➤", elem_classes="send-btn")

    def toggle_sidebar(visible):
        return gr.update(visible=not visible), not visible

    toggle_sidebar_btn.click(toggle_sidebar, inputs=sidebar_visible, outputs=[sidebar_col, sidebar_visible])
    msg.submit(chat_with_azure, inputs=[thread_id, state, msg, convo_selector], outputs=[chatbot, thread_id, msg, convo_selector])
    send_btn.click(chat_with_azure, inputs=[thread_id, state, msg, convo_selector], outputs=[chatbot, thread_id, msg, convo_selector])
    new_chat_btn.click(new_chat, outputs=[chatbot, thread_id, msg, convo_selector])
    convo_selector.change(load_conversation, inputs=[convo_selector], outputs=[chatbot, thread_id])

if __name__ == "__main__":
    demo.launch()