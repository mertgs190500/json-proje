import logging
import pandas as pd
import io

class CsvIngestor:
    def _clean_headers(self, headers):
        """Strips whitespace and quotes from a list of headers."""
        original_columns = list(headers)
        cleaned_columns = [str(h).strip().strip("'\"") for h in original_columns]

        changed_cols = {o: c for o, c in zip(original_columns, cleaned_columns) if o != c}
        if changed_cols:
            logging.info(f"Sütun başlıkları temizlendi: {changed_cols}")
        return cleaned_columns

    def execute(self, inputs, context, db_manager=None):
        """
        Processes raw CSV content based on a 'resolved_profile'.
        It decodes, parses, cleans, and validates the data using pandas.
        """
        raw_content = inputs.get("raw_content")
        file_path = inputs.get("file_path", "N/A") # For logging purposes
        profile = inputs.get("resolved_profile", {})

        if not profile or raw_content is None:
            logging.error("[CsvIngestor] 'raw_content' or 'resolved_profile' is missing from inputs.")
            return {"status": "error", "message": "Missing raw_content or profile.", "data": None}

        logging.info(f"[CsvIngestor] '{file_path}' içeriği işleniyor...")
        logging.info(f"  > Profil uygulanıyor: {profile.get('description', 'N/A')}")

        # Extract parameters from the profile
        encodings = profile.get("encoding", ["utf-8"])
        delimiters = profile.get("delimiter_probe", [","])
        index_col = profile.get("index_col")
        na_values = profile.get("na_values", [])
        required_fields = profile.get("required_fields", [])

        # Step 1: Decode the raw content
        decoded_content = None
        for encoding in encodings:
            try:
                decoded_content = raw_content.decode(encoding)
                logging.info(f"  > İçerik '{encoding}' kodlamasıyla başarıyla çözüldü.")
                break
            except UnicodeDecodeError:
                logging.warning(f"  > '{encoding}' kodlamasıyla çözülemedi. Sonraki deneniyor...")

        if decoded_content is None:
            message = "İçerik desteklenen kodlamaların hiçbiriyle çözülemedi."
            logging.error(f"[CsvIngestor] {message}")
            return {"status": "error", "message": message, "data": None}

        # Step 2: Parse into a DataFrame using pandas, trying each delimiter
        df = None
        for delimiter in delimiters:
            try:
                csv_io = io.StringIO(decoded_content)
                temp_df = pd.read_csv(
                    csv_io,
                    delimiter=delimiter,
                    index_col=index_col if index_col is not None else False,
                    na_values=na_values,
                    keep_default_na=True,
                    quotechar='"',
                    skipinitialspace=True,
                    engine='python'
                )

                # Clean headers right after parsing to check for required fields
                temp_df.columns = self._clean_headers(temp_df.columns)

                # Validation: Check if parsing produced meaningful results
                if temp_df.shape[1] == 0:
                    logging.warning(f"  > '{delimiter}' ayırıcısı 0 sütun üretti. Sonraki deneniyor...")
                    continue
                if required_fields and not all(field in temp_df.columns for field in required_fields):
                    logging.warning(f"  > '{delimiter}' ayırıcısı gerekli sütunları ({required_fields}) üretmedi. Mevcut: {list(temp_df.columns)}. Sonraki deneniyor...")
                    continue

                df = temp_df
                logging.info(f"  > CSV, '{delimiter}' ayırıcısı kullanılarak başarıyla DataFrame'e dönüştürüldü.")
                break
            except Exception as e:
                logging.warning(f"  > Pandas ile '{delimiter}' ayırıcısıyla ayrıştırma başarısız oldu. Hata: {e}")

        if df is None:
            message = "İçerik, desteklenen ayırıcıların hiçbiriyle bir DataFrame'e dönüştürülemedi."
            logging.error(f"[CsvIngestor] {message}")
            return {"status": "error", "message": message, "data": None}

        # Step 3: Clean and Process the DataFrame
        initial_rows = len(df)
        logging.info(f"  > Başlangıç satır sayısı: {initial_rows}")

        if df.index.name and 'Unnamed:' in str(df.index.name):
            logging.info(f"  > '{df.index.name}' isimli gereksiz indeks sütunu kaldırıldı.")
            df.index.name = None

        missing_fields = [field for field in required_fields if field not in df.columns]
        if missing_fields:
            message = f"Gerekli sütunlar eksik: {missing_fields}. Mevcut sütunlar: {list(df.columns)}"
            logging.error(f"[CsvIngestor] {message}")
            return {"status": "error", "message": message, "data": None}

        df.dropna(how='all', inplace=True)
        if len(df) < initial_rows:
            logging.info(f"  > Tamamen boş olan {initial_rows - len(df)} satır kaldırıldı.")

        # Step 4: Finalize and return
        processed_data = df.to_dict('records')
        message = f"İşlem tamamlandı. {len(processed_data)} satır işlendi."
        logging.info(f"[CsvIngestor] {message}")

        return {"status": "success", "message": message, "data": processed_data}