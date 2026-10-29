# Insurance Savings AI Assistant

![Python](https://img.shields.io/badge/Python-3.x-3776AB?logo=python&logoColor=white)
![Azure OpenAI](https://img.shields.io/badge/Azure%20OpenAI-0078D4?logo=microsoftazure&logoColor=white)
![Gradio](https://img.shields.io/badge/Gradio-F97316)

**MySavings** is a retrieval-augmented chatbot that answers customer questions about savings and retirement products, such as PPR (the Portuguese retirement savings plan), for a Portuguese insurance company. Its answers are grounded in the official product documentation and current Euribor rates.

> **Confidentiality:** This project was developed for a real company. The company's name and its data have been hidden for confidentiality reasons.

## Problem

Customers regularly ask about rates, conditions and how savings products work. These questions take up the time of support staff and agents, and the answers have to be accurate and consistent with official documents. The goal was to give customers instant, reliable answers without inventing product terms.

## Solution

**1. Knowledge base**
- Official product documentation, a regulatory reference document and up-to-date Euribor rates.
- All of it is indexed by an **Azure OpenAI Assistant** with **file search** (retrieval).

**2. Source prioritisation**
- Answers grounded in `.txt` sources, such as current rates, are preferred over PDF-based answers. This keeps time-sensitive figures accurate.
- Citation markers are removed so the reply reads cleanly.

**3. Web app (Gradio)**
- Branded chat interface.
- Collapsible sidebar to create, rename and switch between **multiple conversations**. Each conversation is its own Assistants API thread.
- Copy button on every answer.

## Repository structure

```
Insurance-Savings-Assistance/
├── app.py            # Gradio chat app connected to the Azure OpenAI Assistant
├── banner.png        # Banner image
├── .env.example      # Settings template
├── requirements.txt
└── README.md
```

> **Note:** The knowledge-base documents are not included in this repository. They have to be uploaded to your own Azure OpenAI Assistant.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # then fill in your Azure OpenAI settings
python app.py
```

Open http://127.0.0.1:7860 in your browser.

The app reads the following settings from `.env` or from environment variables:

| Variable | Description |
|----------|-------------|
| `AZURE_OPENAI_ENDPOINT` | Your Azure OpenAI resource endpoint |
| `AZURE_OPENAI_API_KEY` | API key for that resource |
| `AZURE_OPENAI_ASSISTANT_ID` | ID of an Assistant with file search and the knowledge-base files uploaded |

`.env` is git-ignored, so credentials are never committed.

## Tech stack

Python · Azure OpenAI (Assistants API, file search) · openai SDK · Gradio

## Author

**Vinícius Pinto** · [GitHub](https://github.com/vilallo)
