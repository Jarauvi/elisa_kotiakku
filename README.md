# 🔋 WIP: Elisa Kotiakku for Home Assistant

<div align="left">
    <img alt="Home Assistant" src="https://img.shields.io/badge/home%20assistant-%2341BDF5.svg"/>
    <img alt="Cloud polling" src="https://img.shields.io/badge/IOT_class-Cloud_polling-blue">
    <img alt="Static Badge" src="https://img.shields.io/badge/License-MIT-green">
    <img alt="Version" src="https://img.shields.io/github/manifest-json/v/Jarauvi/elisa_kotiakku?filename=custom_components%2Felisa_kotiakku%2Fmanifest.json&label=Version">
</div>

> [!IMPORTANT]
> **Note:** This is a **work-in-progress** integration, yet without a functional official API.
> 
> For testing purposes, a **fastapi server** can be found in this repo: https://github.com/Jarauvi/kotiakku_test_server 🧪
> 
> This preliminary version assumes, that all the API data headers will be the same that can be exported from Kotiakku app 

This custom component integrates the **Elisa Kotiakku** energy storage system into Home Assistant. It provides real-time monitoring of solar production, battery status, house consumption, and grid exchange. ⚡

---

## 🛠 Installation

### Option 1: HACS (Recommended) 🚀
1.  Open **HACS** in your Home Assistant instance.
2.  Navigate to **Integrations** > **Custom Repositories** (top right menu).
3.  Paste your GitHub repository URL and select **Integration** as the category.
4.  Click **Install**.
5.  **Restart** Home Assistant. 🔄

### Option 2: Manual 📂
1.  Download the `elisa_kotiakku` folder from this repository.
2.  Copy the folder to your `config/custom_components/` directory.
3.  **Restart** Home Assistant. 🔄

---

## ⚙️ Configuration

1.  Navigate to **Settings** > **Devices & Services**.
2.  Click **Add Integration** ➕ and search for **Elisa Kotiakku**.
3.  Fill in the following details:
    * **Device Name**: e.g., `Kotiakku` 🏠
    * **API URL**: Your private API endpoint. 🌐
    * **API Key**: Your secret key. 🔑
    * **Update Interval**: Minimum of 120 seconds. ⏱️

---

## 📊 Available Sensors

### ⚡ Power Sensors (Current Flow in kW)
| Entity ID | Name (FI) | Description |
| :--- | :--- | :--- |
| `battery_power_kw` | Akun teho | Current battery charge (+) or discharge (-) |
| `solar_power_kw` | Aurinkopaneelien teho | Total current solar production |
| `grid_power_kw` | Verkon teho | Total current grid exchange |
| `house_power_kw` | Kiinteistön kulutus | Current total building consumption |
| `solar_to_house_kw` | Aurinkopaneeleilta kiinteistölle | Solar power used directly by the house |
| `solar_to_battery_kw` | Aurinkopaneeleilta akkuun | Solar power going into storage |
| `solar_to_grid_kw` | Aurinkopaneeleilta verkkoon | Solar power being exported |
| `grid_to_house_kw` | Verkosta kiinteistölle | Grid power used by the house |
| `grid_to_battery_kw` | Verkosta akkuun | Grid power used to charge the battery |
| `battery_to_house_kw` | Akusta kiinteistölle | Battery power used by the house |
| `battery_to_grid_kw` | Akusta verkkoon | Battery power being exported |

### 📈 Energy Sensors (Cumulative Totals in kWh)
| Entity ID | Name (FI) | Description |
| :--- | :--- | :--- |
| `house_energy_kwh` | Talon kokonaiskulutus | Total energy consumed by the property |
| `solar_energy_kwh` | Aurinkopaneelien kokonaistuotto | Total energy produced by panels |
| `grid_energy_kwh` | Verkosta ostettu kokonaisenergia | Total energy imported from grid |
| `total_grid_export_kwh` | Verkkoon myyty kokonaisenergia | Total energy exported to grid |
| `total_battery_charge_kwh` | Akun kokonaislataus | Total energy put into the battery |
| `battery_energy_kwh` | Akusta otettu kokonaisenergia | Total energy taken from the battery |
| `solar_to_house_kwh` | Aurinkopaneeleilta kiinteistölle | Cumulative solar used by house |
| `solar_to_battery_kwh` | Aurinkopaneeleilta akkuun | Cumulative solar stored in battery |
| `solar_to_grid_kwh` | Aurinkopaneeleilta verkkoon | Cumulative solar exported |
| `grid_to_house_kwh` | Verkosta kiinteistölle | Cumulative grid used by house |
| `grid_to_battery_kwh` | Verkosta akkuun | Cumulative grid stored in battery |
| `battery_to_house_kwh` | Akusta kiinteistölle | Cumulative battery used by house |
| `battery_to_grid_kwh` | Akusta verkkoon | Cumulative battery exported |

### 🌡️ Status & Market Data
| Entity ID | Name (FI) | Description |
| :--- | :--- | :--- |
| `state_of_charge_percent` | Akun varaustila | Battery charge level (0–100%) |
| `battery_temperature_c` | Akun lämpötila | Internal battery temperature |
| `spot_price_cents_per_kwh` | Pörssisähkön hinta | Current electricity spot price |

---

## 📊 Energy Dashboard Setup

To populate your **Energy Dashboard**, use these sensors:

* **🔌 Electricity Grid**: 
    * **Consumption**: `grid_energy_kwh`
    * **Return to Grid**: `total_grid_export_kwh`
* **☀️ Solar Production**: 
    * **Solar Production**: `solar_energy_kwh`
* **🔋 Battery System**:
    * **Energy In**: `total_battery_charge_kwh`
    * **Energy Out**: `battery_energy_kwh`

---

## ⚠️ Disclaimer
This integration is a community project and is **not** affiliated with, endorsed by, or supported by Elisa. Use at your own risk.
