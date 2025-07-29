# Elasticsearch Index Size Tracker - Setup Guide

## Overview

This Python script monitors your Elasticsearch cluster growth by tracking index sizes daily and calculating growth trends. It generates two CSV files:
- **Index sizes**: Raw daily measurements of each index
- **Growth analysis**: Calculated growth rates and trends

## Prerequisites

- Python 3.7 or higher
- Access to Elasticsearch Cloud deployment
- API key with read permissions
- macOS, Linux, or Windows system

---

## Step 1: Prepare Your Environment

### For macOS/Linux:

```bash
# Create a project directory
mkdir ~/elasticsearch-tracker
cd ~/elasticsearch-tracker

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install required dependencies
pip install requests
```

### For Windows:

```cmd
# Create a project directory
mkdir C:\elasticsearch-tracker
cd C:\elasticsearch-tracker

# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate

# Install required dependencies
pip install requests
```

---

## Step 2: Get Your Elasticsearch Cloud Credentials

### Get Your Elasticsearch URL:

1. Log into your **Elastic Cloud Console**
2. Navigate to your deployment
3. Copy the **Elasticsearch endpoint URL**
   - Example: `https://my-deployment-abc123.es.us-central1.gcp.cloud.es.io:9243`

### Create an API Key:

1. In your deployment, open **Kibana**
2. Go to **Stack Management** → **Security** → **API Keys**
3. Click **Create API Key**
4. Configure the API key:
   - **Name**: `elasticsearch-tracker`
   - **Expiration**: Set according to your security policy
   - **Role**: Ensure it has `monitor` and `read` permissions
5. Copy the generated **API Key** (base64 encoded string)

---

## Step 3: Download and Configure the Script

### Download the Script:

Save the Python script as `es_tracker.py` in your project directory.

### Configure Your Credentials:

Edit the script and update these lines (around line 25-26):

```python
# Replace these placeholder values:
ES_CLOUD_URL = "https://your-deployment.es.region.cloud.es.io"
API_KEY = "your-api-key-here"

# With your actual values:
ES_CLOUD_URL = "https://my-deployment-abc123.es.us-central1.gcp.cloud.es.io:9243"
API_KEY = "VnVhQ2ZHY0JDZGJrUW0tZTVhT3g6dWkybHA2MzdUeFNXRTJ4ZE1xdjNaUSdx"
```

**Security Note**: Keep your API key secure and never commit it to version control.

---

## Step 4: Test the Script

### Run a Test:

```bash
# Make sure your virtual environment is activated
# You should see (venv) in your prompt

# Run the script
python3 es_tracker.py
```

### Expected Output:

```
#############################################################################
#                    Elasticsearch Index Size Tracker                      #
#############################################################################

Starting Elasticsearch Index Size Tracker
Connecting to: https://your-deployment.es.region.cloud.es.io
Fetching index statistics...
Processing 5 indices...
Saving data to elasticsearch_index_sizes.csv...

================================================================================
ELASTICSEARCH INDEX SIZES - 2025-07-29 14:30:15
================================================================================
Index Name                                     Size (GB)        % of Total     
--------------------------------------------------------------------------------
logs-2025.07                                    5.2340 GB     63.50% [LARGE]
users-data                                      2.1890 GB     26.55% [MEDIUM]
search-index                                    0.8234 GB      9.95% [SMALL]
--------------------------------------------------------------------------------
TOTAL CLUSTER SIZE                               8.2464 GB    100.00%
================================================================================

WARNING: No growth analysis data available yet.
INFO: Run the script for a few days to see growth trends!

=============================================================================
OUTPUT FILES CREATED:
   Index sizes: elasticsearch_index_sizes.csv
   Growth analysis: elasticsearch_growth_analysis.csv
=============================================================================
```

---

## Step 5: Verify Output Files

### Check Generated Files:

```bash
# List the files created
ls -la *.csv

# View the index sizes file
cat elasticsearch_index_sizes.csv

# After running for multiple days, view growth analysis
cat elasticsearch_growth_analysis.csv
```

### File Structure:

**elasticsearch_index_sizes.csv:**
```csv
Date,Index_Name,Size_GB
2025-07-29 09:00:15,index-1,2.5432
2025-07-29 09:00:15,index-2,1.8765
2025-07-29 09:00:15,_TOTAL_CLUSTER_,8.2464
```

