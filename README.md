# Weather Monitoring & Analysis System (API-Based)

## 📋 Project Overview
[cite_start]A Python-based telemetry system developed for the **GITAM PPS-II (24CSEN1041)** short-term project[cite: 1]. This application fetches real-time atmospheric data via the OpenWeatherMap API and performs historical trend analysis.

## 🚀 Key Features
- [cite_start]**Real-time Monitoring:** Fetches Temperature, Humidity, Pressure, and Conditions[cite: 65, 66].
- **Data Persistence:** Logs daily reports to a CSV file for long-term storage.
- **Advanced Analytics:** Identifies hottest/coldest days and calculates weather trends.
- **Interactive GUI (Advanced):** User-friendly interface built with Tkinter.
- **Visualization (Advanced):** Dynamic Matplotlib charts for temperature and humidity trends.

## 🛠 Tech Stack
- [cite_start]**Language:** Python 3.x 
- [cite_start]**Libraries:** `requests`, `pandas`, `matplotlib`, `tkinter` [cite: 9, 68]
- **Data Storage:** CSV / SQLite

## 🏗 Setup Instructions
1. Clone the repository.
2. Activate virtual environment: `python -m venv venv`.
3. Install dependencies: `pip install requests pandas matplotlib`.
4. **Important:** Create a `config.py` in the root directory and add: `API_KEY = "your_openweathermap_key"`.
5. Run the entry point: `python main.py`.

## 👥 Team Details
- **Lead Architect:** Sai Prasad Padhy
- **GUI & Visualization:** [Member Name]
- **Documentation & Design:** [Member Name]
- **QA & Media:** [Member Name]

---
[cite_start]*Target Marks: 10/10 (Including 2 Bonus Marks for GUI & Visualization) [cite: 32, 33]*
