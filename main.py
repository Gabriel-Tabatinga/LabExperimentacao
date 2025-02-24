import requests
import json
import csv
from datetime import datetime
import time

GITHUB_TOKEN = "abc" # tirei token por segurança""
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Content-Type": "application/json"
}

def get_graphql_query(after_cursor=None):
    cursor_part = f', after: "{after_cursor}"' if after_cursor else ""
    return """
    {
      search(query: "stars:>1 sort:stars-desc", type: REPOSITORY, first: 100%s) {
        edges {
          node {
            ... on Repository {
              nameWithOwner
              createdAt
              primaryLanguage {
                name
              }
              pullRequests(states: MERGED) {
                totalCount
              }
              releases {
                totalCount
              }
              issues {
                totalCount
              }
              closedIssues: issues(states: CLOSED) {
                totalCount
              }
              updatedAt
            }
          }
          cursor
        }
        pageInfo {
          endCursor
          hasNextPage
        }
      }
    }
    """ % cursor_part

def check_rate_limit():
    query = """
    {
      rateLimit {
        limit
        cost
        remaining
        resetAt
      }
    }
    """
    response = requests.post(
        "https://api.github.com/graphql",
        headers=HEADERS,
        json={"query": query},
        verify=False  # Solução temporária para SSL
    )
    if response.status_code == 200:
        data = response.json()
        print("Rate Limit Info:", json.dumps(data, indent=2))
    else:
        print(f"Erro ao verificar rate limit: {response.status_code}")
        print(response.text)

def fetch_repositories(after_cursor=None, retries=3):
    query = get_graphql_query(after_cursor)
    for attempt in range(retries):
        response = requests.post(
            "https://api.github.com/graphql",
            headers=HEADERS,
            json={"query": query},
            verify=False 
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Tentativa {attempt + 1}/{retries} - Erro na requisição: {response.status_code}")
            print(response.text)
            if attempt < retries - 1:
                time.sleep(5)
    print("Falha após todas as tentativas.")
    return None

def calculate_age(created_at):
    created_date = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
    current_date = datetime.now()
    return (current_date - created_date).days / 365.25

def days_since_update(updated_at):
    updated_date = datetime.strptime(updated_at, "%Y-%m-%dT%H:%M:%SZ")
    current_date = datetime.now()
    return (current_date - updated_date).days

def save_to_csv(data, filename="github_repos.csv"):
    headers = [
        "name", "age_years", "pull_requests", "releases", 
        "days_since_update", "primary_language", "closed_issues_ratio"
    ]
    
    with open(filename, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if f.tell() == 0:
            writer.writerow(headers)
        
        for repo in data:
            writer.writerow([
                repo["name"],
                repo["age_years"],
                repo["pull_requests"],
                repo["releases"],
                repo["days_since_update"],
                repo["primary_language"],
                repo["closed_issues_ratio"]
            ])

def collect_data():
    all_data = []
    after_cursor = None
    total_collected = 0

    while total_collected < 1000:
        print(f"Coletando repositórios {total_collected + 1} a {total_collected + 100}...")
        result = fetch_repositories(after_cursor)
        
        if not result or "data" not in result or result["data"] is None:
            print("Parando coleta devido a erro ou ausência de dados.")
            break

        repositories = result["data"]["search"]["edges"]
        page_info = result["data"]["search"]["pageInfo"]

        for edge in repositories:
            node = edge["node"]
            total_issues = node["issues"]["totalCount"]
            closed_issues = node["closedIssues"]["totalCount"]
            
            repo_data = {
                "name": node["nameWithOwner"],
                "age_years": calculate_age(node["createdAt"]),
                "pull_requests": node["pullRequests"]["totalCount"],
                "releases": node["releases"]["totalCount"],
                "days_since_update": days_since_update(node["updatedAt"]),
                "primary_language": node["primaryLanguage"]["name"] if node["primaryLanguage"] else "N/A",
                "closed_issues_ratio": (closed_issues / total_issues) if total_issues > 0 else 0
            }
            all_data.append(repo_data)
            total_collected += 1
            if total_collected >= 1000:
                break

        save_to_csv(all_data[-len(repositories):])
        after_cursor = page_info["endCursor"]
        
        if not page_info["hasNextPage"] or total_collected >= 1000:
            break
        
        time.sleep(5)

    return all_data

if __name__ == "__main__":
    print("Verificando limite de taxa...")
    check_rate_limit()
    print("Iniciando coleta de dados...")
    data = collect_data()
    print(f"Total de repositórios coletados: {len(data)}")
    print("Dados salvos em 'github_repos.csv'")