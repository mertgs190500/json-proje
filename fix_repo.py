import os
import requests
import json

# --- Gerekli Bilgiler ---
API_TOKEN = os.getenv('GITHUB_TOKEN')
REPO_OWNER = "mertgs190500"
REPO_NAME = "json-proje"
BASE_BRANCH = "main"
NEW_BRANCH = "fix/final-organization" # Yeni ve temiz bir dal adı

if not API_TOKEN:
    raise ValueError("Lütfen GITHUB_TOKEN ortam değişkenini ayarlayın.")

HEADERS = {
    "Authorization": f"token {API_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# --- OLMASI GEREKEN YER: project_core ---
CORE_FILES = [
    "uygulama.py", "market_analyzer.py", "voc_analyzer.py",
    "keyword_processor.py", "title_optimizer.py", "mab_optimizer.py",
    "data_loader.py", "csv_ingestor.py", "visual_analyzer.py",
    "feedback_processor.py", "finalv2_config.json", "workflow_schema_v2.json",
    "rule_definitions.json", "data_contracts.json", "product_data.json",
    "documentation.json", "csv_profiles.json", "orchestrator_policy.json",
    "knowledge_base.json", "finalv1.json", "populer_urunler.csv"
]

# --- OLMASI GEREKEN YER: Ana Dizin ---
ROOT_FILES = [".gitignore", "README.md"]

def get_latest_commit_sha(branch):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/branches/{branch}"
    r = requests.get(url, headers=HEADERS); r.raise_for_status(); return r.json()["commit"]["sha"]

def create_new_branch(new_branch, base_sha):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/git/refs"
    data = {"ref": f"refs/heads/{new_branch}", "sha": base_sha}
    r = requests.post(url, headers=HEADERS, json=data)
    if r.status_code == 422: print(f"Uyarı: '{new_branch}' dalı zaten mevcut.")
    else: r.raise_for_status()

def get_all_files_from_branch(branch):
    latest_sha = get_latest_commit_sha(branch)
    tree_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/git/trees/{latest_sha}?recursive=1"
    r = requests.get(tree_url, headers=HEADERS); r.raise_for_status(); return r.json()["tree"]

def create_clean_tree(all_files):
    new_tree = []
    seen_files = set() # Yinelenen dosyaları engellemek için

    for file_info in all_files:
        if file_info["type"] != "blob": continue
        
        # Dosya adını ve yolunu normalize et
        original_path = file_info["path"]
        base_name = os.path.basename(original_path)

        # Eğer bu dosyayı daha önce işlediysek atla
        if base_name in seen_files and base_name not in ROOT_FILES:
            continue
            
        final_path = ""
        if base_name in CORE_FILES:
            final_path = f"project_core/{base_name}"
            seen_files.add(base_name)
        elif base_name in ROOT_FILES:
            final_path = base_name
            seen_files.add(base_name)
        else:
            final_path = f"archive/{base_name}"
            # Arşivdeki dosyalar için yinelenme kontrolü daha esnek olabilir
            # ama şimdilik basit tutuyoruz.
            if base_name not in seen_files:
                seen_files.add(base_name)

        if final_path:
            new_tree.append({
                "path": final_path,
                "mode": file_info["mode"],
                "type": file_info["type"],
                "sha": file_info["sha"]
            })

    tree_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/git/trees"
    data = {"tree": new_tree}
    r = requests.post(tree_url, headers=HEADERS, json=data); r.raise_for_status(); return r.json()["sha"]

def commit_and_push(new_tree_sha, branch, parent_sha):
    commit_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/git/commits"
    commit_data = {"message": "fix: Clean and reorganize project structure", "tree": new_tree_sha, "parents": [parent_sha]}
    r = requests.post(commit_url, headers=HEADERS, json=commit_data); r.raise_for_status(); new_commit_sha = r.json()["sha"]
    
    ref_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/git/refs/heads/{branch}"
    ref_data = {"sha": new_commit_sha}
    r = requests.patch(ref_url, headers=HEADERS, json=ref_data); r.raise_for_status()
    print(f"'{branch}' dalı başarıyla güncellendi.")

def create_pull_request(head, base):
    pr_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/pulls"
    pr_data = {"title": "Final Fix: Project File Organization", "body": "This PR cleans up the repository by moving all core files into `project_core` and archiving all legacy files.", "head": head, "base": base}
    r = requests.post(pr_url, headers=HEADERS, json=pr_data)
    if r.status_code == 422:
        print("\nUyarı: Bu Pull Request zaten mevcut olabilir.")
    else:
        r.raise_for_status()
        print("\nPull Request başarıyla oluşturuldu. Lütfen GitHub'da onaylayın:")
        print(r.json()["html_url"])

def main():
    try:
        print("1. Mevcut dosya yapısı analiz ediliyor...")
        all_files = get_all_files_from_branch(BASE_BRANCH)
        
        print("2. Temiz ve doğru dosya yapısı oluşturuluyor...")
        clean_tree_sha = create_clean_tree(all_files)
        
        print(f"3. Değişiklikler için yeni bir dal ('{NEW_BRANCH}') oluşturuluyor...")
        base_sha = get_latest_commit_sha(BASE_BRANCH)
        create_new_branch(NEW_BRANCH, base_sha)
        
        print("4. Değişiklikler yeni dala uygulanıyor...")
        commit_and_push(clean_tree_sha, NEW_BRANCH, base_sha)
        
        print("5. Onay için Pull Request oluşturuluyor...")
        create_pull_request(NEW_BRANCH, BASE_BRANCH)
        
        print("\nİşlem tamamlandı!")

    except requests.exceptions.RequestException as e:
        print(f"\nBir Hata Oluştu: {e}")
        if e.response is not None:
            print(f"Hata Kodu: {e.response.status_code}, Detay: {e.response.text}")

if __name__ == "__main__":
    main()