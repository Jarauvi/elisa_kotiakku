<div align="center">
  <img src="https://github.com/Jarauvi/elisa_kotiakku/blob/main/custom_components/elisa_kotiakku/brand/icon.png?raw=true" width="128" height="128">

  # Elisa Kotiakku for Home Assistant

  [![Home Assistant](https://img.shields.io/badge/home%20assistant-%2341BDF5.svg?style=for-the-badge&logo=home-assistant&logoColor=white)](https://www.home-assistant.io/)
  [![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://hacs.xyz/)
  [![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

  [![Version](https://img.shields.io/github/manifest-json/v/Jarauvi/elisa_kotiakku?filename=custom_components%2Felisa_kotiakku%2Fmanifest.json&label=Version)](https://github.com/Jarauvi/elisa_kotiakku)
  [![Tests](https://github.com/Jarauvi/elisa_kotiakku/actions/workflows/tests.yaml/badge.svg)](https://github.com/Jarauvi/elisa_kotiakku/actions)
  ![Cloud Polling](https://img.shields.io/badge/IOT_class-Cloud_polling-blue)

  **Integrate your Elisa Kotiakku energy storage system into Home Assistant.**
  *Monitor solar production, battery health, and real-time energy costs. Batteries not included.*

  **New!** Check out the [elisa_kotiakku_cards](https://github.com/Jarauvi/elisa_kotiakku_cards) repository for custom UI.

  <img src="https://github.com/Jarauvi/elisa_kotiakku/blob/main/images/kotiakku_diagnostics_card.png?raw=true" width="400">
</div>

---

## ✨ Features

- **Device-Centric**: All sensors are automatically grouped under a single **Elisa Kotiakku device**.
- **Multi-Instance Support**: Manage multiple battery systems independently.
- **Advanced Energy Metering**: Real-time power sensors (kW/W) are automatically integrated into energy sensors (kWh) for full compatibility with the **HA Energy Dashboard**.
- **Smart Analytics**: Built-in logic for conversion loss, round-trip efficiency, and time-to-target estimations (SoC 90% / 15%).
- **Financial Tracking**: Dynamic cost calculation including Spot Price + Transfer Fees + VAT.
- **Data Safety**: Specialized services to restore accumulated totals from history if data is lost.
- **Localization**: Full support for **Finnish (FI)** and **English (EN)**.

---

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

---

## ⚙️ Configuration

### 1. Initial Setup
1. Navigate to **Settings** > **Devices & Services**.
2. Click **Add Integration** ➕ and search for **Elisa Kotiakku**.
3. Complete the following sections:

#### **Section: API Settings**
| Option | Description |
| :--- | :--- |
| **API URL** | The endpoint provided by Elisa (use default). |
| **API Key** | Your private authentication key from the Kotiakku app. |
| **Scan Interval** | Polling frequency in seconds (Min **300s**). |

#### **Section: Battery Settings**
| Option | Description |
| :--- | :--- |
| **Battery Capacity** | Nominal capacity in **kWh** (used for charge time estimations). |
| **Power Unit** | Display power sensors in **kW** or **W**. |

#### **Section: Currency & Pricing**
| Option | Description |
| :--- | :--- |
| **Add VAT** | Include Value Added Tax in cost calculations. |
| **VAT %** | Your local VAT rate (e.g., **25.5%** in Finland). |
| **Transfer Pricing** | `Fixed`, `Day/Night`, `Seasonal`, or `Ignore`. |

### 2. Secondary Pricing Logic (Conditional)
Based on your **Transfer Pricing** selection, a second screen will appear:
* **Fixed Transfer:** Input price (`c/kWh`), electricity tax, and export fees.
* **Day/Night Transfer:** Define start times and distinct rates for Day and Night.
* **Seasonal Transfer:** Configure Winter/Summer months and peak pricing rules.

---

## 🛠 Services

This integration provides services to manage your long-term energy data:

| Service | Description |
| :--- | :--- |
| `set_max_from_history` | Scans HA history for the highest recorded energy/savings values and restores them. Use this if your sensors accidentally reset to zero. |
| `reset_accumulated_sensors` | Manually resets all energy and savings counters for the device back to zero. |

---

## 📊 Available Sensors

### ⚡ Power Sensors (Current Flow)
| Entity ID (Example) | Name (FI) | Description |
| :--- | :--- | :--- |
| `battery_power_kw` | Akun kokonaisteho | Current battery charge (+) or discharge (-) |
| `solar_power_kw` | Aurinkopaneelien kokonaisteho | Total current solar production |
| `grid_power_kw` | Verkon kokonaisteho | Total current grid exchange |
| `house_power_kw` | Kiinteistön kokonaiskulutus | Current total building consumption |
| `solar_to_house_kw` | Aurinkopaneeleilta kiinteistölle | Solar power used directly by the house |
| `solar_to_battery_kw` | Aurinkopaneeleilta akkuun | Solar power going into storage |
| `solar_to_grid_kw` | Aurinkopaneeleilta verkkoon | Solar power being exported |
| `grid_to_house_kw` | Verkosta kiinteistölle | Grid power used by the house |
| `grid_to_battery_kw` | Verkosta akkuun | Grid power used to charge the battery |
| `battery_to_house_kw` | Akusta kiinteistölle | Battery power used by the house |
| `battery_to_grid_kw` | Akusta verkkoon | Battery power being exported |
| `battery_loss_kw` | Akun häviöteho | Estimated power lost during conversion |

### 📊 Energy Sensors (Cumulative Totals in kWh)
| Entity ID | Name (FI) | Description |
| :--- | :--- | :--- |
| `house_energy_kwh` | Kiinteistön kokonaiskulutus | Total cumulative energy consumed |
| `solar_energy_kwh` | Aurinkopaneelien kokonaistuotto | Total cumulative energy produced |
| `total_grid_import_kwh` | Verkosta ostettu kokonaisenergia | Total energy imported from grid |
| `total_grid_export_kwh` | Verkkoon myyty kokonaisenergia | Total energy exported to grid |
| `total_battery_charge_kwh` | Akun kokonaislatausenergia | Total energy put into the battery |
| `total_battery_discharge_kwh` | Akun kokonaispurkuenergia | Total energy taken from the battery |
| `solar_to_house_kwh` | Aurinkopaneeleilta kiinteistölle | Total solar energy used by house |
| `solar_to_battery_kwh` | Aurinkopaneeleilta akkuun | Total solar energy stored |
| `solar_to_grid_kwh` | Aurinkopaneeleilta verkkoon | Total solar energy exported |
| `grid_to_house_kwh` | Verkosta kiinteistölle | Total grid energy used by house |
| `grid_to_battery_kwh` | Verkosta akkuun | Total grid energy stored |
| `battery_to_house_kwh` | Akusta kiinteistölle | Total battery energy used by house |
| `battery_to_grid_kwh` | Akusta verkkoon | Total battery energy exported |
| `battery_loss_kwh` | Akun kokonaisenergiahäviö | Total energy lost in conversion |

### 🔋 Diagnostics & Battery State
| Entity ID | Name (FI) | Description |
| :--- | :--- | :--- |
| `state_of_charge_percent` | Akun varaustila | Battery charge level (0–100%) |
| `battery_state` | Akun tila | *Lataa*, *Purkaa*, *Odottaa*, or *Yhteysvirhe* |
| `battery_temperature_celsius` | Akun lämpötila | Internal battery temperature |
| `battery_efficiency_ratio` | Akun kokonaishyötysuhde | Calculated round-trip efficiency |
| `battery_charge_efficiency` | Latauksen hyötysuhde | Efficiency while charging (*ei lataa* if idle) |
| `battery_discharge_efficiency` | Purkamisen hyötysuhde | Efficiency while discharging (*ei pura* if idle) |
| `battery_cycle_count` | Akun lataussyklit | Calculated cycles based on nominal capacity |
| `time_to_90_percent` | Ladattu 90% tasoon ajassa | Est. minutes until 90% SoC |
| `time_to_15_percent` | Purettu 15% tasoon ajassa | Est. minutes until 15% SoC |

### 💶 Market Data & Savings
| Entity ID | Name (FI) | Description |
| :--- | :--- | :--- |
| `spot_price_cents_per_kwh` | Pörssisähkön hinta | Current market spot price |
| `net_savings_rate` | Säästöt / tunti | Current financial impact in €/h |
| `total_savings_eur` | Kumuloituvat säästöt | Total financial savings since installation |

---

## 🗺️ Roadmap
### Sensors
- [ ] add breakdown of costs/savings to total savings sensor attributes
- [x] add total savings sensor
- [x] add total energy loss sensor
- [x] add efficiency ratio sensor
- [x] add cost savings estimation sensor
- [x] add sensors to estimate when battery is depleted/charged with current usage/charging power
- [x] add energy transfer options to savings sensor, configurable from config/options flows

### Services
- [x] add service to reset energy counters manually.
- [x] add service to retrieve latest maximum energy/savings values if those are accidentally reset

### Under the hood
- [ ] add seller's margin part for purchased energy
- [x] migrate calculations from sensors to coordinator
- [x] restructure config flow for better user experience

## ⚠️ Disclaimer
This integration is a community project and is **not** affiliated with, endorsed by, or supported by Elisa. Use at your own risk. 
