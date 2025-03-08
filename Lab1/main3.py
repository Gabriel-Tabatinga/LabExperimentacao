import requests
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Configurações
GITHUB_API_URL = "https://api.github.com/graphql"
TOKEN = ""  

# Função para fazer a requisição à API do GitHub
def fetch_github_data(query):
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
    }
    response = requests.post(GITHUB_API_URL, json={'query': query}, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Erro na requisição: {response.status_code}")

# Função para processar os dados e salvar em um CSV
def save_to_csv(data, filename='repositorios.csv'):
    repos = []
    for edge in data['data']['search']['edges']:
        repo = edge['node']
        repos.append({
            'nameWithOwner': repo['nameWithOwner'],
            'createdAt': repo['createdAt'],
            'updatedAt': repo['updatedAt'],
            'primaryLanguage': repo['primaryLanguage']['name'] if repo['primaryLanguage'] else None,
            'mergedPullRequests': repo['pullRequests']['totalCount'],
            'releases': repo['releases']['totalCount'],
            'closedIssues': repo['issues']['totalCount'],
            'totalIssues': repo['totalIssues']['totalCount']
        })
    
    df = pd.DataFrame(repos)
    df.to_csv(filename, index=False)

# Função para buscar todos os repositórios com paginação
def fetch_all_repos():
    all_repos = []
    end_cursor = None
    has_next_page = True

    while has_next_page:
        query = """
        {
          search(query: "stars:>1000", type: REPOSITORY, first: 100, after: %s) {
            edges {
              node {
                ... on Repository {
                  nameWithOwner
                  createdAt
                  updatedAt
                  primaryLanguage {
                    name
                  }
                  pullRequests(states: MERGED) {
                    totalCount
                  }
                  releases {
                    totalCount
                  }
                  issues(states: CLOSED) {
                    totalCount
                  }
                  totalIssues: issues {
                    totalCount
                  }
                }
              }
            }
            pageInfo {
              endCursor
              hasNextPage
            }
          }
        }
        """ % (f'"{end_cursor}"' if end_cursor else "null")

        data = fetch_github_data(query)
        repos = data['data']['search']['edges']
        all_repos.extend(repos)

        page_info = data['data']['search']['pageInfo']
        end_cursor = page_info['endCursor']
        has_next_page = page_info['hasNextPage']

    return all_repos

# Função para calcular a idade do repositório em anos
def calculate_age(created_at):
    created_date = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
    now = datetime.now()
    return (now - created_date).days / 365

# Função para calcular o tempo desde a última atualização em dias
def calculate_days_since_last_update(updated_at):
    updated_date = datetime.strptime(updated_at, "%Y-%m-%dT%H:%M:%SZ")
    now = datetime.now()
    return (now - updated_date).days

# Função para analisar e visualizar os dados
def analyze_and_visualize_data(filename='repositorios.csv'):
    df = pd.read_csv(filename)

    # Calcular a idade dos repositórios
    df['age'] = df['createdAt'].apply(calculate_age)

    # Calcular o tempo desde a última atualização
    df['days_since_last_update'] = df['updatedAt'].apply(calculate_days_since_last_update)

    # Calcular a razão de issues fechadas
    df['closed_issues_ratio'] = df['closedIssues'] / df['totalIssues']

    # Exibir estatísticas básicas
    print("Estatísticas básicas:")
    print(df.describe())

    # Visualização 1: Média de pull requests aceitas por linguagem
    df_grouped = df.groupby('primaryLanguage')['mergedPullRequests'].mean().sort_values(ascending=False)
    df_grouped.plot(kind='bar', figsize=(10, 6))
    plt.title('Média de Pull Requests Aceitas por Linguagem')
    plt.xlabel('Linguagem')
    plt.ylabel('Média de Pull Requests Aceitas')
    plt.show()

    # Visualização 2: Média de releases por linguagem
    df_grouped = df.groupby('primaryLanguage')['releases'].mean().sort_values(ascending=False)
    df_grouped.plot(kind='bar', figsize=(10, 6))
    plt.title('Média de Releases por Linguagem')
    plt.xlabel('Linguagem')
    plt.ylabel('Média de Releases')
    plt.show()

    # Visualização 3: Média de dias desde a última atualização por linguagem
    df_grouped = df.groupby('primaryLanguage')['days_since_last_update'].mean().sort_values(ascending=False)
    df_grouped.plot(kind='bar', figsize=(10, 6))
    plt.title('Média de Dias desde a Última Atualização por Linguagem')
    plt.xlabel('Linguagem')
    plt.ylabel('Média de Dias desde a Última Atualização')
    plt.show()

    # Visualização 4: Razão de issues fechadas por linguagem
    df_grouped = df.groupby('primaryLanguage')['closed_issues_ratio'].mean().sort_values(ascending=False)
    df_grouped.plot(kind='bar', figsize=(10, 6))
    plt.title('Razão de Issues Fechadas por Linguagem')
    plt.xlabel('Linguagem')
    plt.ylabel('Razão de Issues Fechadas')
    plt.show()

# Executar a consulta com paginação e salvar os dados
all_repos = fetch_all_repos()
save_to_csv({'data': {'search': {'edges': all_repos}}})

# Analisar e visualizar os dados
analyze_and_visualize_data()