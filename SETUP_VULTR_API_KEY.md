# Setting Up VULTR_API_KEY

## Issue
The data-collector services are failing because VULTR_API_KEY is not set in the environment.

## Solution

### Option 1: Set in .env file (Recommended)

1. **Copy the example file:**
```powershell
Copy-Item .env.example .env
```

2. **Edit the .env file and add your Vultr API key:**
```bash
VULTR_API_KEY=your-actual-vultr-api-key-here
```

3. **Restart the services:**
```powershell
docker-compose restart data-collector data-collector-worker data-collector-beat
```

### Option 2: Set as environment variable

```powershell
# Set for current session
$env:VULTR_API_KEY = "your-actual-vultr-api-key-here"

# Restart services
docker-compose restart data-collector data-collector-worker data-collector-beat
```

### Option 3: Set directly in docker-compose.yml (Not recommended for security)

Edit `docker-compose.yml` and replace:
```yaml
VULTR_API_KEY: ${VULTR_API_KEY:-}
```

With:
```yaml
VULTR_API_KEY: "your-actual-vultr-api-key-here"
```

Then restart services.

---

## How to Get Your Vultr API Key

1. Log in to your Vultr account: https://my.vultr.com/
2. Go to Account → API
3. Click "Enable API"
4. Copy your API key
5. Add it to your .env file

---

## Verify It's Working

After setting the key and restarting services:

```powershell
# Check if the key is set in the container
docker exec optiinfra-data-collector-worker printenv | Select-String "VULTR"

# Should show:
# VULTR_API_KEY=your-key-here
```

### Test Collection

```powershell
curl -Method POST -Uri "http://localhost:8005/api/v1/collect/trigger" `
  -ContentType "application/json" `
  -Body '{"customer_id":"test_user","provider":"vultr","data_types":["cost"],"async_mode":true}'
```

### Check Worker Logs

```powershell
docker logs optiinfra-data-collector-worker --tail 50
```

You should see successful collection instead of "VULTR_API_KEY not configured" error.

---

## Current Status

❌ **VULTR_API_KEY is NOT set**

The services are running but collections are failing because the API key is missing.

**Action Required:** Follow Option 1 above to set your API key.
