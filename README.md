# Weather Telemetry System

```
------------------------------------------------------------
 Python Telemetry Project | GITAM PPS-II (24CSEN1041)
------------------------------------------------------------
```

## Overview

The **Weather Telemetry System** is a Python-based application developed for the **GITAM PPS-II short-term project**.

The system retrieves **real-time atmospheric data** using the **OpenWeatherMap API**, stores it locally for historical reference, and performs **basic trend analysis and visualization** of weather patterns.

This project demonstrates practical implementation of:

* API-based data acquisition
* Data storage and processing
* Weather trend analysis
* GUI development
* Data visualization

---

## Key Features

### Real-Time Weather Monitoring

Fetches live atmospheric data including:

* Temperature
* Humidity
* Atmospheric Pressure
* Weather Conditions

### Data Persistence

* Logs daily weather reports
* Stores historical data in **CSV format**
* Enables long-term trend analysis

### Weather Analytics

Automatically calculates:

* Hottest recorded day
* Coldest recorded day
* Temperature trends
* Humidity trends

### Interactive GUI (Advanced Component)

A **Tkinter-based graphical interface** that allows users to:

* Fetch live weather data
* View stored historical records
* Display visual charts

### Data Visualization

Dynamic charts generated using **Matplotlib** for:

* Temperature trends
* Humidity trends
* Historical comparisons

---

## Technology Stack

| Component | Technology                            |
| --------- | ------------------------------------- |
| Language  | Python 3.x                            |
| API       | OpenWeatherMap                        |
| Libraries | requests, pandas, matplotlib, tkinter |
| Storage   | CSV / SQLite                          |

---

## Project Structure

```
weather-telemetry-system/
│
├── main.py              # Application entry point
├── config.py            # API configuration
├── data/                # Stored weather logs
│   └── weather_log.csv
│
├── modules/
│   ├── api_fetch.py     # API request handling
│   ├── analytics.py     # Weather analysis logic
│   ├── storage.py       # Data persistence
│   └── visualization.py # Chart generation
│
├── gui/
│   └── app_gui.py       # Tkinter interface
│
└── README.md
```

---

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/weather-telemetry-system.git
cd weather-telemetry-system
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate the environment.

**Windows**

```bash
venv\Scripts\activate
```

**Linux / macOS**

```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install requests pandas matplotlib
```

### 4. Configure API Key

Create a file named **config.py** in the root directory.

```python
API_KEY = "your_openweathermap_api_key"
```

You can obtain a free API key from:
[https://openweathermap.org/api](https://openweathermap.org/api)

### 5. Run the Application

```bash
python main.py
```

---

## Example Output

```
---------------------------------------
 Weather Report
---------------------------------------
Location: Visakhapatnam
Temperature: 29.4 °C
Humidity: 72 %
Pressure: 1008 hPa
Condition: Scattered Clouds
---------------------------------------
```

---

## Learning Objectives

This project demonstrates practical implementation of:

* REST API integration
* Data collection pipelines
* File-based data persistence
* Data analysis using Pandas
* GUI development with Tkinter
* Data visualization using Matplotlib

---

## Team Details

```
Lead Architect           : [Member Name]
GUI & Visualization      : [Member Name]
Documentation & Design   : [Member Name]
QA & Media               : [Member Name]
```

---

## Evaluation Target

```
Expected Score: 10 / 10

Includes:
- Core Functionality
- API Integration
- Data Storage
- GUI Implementation
- Visualization Bonus Marks
```

