import os
import requests
import json

# --- Gerekli Bilgiler ---
API_TOKEN = os.getenv('GITHUB_TOKEN')
REPO_OWNER = "mertgs190500"
REPO_NAME = "json-proje"
BRANCH = "main"

if not API_TOKEN:
    raise ValueError("Lütfen GITHUB_TOKEN ortam değişkenini ayarlayın.")

HEADERS = {
    "Authorization": f"token {API_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def get_all_repo_files():
    """Depodaki tüm dosyaların listesini ve yollarını alır."""
    print("GitHub'a bağlanılıyor ve son commit bilgisi alınıyor...")
    # Önce en son commit'in SHA kodunu al
    url_branch = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/branches/{BRANCH}"
    response_branch = requests.get(url_branch, headers=HEADERS)
    response_branch.raise_for_status()
    commit_sha = response_branch.json()["commit"]["sha"]

    # Commit'e ait ağacın (tree) SHA kodunu al
    url_commit = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/git/commits/{commit_sha}"
    response_commit = requests.get(url_commit, headers=HEADERS)
    response_commit.raise_for_status()
    tree_sha = response_commit.json()["tree"]["sha"]
    
    # Ağaçtan tüm dosyaları 'recursive=1' ile çek
    print("Projedeki tüm dosyalar ve klasörler çekiliyor...")
    url_tree = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/git/trees/{tree_sha}?recursive=1"
    response_tree = requests.get(url_tree, headers=HEADERS)
    response_tree.raise_for_status()
    
    # Sadece dosya yollarını (path) listele
    all_paths = [item['path'] for item in response_tree.json().get('tree', [])]
    return all_paths

def main():
    try:
        file_paths = get_all_repo_files()
        
        print("\n--- GITHUB PROJE DOSYA HARİTASI ---")
        if not file_paths:
            print("Projeye ait hiçbir dosya bulunamadı.")
        else:
            for path in sorted(file_paths):
                print(path)
        print("--- HARİTA SONU ---")

    except requests.exceptions.RequestException as e:
        print(f"\nBir Hata Oluştu: {e}")
        if e.response is not None:
            print(f"Hata Detayı: {e.response.text}")

if __name__ == "__main__":
    main()