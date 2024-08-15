import requests
import json
from ics import Calendar, Event

# Configuração de autenticação do Notion API
NOTION_API_KEY = 'secret_XORa2y02Ll03dMruX1tmpAovFwFTND3F7SjZKTQDV17'  # Substitua com sua chave de API do Notion
HEADERS = {
    'Authorization': f'Bearer {NOTION_API_KEY}',
    'Content-Type': 'application/json',
    'Notion-Version': '2022-06-28'
}

# IDs dos bancos de dados que você deseja consultar
DATABASE_IDS = [
    "a49f4a2996a348c08cd2a3ffab19d4c6",
    "67cc01d3c0e84fa0a90fa6e9705cb87c",
    "f155c37287fc48e980296688537065cf",
    "edaecd3dbbd34a2dbc6511bf7a62425c",
    "6c6c73c96cd94588bdfaa2e87a21bf0e",
    "fb86d6c68cfa48a8b5435d603d01e389",
]

# Função para buscar o nome de uma página relacionada pelo ID
def fetch_relation_name(relation_id):
    url = f'https://api.notion.com/v1/pages/{relation_id}'
    response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        page_data = response.json()
        try:
            # Acessar o nome da página relacionada no campo 'properties'
            if 'properties' in page_data:
                for key, value in page_data['properties'].items():
                    # Procurar pelo campo que contém o título (tipo 'title')
                    if value['type'] == 'title' and len(value['title']) > 0:
                        return value['title'][0]['text']['content']  # Retorna o título da página
            return "Nome não encontrado"
        except (KeyError, IndexError):
            return "Erro ao acessar Nome"
    else:
        return "Erro na API"

# Função para consultar o database do Notion
def fetch_notion_data(database_id):
    url = f'https://api.notion.com/v1/databases/{database_id}/query'
    response = requests.post(url, headers=HEADERS)

    if response.status_code == 200:
        print(f"Dados recebidos com sucesso do database {database_id}")
        return response.json()
    else:
        print(f"Erro ao consultar o database {database_id}: {response.status_code}")
        return None

# Função para processar os dados e gerar eventos no iCal
def process_and_generate_ical(database_data, cal):
    if 'results' in database_data:
        for page in database_data['results']:
            properties = page['properties']
            
            # Captura o nome do evento
            try:
                nome = properties['Nome']['title'][0]['text']['content']
            except (KeyError, IndexError):
                nome = "Evento sem título"

            # Captura o valor total e formata como moeda brasileira
            try:
                total = properties['Total']['number']
                total_formatado = f"R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            except (KeyError, IndexError):
                total_formatado = "N/A"

            # Captura a categoria (relacionamento)
            try:
                categoria_id = properties['Categoria']['relation'][0]['id']
                categoria = fetch_relation_name(categoria_id)
            except (KeyError, IndexError):
                categoria = "Sem Categoria"

            # Captura a conta (relacionamento)
            try:
                conta_id = properties['Conta']['relation'][0]['id']
                conta = fetch_relation_name(conta_id)
            except (KeyError, IndexError):
                conta = None

            # Captura o cartão de crédito (relacionamento)
            try:
                cartao_credito_id = properties['Cartão de Crédito']['relation'][0]['id']
                cartao_credito = fetch_relation_name(cartao_credito_id)
            except (KeyError, IndexError):
                cartao_credito = None

            # Captura o cartão Pluxee (relacionamento)
            try:
                cartao_pluxee_id = properties['Cartão Pluxee']['relation'][0]['id']
                cartao_pluxee = fetch_relation_name(cartao_pluxee_id)
            except (KeyError, IndexError):
                cartao_pluxee = None

            # Captura o status
            try:
                status = properties['Status']['status']['name']
            except KeyError:
                status = "Sem Status"

            # Verifica se o campo 'Lembrete' existe e se não é None
            try:
                if properties['Lembrete'] and properties['Lembrete']['date'] and properties['Lembrete']['date']['start']:
                    data = properties['Lembrete']['date']['start']
                else:
                    data = None
            except KeyError:
                data = None
            
            # Se a data for None, pula a criação do evento
            if data:
                # Montar a descrição do evento
                descricao = f"Status: {status}\nCategoria: {categoria}\nTotal: {total_formatado}"

                # Exibir apenas o campo preenchido (Cartão de Crédito, Conta ou Cartão Pluxee)
                if cartao_credito:
                    descricao += f"\nCartão de Crédito: {cartao_credito}"
                elif conta:
                    descricao += f"\nConta: {conta}"
                elif cartao_pluxee:
                    descricao += f"\nCartão Pluxee: {cartao_pluxee}"
                
                # Criar o evento All Day (sem horário definido)
                event = Event()
                event.name = nome
                event.begin = data
                event.make_all_day()  # Define o evento como All Day
                event.description = descricao
                
                # Adicionar ao calendário
                cal.events.add(event)
            else:
                print(f"Evento '{nome}' ignorado por não ter data.")
    else:
        print("A chave 'results' não foi encontrada na resposta da API.")
    
    return cal

# Função principal para gerar o iCal com todos os bancos de dados
def generate_ical_for_databases():
    cal = Calendar()
    
    for db_id in DATABASE_IDS:
        notion_data = fetch_notion_data(db_id)
        
        # Verifica se os dados foram recebidos corretamente
        if notion_data:
            cal = process_and_generate_ical(notion_data, cal)
    
    # Salvar o arquivo .ics com o nome "saidas.ics"
    with open('saidas.ics', 'w') as my_file:
        my_file.writelines(cal)
    print("Arquivo iCal de Saídas gerado com sucesso!")

# Executar a função principal
if __name__ == "__main__":
    generate_ical_for_databases()