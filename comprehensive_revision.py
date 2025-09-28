import json
import os

def apply_revision(input_filename="uretim_cekirdek_v14_strategic.json", output_filename="uretim_cekirdek_v15_revised.json"):
    """
    Applies a comprehensive revision to the specified JSON workflow file according to the provided phases.
    """
    try:
        with open(input_filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"Successfully loaded '{input_filename}'.")
    except FileNotFoundError:
        print(f"Error: Input file '{input_filename}' not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{input_filename}'.")
        return

    # --- FAZ 1: Temizlik - Gereksiz Adımların Kaldırılması ---
    print("\n--- Starting Phase 1: Cleanup ---")
    steps_to_delete = ["21", "22", "23"]
    run_s_path = data.get("run", {}).get("s", {})
    if not run_s_path:
        # Alternative path from the provided JSON structure
        run_s_path = data.get("_run_order", {}).get("steps", {})

    for step_id in steps_to_delete:
        if step_id in run_s_path:
            del run_s_path[step_id]
            print(f"  - Deleted step /run/s/{step_id}")
        else:
            print(f"  - Warning: Step /run/s/{step_id} not found for deletion.")
    print("--- Phase 1 Complete ---")


    # --- FAZ 2: Entegrasyon - Eksik Kanonik Adımların Eklenmesi ---
    print("\n--- Starting Phase 2: Integration ---")

    # Adım Ekleme: 8b_positive
    run_s_path["8b_positive"] = {
        "n": "Ads Sync – Positive Set", "en": True, "purp": "Sync positive keywords for Ads campaign.",
        "requires": ["8a"], "i": ["ads.keywords[]"], "o": ["ads_sync.final_positive[]"],
        "rs": {"note": "Placeholder: Define sync logic."}, "auto_c": True, "await_u": False, "req_ctx": True
    }
    print("  - Added step /run/s/8b_positive")

    # Adım Ekleme: 8c_negative
    run_s_path["8c_negative"] = {
        "n": "Ads Sync – Negative Set", "en": True, "purp": "Sync negative keywords for Ads campaign.",
        "requires": ["8b_positive"], "i": ["ads.negatives[]"], "o": ["ads_sync.final_negative[]", "ads_sync.status"],
        "rs": {"note": "Placeholder: Define sync logic."}, "auto_c": True, "await_u": False, "req_ctx": True
    }
    print("  - Added step /run/s/8c_negative")

    # Adım Ekleme: 12a_attributes
    run_s_path["12a_attributes"] = {
        "n": "Nitelik Seçimi & Bonus Etiket Eşleme", "en": True, "purp": "Select product attributes and map bonus tags.",
        "requires": ["12"], "i": ["product.info{}", "tags.final[13]", "inferred_product_type"],
        "o": ["attributes.selected{}", "tags.mapped_count"],
        "rs": {"note": "Placeholder: Define attribute selection and mapping logic."}, "auto_c": True, "await_u": False, "req_ctx": True
    }
    print("  - Added step /run/s/12a_attributes")

    # Bağımlılık Güncellemesi
    if "9" in run_s_path:
        run_s_path["9"]["requires"] = ["8c_negative"]
        print("  - Updated /run/s/9/requires to ['8c_negative']")
    if "13" in run_s_path:
        run_s_path["13"]["requires"] = ["12a_attributes"]
        print("  - Updated /run/s/13/requires to ['12a_attributes']")
    print("--- Phase 2 Complete ---")


    # --- FAZ 3: Aktivasyon - Taslak Adımlarının Devreye Alınması ---
    print("\n--- Starting Phase 3: Activation & Integration ---")
    steps_to_activate = ["ab.1", "ads.1", "kw.1", "media.1", "seo.1", "trend.1"]
    for step_id in steps_to_activate:
        if step_id in run_s_path:
            run_s_path[step_id]["en"] = True
            if "status" in run_s_path[step_id]:
                run_s_path[step_id]["status"] = "active"
            if "ui" in run_s_path[step_id] and "hidden" in run_s_path[step_id]["ui"]:
                run_s_path[step_id]["ui"]["hidden"] = False
            print(f"  - Activated step {step_id}")

    # Akış Entegrasyonu
    if "media.1" in run_s_path: run_s_path["media.1"]["requires"] = ["1a"]
    if "1b" in run_s_path: run_s_path["1b"]["requires"] = ["media.1"]
    if "kw.1" in run_s_path: run_s_path["kw.1"]["requires"] = ["3"]
    if "trend.1" in run_s_path: run_s_path["trend.1"]["requires"] = ["3"]
    if "3a" in run_s_path:
        if "requires" not in run_s_path["3a"]: run_s_path["3a"]["requires"] = []
        run_s_path["3a"]["requires"].extend(["kw.1", "trend.1"])
        run_s_path["3a"]["requires"] = list(dict.fromkeys(run_s_path["3a"]["requires"])) # remove duplicates
    if "seo.1" in run_s_path: run_s_path["seo.1"]["requires"] = ["12a_attributes"]
    if "13" in run_s_path: run_s_path["13"]["requires"] = ["seo.1"] # Overwrites Phase 2 change
    if "ab.1" in run_s_path: run_s_path["ab.1"]["requires"] = ["18"]
    if "19" in run_s_path:
        if "requires" not in run_s_path["19"]: run_s_path["19"]["requires"] = []
        run_s_path["19"]["requires"].append("ab.1")
    if "ads.1" in run_s_path: run_s_path["ads.1"]["requires"] = ["19"]
    if "20" in run_s_path:
        if "requires" not in run_s_path["20"]: run_s_path["20"]["requires"] = []
        run_s_path["20"]["requires"].append("ads.1")
    print("  - Integrated workshop steps into the flow.")
    print("--- Phase 3 Complete ---")


    # --- FAZ 4: Veri Akışı - Dinamik Product Type Filtrelemesi ---
    print("\n--- Starting Phase 4: Data Flow ---")
    # Adım 1a Güncellemesi
    if "1a" in run_s_path:
        step_1a = run_s_path["1a"]
        if "o" in step_1a and isinstance(step_1a["o"], list):
            if "inferred_product_type" not in step_1a["o"]:
                step_1a["o"].append("inferred_product_type")
        if "art" not in step_1a: step_1a["art"] = {}
        step_1a["art"]["inferred_product_type"] = {"__MIRRORED_PLACEHOLDER__": "inferred_product_type"}
        if "rs" not in step_1a: step_1a["rs"] = {}
        step_1a["rs"]["note_inferred_product_type"] = "Dynamically infers product type from visual analysis."
        print("  - Updated step 1a for data flow.")

    # Adım 5a Güncellemesi
    if "5a" in run_s_path:
        step_5a = run_s_path["5a"]
        if "i" in step_5a and isinstance(step_5a["i"], list):
            if "inferred_product_type" not in step_5a["i"]:
                step_5a["i"].append("inferred_product_type")
        if "mirror" not in step_5a: step_5a["mirror"] = {}
        step_5a["mirror"]["inferred_product_type_from_1a"] = {"__REF__": "/run/s/1a/art/inferred_product_type"}
        if "rs" not in step_5a: step_5a["rs"] = {}
        step_5a["rs"]["note_dynamic_filter"] = "Filters popular products based on inferred_product_type from step 1a."
        print("  - Updated step 5a for data flow.")

    # Adım 7 Güncellemesi
    if "7" in run_s_path:
        step_7 = run_s_path["7"]
        if "i" in step_7 and isinstance(step_7["i"], list):
            if "inferred_product_type" not in step_7["i"]:
                step_7["i"].append("inferred_product_type")
        if "mirror" not in step_7: step_7["mirror"] = {}
        step_7["mirror"]["inferred_product_type_from_1a"] = {"__REF__": "/run/s/1a/art/inferred_product_type"}
        if "rs" not in step_7: step_7["rs"] = {}
        step_7["rs"]["note_dynamic_filter"] = "Filters competitor analysis based on inferred_product_type from step 1a."
        print("  - Updated step 7 for data flow.")
    print("--- Phase 4 Complete ---")

    # --- Yazma ve Sonuç ---
    print(f"\nWriting updated JSON to '{output_filename}'...")
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print("Revision script finished successfully.")

if __name__ == "__main__":
    # To allow running from different directories, locate the script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(script_dir, "uretim_cekirdek_v14_strategic.json")
    output_path = os.path.join(script_dir, "uretim_cekirdek_v15_revised.json")

    apply_revision(input_path, output_path)