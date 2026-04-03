# Weather Telemetry System

**Python Telemetry Project | GITAM PPS-II (24CSEN1041)**

---

## Overview

The Weather Telemetry System is a Python-based application developed for the GITAM PPS-II short-term project (24CSEN1041). This project bridges a high-performance data engine with a modern Model-View-Controller (MVC) architecture, delivering real-time weather monitoring and analytics capabilities through an intuitive graphical interface. The system seamlessly integrates REST API communication, asynchronous data processing, and persistent storage mechanisms to provide a comprehensive telemetry solution for atmospheric data collection and analysis.

---

## Key Features

- **Real-Time Weather Monitoring**: Fetches live atmospheric data using the Open-Meteo API, providing current weather conditions and forecasts without requiring API key configuration.

- **Data Persistence**: Implements a self-healing architecture that logs telemetry data locally to CSV format with robust error handling and automatic recovery mechanisms.

- **Weather Analytics**: Performs advanced data analysis by calculating temperature extremes, pressure trends, and atmospheric variations using discrete derivatives and statistical methods.

- **Interactive GUI**: Features a hardware-accelerated graphical user interface built with PySide6, delivering responsive and visually polished user interactions.

- **Data Visualization**: Generates dynamic, interactive charts using Matplotlib, enabling users to visualize temporal weather patterns and trends with ease.

---

## Technology Stack

| Component | Technology |
|-----------|-----------|
| **Language** | Python 3.x |
| **API Integration** | Open-Meteo (Free, No API Key Required) |
| **GUI Framework** | PySide6 |
| **Data Processing** | pandas, numpy |
| **Visualization** | Matplotlib |
| **HTTP Client** | requests |
| **Data Storage** | CSV (telemetry_logs/) |

---

## Project Structure

```
Project-Mausam/
│
├── run.py                          # Application entry point
├── bridge.py                       # Controller & threading logic
├── finalBackend.py                 # Data storage and API integration
├── design_ai.py                    # PySide6 graphical interface
│
├── telemetry_logs/                 # Weather telemetry data storage
│   └── *.csv                       # Timestamped weather logs
│
├── requirements.txt                # Python dependencies
└── README.md                       # Project documentation
```

---

## Setup Instructions

### Prerequisites

Ensure you have Python 3.8 or higher installed on your system.

### Installation Steps

1. **Clone the Repository**

   ```bash
   git clone https://github.com/tsylatac37/Project-Mausam.git
   cd Project-Mausam
   ```

2. **Create a Virtual Environment**

   ```bash
   # On Windows
   python -m venv venv
   venv\Scripts\activate

   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Application**

   ```bash
   python run.py
   ```

### Important Note

Unlike OpenWeatherMap and similar services, the Open-Meteo API **does NOT require API key configuration**. The application will automatically connect to the free Open-Meteo endpoints without additional authentication setup. This eliminates the overhead of credential management while maintaining reliable data access.

---

## Learning Objectives

This project implements practical demonstrations of the following concepts:

- **REST API Integration**: Demonstrates synchronous HTTP communication with third-party APIs using the `requests` library and proper error handling.

- **Model-View-Controller (MVC) Architecture**: Separates business logic (Model), user interface (View), and control flow (Controller) into distinct, maintainable modules.

- **Multi-threading in GUI Applications**: Implements asynchronous data fetching and processing in the GUI thread to prevent UI freezing and maintain responsiveness.

- **Data Analysis using Pandas**: Performs statistical computations, data aggregation, filtering, and transformation on weather datasets.

- **Data Visualization**: Creates dynamic, publication-quality charts and graphs that effectively communicate temporal weather patterns and analytical insights.

---

## Team Details

| Member | Role |
|--------|------|
| [Member Name] | Lead Architect & Backend |
| [Member Name] | GUI & Visualization |
| [Member Name] | Documentation & Design |
| [Member Name] | QA & Integration |

---

## License

This project is developed as part of the GITAM PPS-II coursework (24CSEN1041) and is intended for educational purposes.

## Acknowledgments

- **Open-Meteo**: Providing free, reliable weather data API
- **GITAM University**: Supporting practical project-based learning

---

*Last Updated: April 2026*