**elasticsearch_growth_analysis.csv (after 2+ days):**
```csv
Date,Total_Size_GB,Daily_Growth_GB,Growth_Percentage
2025-07-29,8.2464,0.1234,1.52
2025-07-30,8.5678,0.3214,3.90
```

---

## Step 6: Set Up Daily Automation

### Option A: Cron Job (macOS/Linux)

```bash
# Open crontab editor
crontab -e

# Add this line to run daily at 9:00 AM:
0 9 * * * cd /Users/yourusername/elasticsearch-tracker && source venv/bin/activate && python3 es_tracker.py >> tracker.log 2>&1
```

### Option B: Windows Task Scheduler

1. Open **Task Scheduler**
2. Click **Create Basic Task**
3. Configure:
   - **Name**: Elasticsearch Tracker
   - **Trigger**: Daily at desired time
   - **Action**: Start a program
   - **Program**: `C:\elasticsearch-tracker\venv\Scripts\python.exe`
   - **Arguments**: `es_tracker.py`
   - **Start in**: `C:\elasticsearch-tracker`

### Option C: Cloud Functions (Advanced)

Deploy the script as:
- **AWS Lambda** with EventBridge scheduler
- **Google Cloud Functions** with Cloud Scheduler
- **Azure Functions** with Timer Trigger

---

## Step 7: Monitor and Analyze Growth

### Daily Monitoring:

After running for several days, you'll see growth analysis:

```
=================================================================================
GROWTH ANALYSIS - LAST 7 DAYS
=================================================================================
Date         Total (GB)   Growth (GB)  Growth %   Trend          
---------------------------------------------------------------------------------
2025-07-23      7.2340     0.1250      1.76%     STABLE         
2025-07-24      7.8920     0.6580      9.10%     HIGH GROWTH    
2025-07-25      8.1200     0.2280      2.89%     GROWING        
---------------------------------------------------------------------------------
SUMMARY STATISTICS:
   Average Daily Growth:     0.3370 GB
   Total Growth (Period):    1.0110 GB  
   Assessment: MODERATE growth - plan for scaling
=================================================================================
```

### Advanced Analysis:

Import CSV files into Excel or Google Sheets for:
- **Trend charts** and visualizations
- **Capacity planning** calculations
- **Cost forecasting** based on growth rates
- **Alerting** on unusual growth patterns

---

## Troubleshooting

### Common Issues:

1. **"Module not found: requests"**
   ```bash
   # Ensure virtual environment is activated and install requests
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install requests
   ```

2. **"Connection failed"**
   - Verify your Elasticsearch URL is correct
   - Check that your API key is valid and has proper permissions
   - Ensure your network can reach the Elasticsearch endpoint

3. **"Permission denied"**
   - Make sure your API key has `monitor` and `read` permissions
   - Check if your Elasticsearch deployment is accessible

4. **"No indices found"**
   - Verify your cluster has indices with data
   - Check if the API key has access to view indices

### Getting Help:

- Check the generated log files for detailed error messages
- Verify network connectivity to your Elasticsearch cluster
- Ensure API key permissions are correctly configured

---

## Security Best Practices

1. **API Key Security**:
   - Use environment variables instead of hardcoding credentials
   - Set appropriate expiration dates for API keys
   - Limit API key permissions to minimum required (read-only)

2. **Environment Variables** (Recommended):
   ```bash
   # Set environment variables
   export ES_CLOUD_URL="https://your-deployment.es.region.cloud.es.io"
   export ES_API_KEY="your-api-key-here"
   
   # Update script to use environment variables:
   ES_CLOUD_URL = os.getenv('ES_CLOUD_URL')
   API_KEY = os.getenv('ES_API_KEY')
   ```

3. **File Permissions**:
   ```bash
   # Restrict access to script and data files
   chmod 600 es_tracker.py *.csv
   ```

---

## Support and Maintenance

### Regular Maintenance:
- Monitor log files for errors
- Rotate log files periodically
- Review and update API keys before expiration
- Backup historical CSV data

### Scaling Considerations:
- For large clusters (100+ indices), consider running during off-peak hours
- Monitor script execution time and adjust timeout settings if needed
- Consider archiving old CSV data after extended periods

### Customization:
The script can be easily modified to:
- Change output file names and locations  
- Adjust the number of days shown in growth analysis
- Add email notifications for growth alerts
- Export data to databases or monitoring systems
