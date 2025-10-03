import unittest
import sys
import os
from datetime import datetime, timedelta

# Add project_core to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from project_core.audit_generator import AuditGenerator
from knowledge_manager import KnowledgeManager
from version_control import VersionControl
import shutil

class TestAuditGenerator(unittest.TestCase):

    def setUp(self):
        """Set up the test environment before each test."""
        self.audit_generator = AuditGenerator()

        # Setup VersionControl and inject into KnowledgeManager
        self.version_config = {"pattern": "test_v{N}_{sha12}.json"}
        self.version_controller = VersionControl(self.version_config)
        self.knowledge_manager = KnowledgeManager(version_controller=self.version_controller, base_path="test_knowledge_base.json")

        # Mock context data
        self.start_time = (datetime.now() - timedelta(minutes=10)).isoformat()
        self.mock_context = {
            "workflow_start_time": self.start_time,
            "product_info": {
                "product_id": "TEST_PROD_123"
            },
            "steps": {
                "10": {
                    "name": "Başlık Oluşturma",
                    "output": {"final_title": "Test Title"}
                },
                "11": {
                    "name": "Açıklama Oluşturma",
                    "output": {"status": "SUCCESS"},
                    "warnings": ["Description is a bit short."]
                },
                "17":{
                    "name": "Export CSV",
                    "output": {"file_path": "/output/test.csv"}
                }
            },
            "version_control": {
                "versions": [
                    {"filename": "v1.json", "sha1": "abc123sha1"},
                    {"filename": "v2.json", "sha1": "def456sha1"}
                ]
            }
        }

        # Mock inputs for the audit step
        self.mock_inputs = {
            "summary_info": {
                "config_version": "v1.0-test"
            }
        }

        # Add a relevant insight to the knowledge base
        self.knowledge_manager.add_insight(
            key="title_strategy",
            value="High CTR observed for titles with brand name.",
            source_id="feedback_processor",
            confidence=0.85
        )

    def tearDown(self):
        """Clean up after each test."""
        # Clean up the versioned outputs directory created during the test
        if os.path.exists("outputs"):
            shutil.rmtree("outputs")

    def test_execute_report_generation(self):
        """Test the successful generation of a complete audit report."""
        result = self.audit_generator.execute(self.mock_inputs, self.mock_context, self.knowledge_manager)

        self.assertEqual(result["status"], "SUCCESS")
        self.assertIn("Denetim raporu başarıyla oluşturuldu.", result["message"])

        report = result["data"]["report_content"]

        # Check for all major sections
        self.assertIn("# Workflow Audit Report", report)
        self.assertIn("## Özet Bilgiler", report)
        self.assertIn("## Adım Adım Döküm", report)
        self.assertIn("## Veri Bütünlüğü Kontrolü", report)
        self.assertIn("## Öğrenimlerin Özeti", report)

        # Check for specific data points
        self.assertIn("Kullanılan Konfigürasyon Versiyonu:** v1.0-test", report)
        self.assertIn("İşlenen Ürün ID:** TEST_PROD_123", report)

        # Check step details
        self.assertIn("Adım 10: Başlık Oluşturma", report)
        self.assertIn("Ana Çıktı: `final_title` = `Test Title`", report)
        self.assertIn("Adım 11: Açıklama Oluşturma", report)
        self.assertIn("Uyarı: Description is a bit short.", report)

        # Check integrity section
        self.assertIn("Dosya: `v1.json`, SHA1: `abc123sha1`", report)
        self.assertIn("SONUÇ: 0 Veri Kaybı ilkesi doğrulandı.", report)

        # Check learnings section
        self.assertIn("Bu iş akışı sırasında aşağıdaki yeni öğrenimler eklendi:", report)
        self.assertIn("High CTR observed for titles with brand name.", report)

if __name__ == '__main__':
    unittest.main()