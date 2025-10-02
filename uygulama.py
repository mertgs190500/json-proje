import time
import logging

# Logging ayarlarını yapılandır
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class WorkflowOrchestrator:
    """
    İş akışını yönetir, görevleri sırayla çalıştırır ve durum yönetimi yapar.
    """
    def __init__(self):
        """Orkestratörü başlatır ve başlangıç durumunu 'IDLE' olarak ayarlar."""
        self.state = "IDLE"  # Olası durumlar: "IDLE" (Boşta), "WORKING" (Çalışıyor)
        logging.info("Orchestrator initialized. State: IDLE")

    def run(self, task_id):
        """
        Yeni bir görevi çalıştırmayı dener. Orkestratör meşgulse yeni görevi reddeder.
        Görev bittiğinde veya hata verdiğinde durumu her zaman 'IDLE'a geri döndürür.
        """
        # Durum Kontrolü: Eğer orkestratör zaten çalışıyorsa, yeni görevi kabul etme.
        if self.state == "WORKING":
            logging.warning(f"Orchestrator is busy. Cannot start new task '{task_id}'. Please wait.")
            return

        try:
            # Durumu 'WORKING' olarak ayarla ve göreve başla.
            self.state = "WORKING"
            logging.info(f"Task '{task_id}' started. State: WORKING")

            # --- GÖREVİN ÇALIŞTIĞI YER (Simülasyon) ---
            print(f"Executing task: {task_id}...")
            time.sleep(5)  # Örnek olarak 5 saniyelik bir görevi simüle eder.
            print(f"Task '{task_id}' successfully finished.")
            # --- Simülasyon Sonu ---

            logging.info(f"Task '{task_id}' completed.")

        except Exception as e:
            logging.error(f"An error occurred during task '{task_id}': {e}")

        finally:
            # KRİTİK DÜZELTME: Görev başarılı da olsa, hata da verse,
            # işlem bittiğinde durumu her zaman 'IDLE'a geri döndür.
            self.state = "IDLE"
            logging.info(f"State reset to: IDLE. Ready for a new task.")

# Bu dosya doğrudan çalıştırıldığında bir örnek kullanım gösterir.
if __name__ == "__main__":
    orchestrator = WorkflowOrchestrator()

    print("\n--- İlk görevi çalıştırma denemesi ---")
    orchestrator.run("CSV-INGEST-PROCESS-01")

    print("\n--- İkinci görevi çalıştırma denemesi ---")
    # İlk görev bittiği ve durumu 'IDLE'a döndüğü için bu görev başlayabilir.
    orchestrator.run("MKT-ANLZ-01")