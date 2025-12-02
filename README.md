# VesselWatch

VesselWatch is a simple web app that provides real-time information and delay prediction for Washington State Ferries. It's mostly written in Python and uses a FastAPI backend, and HTMX for the front-end. Check it out at [here]([url](https://whens-the-ferry-production.up.railway.app/)).

## Features

- **Real-time Sailing Information**: Get up-to-the-minute departure and arrival times for all Washington State Ferry routes.
- **Live Vessel Tracking**: View the real-time locations of all active ferries on an interactive map.
- **Data Caching**: The application caches sailing data to provide a fast and responsive user experience, even during peak hours.
- **Data Collection**: The application collects and stores historical vessel data for analysis.

## Getting Started

### Prerequisites

- Python 3.13 or higher
- [uv](https://github.com/astral-sh/uv) - An extremely fast Python package installer and resolver.

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/vesselwatch.git
   cd vesselwatch
   ```

2. **Install dependencies:**
   This project uses `uv` for package management. To install the dependencies, run:
   ```bash
   uv pip install -e .
   ```

3. **Set up environment variables:**
   Create a `.env` file by copying the example file:
   ```bash
   cp .env.example .env
   ```
   You will need to add your WSDOT API key to the `.env` file. You can get a free API key from the [WSDOT Developer Portal](https://www.wsdot.wa.gov/traffic/api/).
   ```
   WSDOT_API_KEY="YOUR_KEY_FROM_WSDOT"
   ```

## Usage

Once the installation is complete, you can start the application by running the following command in the root of the project directory:

```bash
uvicorn backend.main:app --reload
```

This will start the FastAPI development server. You can then access the application by opening your web browser and navigating to `http://127.0.0.1:8000`.

The main page will display the current sailing information. You can switch between the "Sailings" and "Map" tabs to see the next sailings or the live vessel map.

## Deployment

This application is configured for deployment on [Railway](https://railway.app/). The `railway.toml` file contains the build and deploy configuration.

To deploy this application to Railway, you will need to:

1. **Create a new project on Railway.**
2. **Link your GitHub repository to the project.**
3. **Add the `WSDOT_API_KEY` as a secret in your Railway project.**

Railway will then automatically build and deploy the application. The `startCommand` in the `railway.toml` file is configured to run the application using `uvicorn`.
