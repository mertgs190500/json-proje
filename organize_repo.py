import os
import requests
import json

# --- GÜVENLİK UYARISI: API Kodunu doğrudan buraya YAZMAYIN! ---
# Bu kodu terminalden bir ortam değişkeni olarak alacağız.
API_TOKEN = os.getenv('GITHUB_TOKEN')
if not API_TOKEN:
    raise ValueError("Lütfen GITHUB_TOKEN ortam değişkenini ayarlayın.")

# --- LÜTFEN BU BİLGİLERİ KENDİ PROJENİZE GÖRE DÜZENLEYİN ---
REPO_OWNER = "mertgs190500"  # GitHub kullanıcı adınız
REPO_NAME = "json-proje"      # GitHub proje adınız
BASE_BRANCH = "main"          # Ana dalınızın adı
NEW_BRANCH = "feature/file-organization" # Oluşturulacak yeni dalın adı

HEADERS = {
    "Authorization": f"token {API_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# --- project_core klasörüne taşınacak dosyaların tam listesi ---
CORE_FILES = [
    "uygulama.py", "market_analyzer.py", "voc_analyzer.py",
    "keyword_processor.py", "title_optimizer.py", "mab_optimizer.py",
    "data_loader.py", "csv_ingestor.py", "visual_analyzer.py",
    "feedback_processor.py", "finalv2_config.json", "workflow_schema_v2.json",
    "rule_definitions.json", "data_contracts.json", "product_data.json",
    "documentation.json", "csv_profiles.json", "orchestrator_policy.json",
    "knowledge_base.json", "finalv1.json", "populer_urunler.csv"
]

# --- Ana dizinde kalacak dosyalar ---
IGNORE_FILES = [".gitignore", "README.md"]

def get_latest_commit_sha(branch):
    """Belirtilen daldaki son commit'in SHA kodunu alır."""
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/branches/{branch}"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()["commit"]["sha"]

def get_tree_sha(commit_sha):
    """Belirtilen commit'in ağaç (tree) SHA kodunu alır."""
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/git/commits/{commit_sha}"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()["tree"]["sha"]

def get_all_repo_files(tree_sha):
    """Depodaki tüm dosyaların listesini ve bilgilerini alır."""
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/git/trees/{tree_sha}?recursive=1"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()["tree"]

def create_new_branch(new_branch_name, base_sha):
    """Yeni bir dal oluşturur."""
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/git/refs"
    data = {
        "ref": f"refs/heads/{new_branch_name}",
        "sha": base_sha
    }
    response = requests.post(url, headers=HEADERS, json=data)
    if response.status_code == 422: # Zaten varsa sorun değil
        print(f"Uyarı: '{new_branch_name}' dalı zaten mevcut.")
    else:
        response.raise_for_status()
    print(f"'{new_branch_name}' dalı oluşturuldu veya zaten mevcut.")

def create_new_tree(base_tree_sha, all_files):
    """Taşınmış dosya yapısına göre yeni bir ağaç (tree) nesnesi oluşturur."""
    new_tree = []
    for file_info in all_files:
        path = file_info["path"]
        
        # Sadece dosyalara odaklan, klasörleri atla
        if file_info["type"] != "blob":
            continue
            
        new_path = ""
        if path in CORE_FILES:
            new_path = f"project_core/{path}"
        elif path not in IGNORE_FILES:
            new_path = f"archive/{path}"
        else:
            # .gitignore ve README.md için yolu koru
            new_path = path

        if new_path:
            new_tree.append({
                "path": new_path,
                "mode": file_info["mode"],
                "type": file_info["type"],
                "sha": file_info["sha"]
            })

    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/git/trees"
    data = {"base_tree": base_tree_sha, "tree": new_tree}
    response = requests.post(url, headers=HEADERS, json=data)
    response.raise_for_status()
    print("Yeni dosya yapısı için ağaç (tree) başarıyla oluşturuldu.")
    return response.json()["sha"]

def create_commit(new_tree_sha, parent_commit_sha, message):
    """Yeni ağacı referans alan bir commit oluşturur."""
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/git/commits"
    data = {
        "message": message,
        "tree": new_tree_sha,
        "parents": [parent_commit_sha]
    }
    response = requests.post(url, headers=HEADERS, json=data)
    response.raise_for_status()
    print("Yeni commit başarıyla oluşturuldu.")
    return response.json()["sha"]

def update_branch_ref(branch_name, commit_sha):
    """Dalın en son commit'ini günceller."""
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/git/refs/heads/{branch_name}"
    data = {"sha": commit_sha}
    response = requests.patch(url, headers=HEADERS, json=data)
    response.raise_for_status()
    print(f"'{branch_name}' dalı yeni commit'e güncellendi.")

def create_pull_request(head_branch, base_branch, title, body):
    """Onay için bir Pull Request oluşturur."""
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/pulls"
    data = {
        "title": title,
        "body": body,
        "head": head_branch,
        "base": base_branch
    }
    response = requests.post(url, headers=HEADERS, json=data)
    if response.status_code == 422: # Zaten varsa
        print("Uyarı: Bu Pull Request zaten mevcut olabilir.")
        print(response.json())
    else:
        response.raise_for_status()
        print("Pull Request başarıyla oluşturuldu. Lütfen GitHub'da onaylayın.")
        print(response.json()["html_url"])

def main():
    try:
        print(f"1. '{BASE_BRANCH}' dalındaki son durum alınıyor...")
        latest_sha = get_latest_commit_sha(BASE_BRANCH)
        
        print("2. Yeni bir çalışma dalı oluşturuluyor...")
        create_new_branch(NEW_BRANCH, latest_sha)

        print("3. Mevcut dosya listesi alınıyor...")
        base_tree_sha = get_tree_sha(latest_sha)
        all_files = get_all_repo_files(base_tree_sha)
        
        print("4. Yeni dosya yapısı oluşturuluyor...")
        new_tree_sha = create_new_tree(base_tree_sha, all_files)
        
        print("5. Değişiklikler commit'leniyor...")
        commit_message = "refactor: Organize project file structure via API"
        new_commit_sha = create_commit(new_tree_sha, latest_sha, commit_message)
        
        print(f"6. '{NEW_BRANCH}' dalı güncelleniyor...")
        update_branch_ref(NEW_BRANCH, new_commit_sha)
        
        print("7. Onay için Pull Request oluşturuluyor...")
        pr_title = "Refactor: Project File Organization"
        pr_body = "This PR automatically reorganizes the project files into `project_core` and `archive` folders as requested."
        create_pull_request(NEW_BRANCH, BASE_BRANCH, pr_title, pr_body)

        print("\nİşlem başarıyla tamamlandı!")

    except requests.exceptions.RequestException as e:
        print(f"\nBir Hata Oluştu: {e}")
        if e.response is not None:
            print(f"Hata Detayı: {e.response.text}")

if __name__ == "__main__":
    main()