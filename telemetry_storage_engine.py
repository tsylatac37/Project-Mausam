import csv
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Configure simple logging to show program status in the terminal
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class TelemetryStorageEngine:
    # Optimized memory usage for the class attributes
    __slots__ = ['storage_path', 'file_path', 'schema']

    def __init__(self, storage_dir: str = "data_logs", filename: str = "daily_telemetry.csv"):
        self.storage_path = Path(storage_dir)
        self.file_path = self.storage_path / filename
        
        # Define the columns for our CSV file
        self.schema = [
            "timestamp", "location_id", "temp_c", 
            "humidity_pct", "wind_kph", "condition"
        ]
        
        self._initialize_storage()

    def _initialize_storage(self) -> None:
        """Creates the storage folder and file headers if they don't exist."""
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        if not self.file_path.exists():
            with open(self.file_path, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.schema, restval="NaN")
                writer.writeheader()
            logging.info(f"Created new log file: {self.file_path}")

    def log_reading(self, data: Dict[str, Any]) -> bool:
        """Saves a single weather reading to the CSV file."""
        if "timestamp" not in data:
            data["timestamp"] = datetime.now().isoformat()
            
        try:
            with open(self.file_path, mode='a', newline='', encoding='utf-8') as f:
                # extrasaction='ignore' ensures we only save columns defined in self.schema
                writer = csv.DictWriter(
                    f, fieldnames=self.schema, restval="NaN", extrasaction='ignore'
                )
                writer.writerow(data)
            return True
        except IOError as e:
            logging.error(f"Error saving data: {e}")
            return False

    def log_batch(self, batch_data: List[Dict[str, Any]]) -> bool:
        """Saves multiple weather readings at once for better performance."""
        if not batch_data: return True
            
        for data in batch_data:
            if "timestamp" not in data:
                data["timestamp"] = datetime.now().isoformat()

        try:
            with open(self.file_path, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(
                    f, fieldnames=self.schema, restval="NaN", extrasaction='ignore'
                )
                writer.writerows(batch_data)
            return True
        except IOError as e:
            logging.error(f"Error saving batch data: {e}")
            return False