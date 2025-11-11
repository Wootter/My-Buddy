# My Buddy — Cloud Server

Flask + SQLAlchemy web application with automatic Viam robot sensor data collection.

---

## Quick Start

### 1. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 2. Run the Application
```powershell
python main.py
```

The app will:
- Start Flask server on `http://127.0.0.1:5000`
- Automatically fetch Viam sensor data hourly
- Display sensor graphs at `/data`

---

## Features

- **Authentication System**: Login/register with email and password
- **Sensor Dashboard**: Real-time graphs showing sensor data
- **Automatic Data Collection**: Fetches data from Viam robot every hour
- **Manual Refresh**: Button to fetch data on demand
- **RESTful API**: JSON endpoints for sensor management

---

## Configuration

### Viam Robot Setup

Your sensors are already configured in `viam_integration.py`:

| Sensor | Type | Viam Component |
|--------|------|----------------|
| DHT22 Temperature | temperature | dht22_sensor |
| DHT22 Humidity | humidity | dht22_sensor |
| VEML7700 Light | light | VEML7700 |
| MH-SR602 Motion | motion | MH-SR602 |

**Robot:** `my-buddy-main.1zxw399cc5.viam.cloud`

---

## Pages

- **`/`** - Home page
- **`/login`** - User login
- **`/register`** - Create account
- **`/profile`** - Account dashboard
- **`/data`** - Sensor graphs (with refresh button)
- **`/logout`** - Logout

---

## API Endpoints

### Manual Data Fetch
```http
POST /api/viam/fetch-now
```
Immediately fetches data from Viam sensors.

### Test Connection
```http
GET /api/viam/test
```
Tests connection to Viam robot.

---

## Database Structure

**Account** → owns → **Sensor** → has → **SensorData**

```
Account (email, username, password)
  └─ Sensor (name, type)
      └─ SensorData (timestamp, value, unit)
```

---

## Technology Stack

- **Flask 2.2+** - Web framework
- **SQLAlchemy 3.0+** - ORM
- **SQLite** - Database
- **APScheduler 3.10+** - Background tasks
- **Viam SDK 0.27+** - Robot integration
- **Chart.js** - Data visualization

---

## Troubleshooting

### No sensor data appearing?
- Check Flask console for "Stored X/4 sensor readings"
- Visit `/api/viam/test` to test connection
- Click "Refresh Data Now" button on `/data` page

### DHT22 showing errors?
- Normal if sensor isn't wired up yet
- Other sensors (VEML7700, MH-SR602) should still work

---

## Notes

- Passwords are hashed using Werkzeug
- Sessions use Flask cookies
- Database file: `instance/mybuddy.db`
- Data fetches automatically every hour
- All graphs share the same timeline (X-axis)
