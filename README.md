<div align="center">
  <img src="https://github.com/Jarauvi/elisa_kotiakku/blob/main/custom_components/elisa_kotiakku/brand/icon.png?raw=true" width="128" height="128">

  # Elisa Kotiakku for Home Assistant

  [![Home Assistant](https://img.shields.io/badge/home%20assistant-%2341BDF5.svg?style=for-the-badge&logo=home-assistant&logoColor=white)](https://www.home-assistant.io/)
  [![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://hacs.xyz/)
  [![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

  [![Version](https://img.shields.io/github/manifest-json/v/Jarauvi/elisa_kotiakku?filename=custom_components%2Felisa_kotiakku%2Fmanifest.json&label=Version)](https://github.com/Jarauvi/elisa_kotiakku)
  [![Tests](https://github.com/Jarauvi/elisa_kotiakku/actions/workflows/tests.yaml/badge.svg)](https://github.com/Jarauvi/elisa_kotiakku/actions)
  ![Cloud Polling](https://img.shields.io/badge/IOT_class-Cloud_polling-blue)

  **Integrate your Elisa Kotiakku energy storage system into Home Assistant.** *Monitor solar production, battery health, and real-time energy costs.*
</div>

---

## ✨ Features

- **Device-Centric Design**: All sensors are automatically grouped under a single **Elisa Kotiakku device**.
- **Multi-Instance Support**: Manage multiple battery systems within a single Home Assistant instance.
- **Persistent Energy Metering**: Power sensors (kW/W) are automatically integrated into energy sensors (kWh) using Riemann sum logic, ensuring stable data for long-term statistics.
- **Smart Analytics**: Built-in calculations for conversion loss, round-trip efficiency, and time-to-target estimations.
- **Localized**: Full native support for **Finnish (FI)** and **English (EN)**.


## 🚀 Installation

### Option 1: HACS (Recommended)
1. Open **HACS** > **Integrations**.
2. Click the three dots in the top right and select **Custom Repositories**.
3. Paste: `https://github.com/Jarauvi/elisa_kotiakku`
4. Select category **Integration** and click **Add**.
5. Find "Elisa Kotiakku" and click **Download**.
6. **Restart** Home Assistant.

### Option 2: Manual
1. Download the `elisa_kotiakku` folder from `custom_components/`.
2. Copy it to your Home Assistant `config/custom_components/` directory.
3. **Restart** Home Assistant.


## ⚙️ Configuration

1. Navigate to **Settings** > **Devices & Services**.
2. Click **Add Integration** ➕ and search for **Elisa Kotiakku**.
3. Configure the following options:

| Option | Description |
| :--- | :--- |
| **Device Name** | The name for this battery instance (e.g., "Kotiakku"). |
| **API URL** | The endpoint provided by Elisa (just use default one). |
| **API Key** | Your private authentication key (get from the Kotiakku app). |
| **Update Interval** | Polling frequency in seconds (Minimum **300s** recommended). |
| **Power Unit** | Choose between **kW** or **W**. |
| **Battery Capacity** | Nominal capacity in **kWh** (used for cycle counting and time estimation). |


## 📊 Available Sensors

### ⚡ Power Sensors (Current Flow)
| Entity ID (Example) | Name (FI) | Description |
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
| `battery_loss_kw` | Akun tehohäviö | Estimated power lost during conversion |

### 📊 Energy Sensors (Cumulative Totals in kWh)
| Entity ID | Name (FI) | Description |
| :--- | :--- | :--- |
| `house_energy_kwh` | Talon kokonaiskulutus | Total energy consumed by the property |
| `solar_energy_kwh` | Aurinkopaneelien kokonaistuotto | Total energy produced by panels |
| `total_grid_import_kwh` | Verkosta ostettu kokonaisenergia | Total energy imported from grid |
| `total_grid_export_kwh` | Verkkoon myyty kokonaisenergia | Total energy exported to grid |
| `total_battery_charge_kwh` | Akun kokonaislataus | Total energy put into the battery |
| `total_battery_discharge_kwh` | Akun kokonaispurku | Total energy taken from the battery |

### 🔋 Diagnostics & Battery State
| Entity ID | Name (FI) | Description |
| :--- | :--- | :--- |
| `state_of_charge_percent` | Akun varaustila | Battery charge level (0–100%) |
| `battery_state` | Akun tila | Current mode: *Lataa*, *Purkaa*, or *Odottaa* |
| `battery_temperature_celsius` | Akun lämpötila | Internal battery temperature |
| `battery_efficiency_ratio` | Akun hyötysuhde | Calculated round-trip efficiency percentage |
| `battery_charge_efficiency` | Latauksen hyötysuhde | Calculated charging efficiency percentage |
| `battery_discharge_efficiency` | Purkamisen hyötysuhde | Calculated discharging efficiency percentage |
| `battery_cycle_count` | Akun syklit | Calculated discharge cycles based on capacity |
| `time_to_90_percent` | Lataus 90% varaustilaan | Est. minutes until 90% SoC is reached |
| `time_to_15_percent` | Purku 15% varaustilaan | Est. minutes until 15% SoC is reached |

### 💶 Market Data and Savings
| Entity ID | Name (FI) | Description |
| :--- | :--- | :--- |
| `spot_price_cents_per_kwh` | Pörssisähkön hinta | Current electricity spot price |
| `net_savings_rate` | Tuntikohtainen säästö | Current financial impact (€/h) based on spot price |


## 🗺️ Roadmap
- [ ] Add button entities to reset energy counters manually.
- [x] add efficiency ratio sensor
- [x] add cost savings estimation sensor
- [x] add sensors to estimate when battery is depleted/charged with current usage/charging power


## ⚠️ Disclaimer
This integration is a community project and is **not** affiliated with, endorsed by, or supported by Elisa. Use at your own risk.
