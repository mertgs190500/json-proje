import logging
import pandas as pd
import io

class CsvIngestor:
    def _clean_headers(self, df):
        """Strips whitespace and converts headers to a more canonical form."""
        original_columns = list(df.columns)
        df.columns = df.columns.str.strip()
        cleaned_columns = list(df.columns)
        if original_columns != cleaned_columns:
            logging.info(f"Sütun başlıkları temizlendi: {dict(zip(original_columns, cleaned_columns))}")
        return df

    def execute(self, inputs, context, db_manager=None):
        """
        Processes a CSV file based on a 'resolved_profile' provided in the inputs.
        It uses pandas to read and clean the data according to the profile rules.
        """
        file_path = inputs.get("file_path")
        profile = inputs.get("resolved_profile", {})

        if not profile or not file_path:
            logging.error("[CsvIngestor] 'file_path' or 'resolved_profile' is missing from inputs.")
            return {"status": "error", "message": "Missing file_path or profile.", "data": None}

        logging.info(f"[CsvIngestor] '{file_path}' dosyası işleniyor...")
        logging.info(f"  > Profil uygulanıyor: {profile.get('description', 'N/A')}")

        # Extract parameters from the profile with sensible defaults
        encodings = profile.get("encoding", ["utf-8"])
        delimiters = profile.get("delimiter_probe", [","])
        index_col = profile.get("index_col") # Can be None
        na_values = profile.get("na_values") # Can be None
        required_fields = profile.get("required_fields", [])

        # Attempt to read the file using specified encodings
        raw_content = None
        for encoding in encodings:
            try:
                with open(file_path, 'rb') as f:
                    raw_content = f.read()
                raw_content.decode(encoding) # Try decoding to see if it works
                logging.info(f"  > Dosya '{encoding}' kodlamasıyla başarıyla okundu.")
                break
            except (UnicodeDecodeError, FileNotFoundError) as e:
                logging.warning(f"  > '{encoding}' kodlamasıyla okunamadı. Deneniyor... Hata: {e}")
                raw_content = None

        if raw_content is None:
            message = f"Dosya desteklenen kodlamaların hiçbiriyle okunamadı: {encodings}"
            logging.error(f"[CsvIngestor] {message}")
            return {"status": "error", "message": message, "data": None}

        # Attempt to parse the CSV using pandas with different delimiters
        df = None
        for delimiter in delimiters:
            try:
                # Use a file-like object to pass the decoded string to pandas
                csv_io = io.StringIO(raw_content.decode(encoding))
                temp_df = pd.read_csv(
                    csv_io,
                    sep=delimiter,
                    index_col=index_col,
                    na_values=na_values,
                    keep_default_na=True # Ensure pandas default NaNs are also caught
                )
                # A simple check to see if the delimiter worked: at least one column was parsed.
                if len(temp_df.columns) > 1 or required_fields:
                    df = temp_df
                    logging.info(f"  > CSV '{delimiter}' ayırıcısıyla başarıyla ayrıştırıldı.")
                    break
            except Exception as e:
                logging.warning(f"  > '{delimiter}' ayırıcısıyla ayrıştırma başarısız oldu. Deneniyor... Hata: {e}")

        if df is None:
            message = "Dosya desteklenen ayırıcıların hiçbiriyle bir DataFrame'e dönüştürülemedi."
            logging.error(f"[CsvIngestor] {message}")
            return {"status": "error", "message": message, "data": None}

        # Post-processing
        initial_rows = len(df)
        logging.info(f"  > Başlangıç satır sayısı: {initial_rows}")

        # Clean headers
        df = self._clean_headers(df)

        # Validate required fields
        missing_fields = [field for field in required_fields if field not in df.columns]
        if missing_fields:
            message = f"Gerekli sütunlar eksik: {missing_fields}. Mevcut sütunlar: {list(df.columns)}"
            logging.error(f"[CsvIngestor] {message}")
            return {"status": "error", "message": message, "data": None}

        # Drop rows where all values are NaN (often indicates empty rows)
        df.dropna(how='all', inplace=True)
        if len(df) < initial_rows:
            logging.info(f"  > Tamamen boş olan {initial_rows - len(df)} satır kaldırıldı.")

        # Convert to list of dictionaries for JSON serialization
        processed_data = df.to_dict('records')

        message = f"İşlem tamamlandı. {len(processed_data)} satır işlendi."
        logging.info(f"[CsvIngestor] {message}")
        return {"status": "success", "message": message, "data": processed_data}