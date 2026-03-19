import csv
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Configure terminal logging (Your "Status LEDs")
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class TelemetryStorageEngine:
    # Register Allocation: Lock down memory
    __slots__ = ['storage_path', 'file_path', 'schema']

    def __init__(self, storage_dir: str = "data_logs", filename: str = "daily_telemetry.csv"):
        self.storage_path = Path(storage_dir)
        self.file_path = self.storage_path / filename
        
        # The Pinout Diagram (Column Headers)
        self.schema = [
            "timestamp", "location_id", "temp_c", 
            "humidity_pct", "wind_kph", "condition"
        ]
        
        self._initialize_storage()

    def _initialize_storage(self) -> None:
        """The 'Power-On' routine: Creates the folder and the header row."""
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        if not self.file_path.exists():
            with open(self.file_path, mode='w', newline='', encoding='utf-8') as f:
                # Initialize the 'Canvas' and write the headers
                writer = csv.DictWriter(f, fieldnames=self.schema, restval="NaN")
                writer.writeheader()
            logging.info(f"Initialized new telemetry log at: {self.file_path}")

    def log_reading(self, telemetry_data: Dict[str, Any]) -> bool:
        """The 'Live Feed' routine: Appends one row of data."""
        if "timestamp" not in telemetry_data:
            telemetry_data["timestamp"] = datetime.now().isoformat()

        try:
            with open(self.file_path, mode='a', newline='', encoding='utf-8') as f:
                # The Noise Filter: Ignore extra API junk
                writer = csv.DictWriter(
                    f, fieldnames=self.schema, restval="NaN", extrasaction='ignore'
                )
                writer.writerow(telemetry_data)
            return True
        except IOError as e:
            logging.error(f"I/O error logging telemetry: {e}")
            return False

    def log_batch(self, telemetry_batch: List[Dict[str, Any]]) -> bool:
        """Burst Mode: Saves multiple rows at once for efficiency."""
        if not telemetry_batch: return True
            
        for data in telemetry_batch:
            if "timestamp" not in data:
                data["timestamp"] = datetime.now().isoformat()

        try:
            with open(self.file_path, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(
                    f, fieldnames=self.schema, restval="NaN", extrasaction='ignore'
                )
                writer.writerows(telemetry_batch)
            return True
        except IOError as e:
            logging.error(f"I/O error in batch logging: {e}")
            return False