# Database Restructure: ViaDevice → Robot + UserRobot

## What Changed

### Old Model (ViaDevice)
- One-to-one relationship between User and Device
- Deleting device loses credentials but kept data
- Only one user per device

### New Model (Robot + UserRobot)
```
Robot (Independent entity)
  ├── robot_name
  ├── viam_robot_address (unique identifier)
  ├── status
  └── last_connected

UserRobot (User's connection to Robot)
  ├── account_id → Account
  ├── robot_id → Robot
  ├── viam_api_key (user's credentials)
  ├── viam_api_key_id
  └── added_at

Sensor (now links to Robot, not Account)
  ├── robot_id → Robot
  └── (all sensor readings stay)

SensorData (unchanged)
  └── links to Sensor
```

## Benefits

✅ **Multiple users can share the same robot**
- User A adds Robot X → Creates Robot X
- User B adds Robot X → Uses existing Robot X
- Both see shared sensor data

✅ **Data persists when removing device**
- Delete UserRobot connection (just removes from profile)
- Robot stays with all historical sensor data
- Re-add robot later, all data is still there

✅ **One source of truth for each robot**
- Robot status/last_connected is shared
- Prevents duplicate robots for same address
- Cleaner sensor data organization

## Migration Steps

### On Your Server:

1. **Pull the latest code**
   ```bash
   cd /root/My-Buddy/Cloud\ Server
   git pull
   ```

2. **Backup your database (IMPORTANT!)**
   ```bash
   cp instance/mybuddy.db instance/mybuddy.db.backup
   ```

3. **Create new tables**
   ```bash
   source /root/My-Buddy/env/bin/activate
   cd /root/My-Buddy/Cloud\ Server
   python3 -c "from main import app, db; app.app_context().push(); db.create_all(); print('✓ Tables created')"
   ```

4. **Run migration script**
   ```bash
   python3 migrate_to_robot_model.py
   ```
   This will:
   - Find all existing ViaDevice records
   - Create Robot entries
   - Create UserRobot connections
   - Preserve all credentials

5. **Restart gunicorn**
   ```bash
   pkill -f gunicorn
   source /root/My-Buddy/env/bin/activate
   cd /root/My-Buddy/Cloud\ Server
   /root/My-Buddy/env/bin/gunicorn main:app &
   ```

6. **Verify in database**
   ```bash
   sqlite3 instance/mybuddy.db ".tables"
   # Should show: account robot sensor sensor_data user_robot
   
   sqlite3 instance/mybuddy.db "SELECT * FROM robot;"
   sqlite3 instance/mybuddy.db "SELECT * FROM user_robot;"
   ```

## API Changes

### Old Endpoints (no longer work)
- `GET /api/devices` - Returns ViaDevice records
- `POST /api/devices` - Creates ViaDevice
- `DELETE /api/devices/<id>` - Deletes ViaDevice
- `POST /api/devices/<id>/connect` - Connects to device

### New Endpoints (same URLs, different response)
- `GET /api/devices` - Returns UserRobot records with robot info
- `POST /api/devices` - Creates Robot if needed + UserRobot connection
- `DELETE /api/devices/<id>` - Deletes UserRobot (keeps Robot & data)
- `POST /api/devices/<id>/connect` - Updates Robot status

## Form Fields Updated

**Old Form (ViaDevice)**
```
- device_name
- viam_api_key
- viam_api_key_id
- viam_robot_address
```

**New Form (Robot + UserRobot)**
```
- robot_name (was device_name, now matches Robot.robot_name)
- viam_api_key
- viam_api_key_id
- viam_robot_address
```

## Example Flow

**Scenario: Two users adding the same Raspberry Pi**

### User A adds robot:
1. Fills form: "My Pi", API key A, key ID A, address "my-pi.viam.cloud"
2. Backend creates Robot with address "my-pi.viam.cloud"
3. Creates UserRobot linking User A to Robot with their credentials
4. Sensor data starts being saved to Robot

### User B adds same robot:
1. Fills form: "Shared Pi", API key B, key ID B, address "my-pi.viam.cloud"
2. Backend finds existing Robot (same address)
3. Creates UserRobot linking User B to same Robot with their credentials
4. Both users now see the same sensor data!

### User A deletes device:
1. Deletes UserRobot (user-robot connection)
2. Robot stays in database
3. Sensor data persists
4. User B still has access
5. User A can re-add later with fresh credentials

## Rollback (if needed)

If migration fails:

```bash
# Restore backup
cp instance/mybuddy.db.backup instance/mybuddy.db

# Revert code
git revert HEAD
git pull

# Restart
pkill -f gunicorn
/root/My-Buddy/env/bin/gunicorn main:app &
```

## Questions?

If migration fails or you have questions:
1. Check the migration script output for errors
2. Verify database backup was created
3. Check gunicorn logs: `/root/My-Buddy/gunicorn.log`
4. Test from your local machine first if unsure
