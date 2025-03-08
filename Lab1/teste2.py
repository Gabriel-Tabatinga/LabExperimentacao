import requests
import json
import csv
from datetime import datetime
import time

# Token de autenticação do GitHub
# HEADERS = {
#     "Authorization": f"Bearer {GITHUB_TOKEN}",
#     "Content-Type": "application/json"
# }
github_token = ""
graphql_url = "https://api.github.com/graphql"
headers = {"Authorization": f"Bearer {github_token}"}

def fetch_repositories(after_cursor=None):
    query = """
    query ($after: String) {
      search(query: "stars:>1000", type: REPOSITORY, first: 100, after: $after) {
        pageInfo {
          endCursor
          hasNextPage
        }
        nodes {
          nameWithOwner
          createdAt
          primaryLanguage { name }
          releases { totalCount }
          pullRequests(states: MERGED) { totalCount }
          issues {
            totalCount
          }
          closedIssues: issues(states: CLOSED) {
            totalCount
          }
          updatedAt
        }
      }
    }
    """
    
    variables = {"after": after_cursor}
    response = requests.post(graphql_url, json={"query": query, "variables": variables}, headers=headers)
    return response.json()

def collect_data():
    repositories = []
    cursor = None
    count = 0
    
    while count < 1000:
        data = fetch_repositories(cursor)
        search_data = data.get("data", {}).get("search", {})
        
        for repo in search_data.get("nodes", []):
            repositories.append([
                repo["nameWithOwner"],
                repo["createdAt"],
                repo["primaryLanguage"]["name"] if repo["primaryLanguage"] else "Unknown",
                repo["releases"]["totalCount"],
                repo["pullRequests"]["totalCount"],
                repo["issues"]["totalCount"],
                repo["closedIssues"]["totalCount"],
                repo["updatedAt"]
            ])
            count += 1
            if count >= 1000:
                break
        
        if search_data.get("pageInfo", {}).get("hasNextPage"):
            cursor = search_data["pageInfo"]["endCursor"]
        else:
            break
    
    return repositories

def save_to_csv(data, filename="repositorios.csv"):
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Nome", "Criado em", "Linguagem", "Releases", "Pull Requests", "Total Issues", "Issues Fechadas", "Última Atualização"])
        writer.writerows(data)

data = collect_data()
save_to_csv(data)
print("Dados coletados e salvos em 'repositorios.csv'")
