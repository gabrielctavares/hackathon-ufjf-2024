# Hackathon UFJF 2024

Projeto desenvolvido para o Hackathon da Semana da computação da Universidade Federal de Juiz de Fora (UFJF) em 2024. 
Este repositório contém uma aplicação desenvolvida com Python e utilizando o Streamlit como framework para a interface de usuário.

## Sobre o Projeto

Este projeto foi criado para resolver o seguinte problema: **Consolidar dados em séries temporais utilizando um motor de inferência.**

A solução propõe um sistema inovador que **aplica técnicas de aprendizado de máquina e análise estatística para processar e consolidar dados de séries temporais.**

Este projeto ficou em 4º lugar no Hackathon 2024.

## Estrutura do Projeto

- `data/`: Dados utilizados pelo projeto.
- `database/`: Arquivos relacionados ao banco de dados.
- `services/`: Serviços e lógica do back-end.
- `views/`: Componentes e templates do front-end.
- `app.py`: Arquivo principal da aplicação.
- `requirements.txt`: Dependências necessárias para o projeto.

## Como Executar

1. **Clone o repositório:**

   ```bash
   git clone https://github.com/gabrielctavares/hackathon-ufjf-2024.git
   cd hackathon-ufjf-2024
  
2. **Crie um ambiente virtual e ative-o:**
   ```bash
    python -m venv venv
   
    # No Windows   
    venv\\Scripts\\activate
   
    # No Unix ou MacOS   
    source venv/bin/activate

3. **Instale as dependências:**
   ```bash
    pip install -r requirements.txt
   
4. **Inicie a aplicação com o Streamlit:**
   ```bash
     streamlit run app.py
