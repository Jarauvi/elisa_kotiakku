# Elisa Kotiakku for Home Assistant

<div align="left">
    <img alt="Home Assistant" src="https://img.shields.io/badge/home%20assistant-%2341BDF5.svg"/>
    <img alt="Cloud polling" src="https://img.shields.io/badge/IOT_class-Cloud_polling-blue">
    <img alt="Static Badge" src="https://img.shields.io/badge/License-MIT-green">
    <img alt="Version" src="https://img.shields.io/github/manifest-json/v/Jarauvi/elisa_kotiakku?filename=custom_components%2Felisa_kotiakku%2Fmanifest.json&label=Version">
</div>

This custom component integrates the **Elisa Kotiakku** energy storage system into Home Assistant. It provides real-time monitoring of solar production, battery status, house consumption, and grid exchange.



## Installation

### Option 1: HACS (Recommended)
1.  Open **HACS** in your Home Assistant instance.
2.  Navigate to **Integrations** > **Custom Repositories** (top right menu).
3.  Paste your GitHub repository URL and select **Integration** as the category.
4.  Click **Install**.
5.  Restart Home Assistant.

### Option 2: Manual
1.  Download the `elisa_kotiakku` folder from this repository.
2.  Copy the folder to your `config/custom_components/` directory.
3.  Restart Home Assistant.

## Configuration

1.  Navigate to **Settings** > **Devices & Services**.
2.  Click **Add Integration** and search for **Elisa Kotiakku**.
3.  Fill in the following details:
    * **Device Name**: e.g., "Kotiakku"
    * **API URL**: Your private API endpoint.
    * **API Key**: Your secret key.
    * **Update Interval**: Recommended 60 seconds.

## Energy Dashboard Setup

To populate your Energy Dashboard, use these sensors:

* **Electricity Grid**: 
    * Consumption: `grid_to_house_energy_kwh`
    * Return to Grid: `total_grid_export_energy_kwh`
* **Solar Production**: 
    * Solar Production: `solar_energy_kwh`
* **Battery System**:
    * Energy In: `total_battery_charge_energy_kwh`
    * Energy Out: `battery_to_house_energy_kwh`

---

## Disclaimer
This integration is a community project and is not affiliated with, endorsed by, or supported by Elisa. Use at your own risk.
