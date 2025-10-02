import os
import requests
import time

API_TOKEN = os.getenv('GITHUB_TOKEN')
REPO_OWNER = "mertgs190500"
REPO_NAME = "json-proje"
BASE_BRANCH = "main"
# Her seferinde farklı bir dal adı kullanarak çakışmaları önle
NEW_BRANCH = f"fix/final-organization-{int(time.time())}"

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
    "feedback_processor.py", "packaging_strategist.py", "finalv2_config.json", 
    "workflow_schema_v2.json", "rule_definitions.json", "data_contracts.json", 
    "product_data.json", "documentation.json", "csv_profiles.json", 
    "orchestrator_policy.json", "knowledge_base.json", "finalv1.json", 
    "populer_urunler.csv"
]

# --- OLMASI GEREKEN YER: Ana Dizin ---
ROOT_FILES = [".gitignore", "README.md"]

def get_latest_commit_sha(branch):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/git/refs/heads/{branch}"
    r = requests.get(url, headers=HEADERS); r.raise_for_status(); return r.json()["object"]["sha"]

def get_all_files_from_branch(branch):
    latest_sha = get_latest_commit_sha(branch)
    tree_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/git/trees/{latest_sha}?recursive=1"
    r = requests.get(tree_url, headers=HEADERS); r.raise_for_status(); return r.json()["tree"]

def create_new_branch(new_branch, base_sha):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/git/refs"
    data = {"ref": f"refs/heads/{new_branch}", "sha": base_sha}
    r = requests.post(url, headers=HEADERS, json=data); r.raise_for_status()

def create_clean_tree(all_files):
    new_tree = []
    processed_files = set()
    for file_info in all_files:
        if file_info["type"] != "blob": continue
        
        base_name = os.path.basename(file_info["path"])
        if base_name in processed_files: continue
        
        final_path = ""
        if base_name in CORE_FILES:
            final_path = f"project_core/{base_name}"
        elif base_name in ROOT_FILES:
            final_path = base_name
        else:
            final_path = f"archive/{base_name}"
        
        new_tree.append({"path": final_path, "mode": file_info["mode"], "type": "blob", "sha": file_info["sha"]})
        processed_files.add(base_name)
        
    tree_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/git/trees"
    data = {"tree": new_tree}
    r = requests.post(tree_url, headers=HEADERS, json=data); r.raise_for_status(); return r.json()["sha"]

def commit_and_push(new_tree_sha, branch, parent_sha):
    commit_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/git/commits"
    commit_data = {"message": "fix: Final and correct project structure organization", "tree": new_tree_sha, "parents": [parent_sha]}
    r = requests.post(commit_url, headers=HEADERS, json=commit_data); r.raise_for_status(); new_commit_sha = r.json()["sha"]
    
    ref_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/git/refs/heads/{branch}"
    ref_data = {"sha": new_commit_sha, "force": True} # Force push to the new branch
    requests.patch(ref_url, headers=HEADERS, json=ref_data).raise_for_status()
    print(f"'{branch}' dalı başarıyla güncellendi.")
    return new_commit_sha

def create_pull_request(head, base):
    pr_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/pulls"
    pr_data = {"title": "Final Fix: Project File Organization", "body": "This PR cleans the repository structure. All core files are moved to `project_core`, and all other files are moved to `archive`.", "head": head, "base": base}
    r = requests.post(pr_url, headers=HEADERS, json=pr_data)
    if r.status_code == 422:
        print("\nUyarı: Benzer bir Pull Request zaten mevcut olabilir. Lütfen GitHub'ı kontrol edin.")
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
        new_commit_sha = commit_and_push(clean_tree_sha, NEW_BRANCH, base_sha)
        
        print("5. Onay için Pull Request oluşturuluyor...")
        create_pull_request(NEW_BRANCH, BASE_BRANCH)
        
        print("\nİşlem tamamlandı!")

    except requests.exceptions.RequestException as e:
        print(f"\nBir Hata Oluştu: {e}")
        if e.response is not None:
            print(f"Hata Kodu: {e.response.status_code}, Detay: {e.response.text}")

if __name__ == "__main__":
    main()