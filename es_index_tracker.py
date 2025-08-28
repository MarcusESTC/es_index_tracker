#!/usr/bin/env python3
"""
#############################################################################
#                    Elasticsearch Index Size Tracker                      #
#                         (Primary Storage Analysis)                       #
#                                                                           #
#  Monitor your Elasticsearch data growth with detailed analytics          #
#  Tracks primary index sizes daily (excludes replicas)                    #
#  Generates pure data growth reports for capacity planning                 #
#                                                                           #
#  Author: Marcus Rodrigues                                                #
#  Version: 5 - Primary Storage Focus                                    #
#  Last Updated: August 2025                                               #
#############################################################################
"""

import requests
import json
import csv
import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import sys

# =============================================================================
#                               CONFIGURATION
# =============================================================================

# Elasticsearch Connection Settings
ES_CLOUD_URL = "https://your-deployment.es.region.cloud.es.io"  # Your ES Cloud URL
API_KEY = "your-api-key-here"                                   # Your API Key

# Output File Settings
OUTPUT_FILE = "elasticsearch_primary_sizes.csv"       # Raw primary index size data
GROWTH_FILE = "elasticsearch_primary_growth.csv"      # Primary data growth analysis

# =============================================================================
#                           ELASTICSEARCH TRACKER CLASS
# =============================================================================

class ElasticsearchSizeTracker:
    """
    Main class for tracking Elasticsearch index sizes and growth trends.
    
    This class handles:
    - Connection to Elasticsearch Cloud
    - Fetching index statistics via Cat Indices API
    - Storing data in CSV format
    - Calculating and displaying growth metrics
    """
    
    def __init__(self, es_url: str, api_key: str):
        """
        Initialize the Elasticsearch Size Tracker.
        
        Args:
            es_url (str): Elasticsearch cloud deployment URL
            api_key (str): API key for authentication
        """
        self.es_url = es_url.rstrip('/')
        self.headers = {
            'Authorization': f'ApiKey {api_key}',
            'Content-Type': 'application/json'
        }
    
    def get_index_stats(self) -> List[Dict]:
        """
        Fetch index statistics using the efficient Cat Indices API.
        Fetches primary storage size only for pure data growth analysis.
        
        Returns:
            List[Dict]: List of index information with name and primary storage size
            
        Raises:
            SystemExit: If unable to connect to Elasticsearch
        """
        try:
            # Using Cat Indices API for primary storage size (excluding replicas)
            url = f"{self.es_url}/_cat/indices?format=json&bytes=b&h=index,pri.store.size"
            
            print("Fetching index statistics (primary storage only)...")
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"ERROR: Unable to fetch index stats: {e}")
            sys.exit(1)
    
    def calculate_index_sizes(self, indices_data: List[Dict]) -> List[Tuple[str, float]]:
        """
        Convert primary index sizes from bytes to GB for better readability.
        Handles None values and various data types safely.
        Tracks primary storage only (excludes replicas) for pure data growth analysis.
        
        Args:
            indices_data (List[Dict]): Raw index data from Cat Indices API
            
        Returns:
            List[Tuple[str, float]]: List of (index_name, primary_size_in_gb) tuples
        """
        index_sizes = []
        
        if not indices_data:
            print("WARNING: No indices found in response")
            return index_sizes
        
        print(f"Processing {len(indices_data)} indices...")
        
        null_count = 0
        error_count = 0
        
        for index_info in indices_data:
            index_name = index_info.get('index', 'unknown')
            
            # Safely handle pri.store.size which might be None, string, or number
            store_size_raw = index_info.get('pri.store.size')
            
            if store_size_raw is None:
                # Handle None case (common with searchable snapshots, frozen indices)
                size_bytes = 0
                null_count += 1
            elif store_size_raw == '':
                # Handle empty string case
                size_bytes = 0
            else:
                try:
                    # Convert to int, handling both string and numeric inputs
                    size_bytes = int(store_size_raw)
                except (ValueError, TypeError) as e:
                    print(f"WARNING: Cannot parse primary store size for '{index_name}': {store_size_raw} - using 0")
                    error_count += 1
                    size_bytes = 0
            
            # Convert bytes to GB (1 GB = 1024³ bytes)
            size_gb = size_bytes / (1024 ** 3)
            index_sizes.append((index_name, size_gb))
        
        # Summary of issues found
        if null_count > 0:
            print(f"INFO: Found {null_count} indices with null primary store sizes (likely searchable snapshots or frozen indices)")
        if error_count > 0:
            print(f"WARNING: Found {error_count} indices with unparseable primary store sizes")
        
        return index_sizes
    
    def get_total_cluster_size(self, index_sizes: List[Tuple[str, float]]) -> float:
        """
        Calculate total primary cluster size by summing all primary index sizes.
        This excludes replica storage for pure data growth analysis.
        
        Args:
            index_sizes (List[Tuple[str, float]]): Individual primary index sizes
            
        Returns:
            float: Total primary cluster size in GB (excluding replicas)
        """
        return sum(size for _, size in index_sizes)
    
    def save_to_csv(self, index_sizes: List[Tuple[str, float]], total_size: float, output_file: str):
        """
        Save primary index sizes to CSV file with timestamp.
        
        Args:
            index_sizes (List[Tuple[str, float]]): Individual primary index sizes
            total_size (float): Total primary cluster size
            output_file (str): Path to output CSV file
        """
        current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Check if file exists to determine if we need headers
        file_exists = os.path.exists(output_file)
        
        print(f"Saving primary storage data to {output_file}...")
        
        with open(output_file, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write headers if file is new
            if not file_exists:
                writer.writerow(['Date', 'Index_Name', 'Primary_Size_GB'])
            
            # Write individual primary index sizes
            for index_name, size_gb in sorted(index_sizes):
                writer.writerow([current_date, index_name, f"{size_gb:.4f}"])
            
            # Write total primary cluster size with special marker
            writer.writerow([current_date, '_TOTAL_PRIMARY_CLUSTER_', f"{total_size:.4f}"])
    
    def display_current_sizes(self, index_sizes: List[Tuple[str, float]], total_size: float, show_zero_sizes: bool = False):
        """
        Display current primary index sizes in a formatted console output.
        Shows primary storage only (excludes replicas) for data growth analysis.
        
        Args:
            index_sizes (List[Tuple[str, float]]): Individual primary index sizes
            total_size (float): Total primary cluster size
            show_zero_sizes (bool): Whether to show indices with 0 GB primary size
        """
        # Filter out zero-sized indices if requested
        if not show_zero_sizes:
            filtered_sizes = [(name, size) for name, size in index_sizes if size > 0]
            zero_count = len(index_sizes) - len(filtered_sizes)
        else:
            filtered_sizes = index_sizes
            zero_count = 0
        
        print(f"\n{'='*85}")
        print(f"ELASTICSEARCH PRIMARY INDEX SIZES - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"(Primary storage only - excludes replicas for data growth analysis)")
        if zero_count > 0:
            print(f"(Hiding {zero_count} zero-sized indices - set show_zero_sizes=True to display)")
        print(f"{'='*85}")
        print(f"{'Index Name':<50} {'Primary (GB)':<15} {'% of Total':<15}")
        print(f"{'-'*85}")
        
        # Sort by size (largest first) for better visualization
        sorted_indices = sorted(filtered_sizes, key=lambda x: x[1], reverse=True)
        
        for index_name, size_gb in sorted_indices:
            # Calculate percentage of total
            percentage = (size_gb / total_size * 100) if total_size > 0 else 0
            
            # Category indicator based on size
            if size_gb > total_size * 0.3:  # Large index (>30% of total)
                category = "[LARGE]"
            elif size_gb > total_size * 0.1:  # Medium index (>10% of total)
                category = "[MEDIUM]"
            else:  # Small index
                category = "[SMALL]"
            
            print(f"{index_name:<50} {size_gb:>10.4f} GB   {percentage:>8.2f}% {category}")
        
        print(f"{'-'*85}")
        print(f"{'TOTAL PRIMARY CLUSTER SIZE':<50} {total_size:>10.4f} GB   {'100.00%':>8}")
        if zero_count > 0:
            print(f"{'ZERO-SIZED INDICES':<50} {zero_count:>10} indices")
        print(f"{'='*85}")
        print("NOTE: This shows primary storage only (no replicas) for pure data growth analysis")

    def run(self, output_file: str = OUTPUT_FILE, show_zero_sizes: bool = False):
        """
        Main execution method - orchestrates the entire tracking process.
        
        Args:
            output_file (str): Path to the main CSV output file
            show_zero_sizes (bool): Whether to display zero-sized indices
        """
        print(f"\nStarting Elasticsearch Index Size Tracker")
        print(f"Connecting to: {self.es_url}")
        
        # Get index statistics using Cat Indices API
        indices_data = self.get_index_stats()
        
        # Calculate sizes in GB
        index_sizes = self.calculate_index_sizes(indices_data)
        total_size = self.get_total_cluster_size(index_sizes)
        
        if not index_sizes:
            print("ERROR: No indices found or error calculating sizes")
            return
        
        # Save to CSV
        self.save_to_csv(index_sizes, total_size, output_file)
        
        # Display results
        self.display_current_sizes(index_sizes, total_size, show_zero_sizes)

# =============================================================================
#                           GROWTH ANALYSIS FUNCTIONS
# =============================================================================

def save_growth_analysis(csv_file: str, growth_file: str) -> Optional[List[Dict]]:
    """
    Analyze primary data growth trends and save to dedicated growth file.
    
    This function:
    - Reads historical primary storage data from the main CSV file
    - Calculates daily growth rates and percentages for primary data only
    - Saves growth analysis to a separate CSV file
    - Prevents duplicate entries for the same date
    
    Args:
        csv_file (str): Path to main CSV file with raw primary storage data
        growth_file (str): Path to growth analysis CSV file
        
    Returns:
        Optional[List[Dict]]: List of new growth entries added, or None if no data
    """
    if not os.path.exists(csv_file):
        print(f"WARNING: No historical data found at {csv_file}")
        return None
    
    print("Analyzing primary data growth trends...")
    
    # Read CSV and extract daily totals (primary storage only)
    daily_totals = {}
    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            # Look for the primary cluster total marker
            if row['Index_Name'] == '_TOTAL_PRIMARY_CLUSTER_':
                date = row['Date'].split(' ')[0]  # Extract date part only
                # Handle both old format (Size_GB) and new format (Primary_Size_GB)
                size_gb = row.get('Primary_Size_GB') or row.get('Size_GB')
                if size_gb:
                    daily_totals[date] = float(size_gb)
    
    if len(daily_totals) < 2:
        print("INFO: Need at least 2 days of data for growth analysis")
        return None
    
    # Sort dates chronologically
    sorted_dates = sorted(daily_totals.keys())
    
    # Check for existing growth data to avoid duplicates
    growth_file_exists = os.path.exists(growth_file)
    last_growth_date = None
    
    if growth_file_exists:
        try:
            with open(growth_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    last_growth_date = row['Date']
        except Exception:
            pass  # File might be empty or corrupted
    
    # Calculate growth metrics
    growth_entries = []
    prev_size = None
    
    for date in sorted_dates:
        size = daily_totals[date]
        if prev_size is not None:
            growth_gb = size - prev_size
            growth_pct = (growth_gb / prev_size) * 100 if prev_size > 0 else 0
            
            # Only add entries newer than the last saved entry
            if last_growth_date is None or date > last_growth_date:
                growth_entries.append({
                    'Date': date,
                    'Primary_Size_GB': size,
                    'Daily_Growth_GB': growth_gb,
                    'Growth_Percentage': growth_pct
                })
        prev_size = size
    
    # Save new growth entries
    if growth_entries:
        with open(growth_file, 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Date', 'Primary_Size_GB', 'Daily_Growth_GB', 'Growth_Percentage']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Write headers if file is new
            if not growth_file_exists:
                writer.writeheader()
            
            # Write growth entries with proper formatting
            for entry in growth_entries:
                writer.writerow({
                    'Date': entry['Date'],
                    'Primary_Size_GB': f"{entry['Primary_Size_GB']:.4f}",
                    'Daily_Growth_GB': f"{entry['Daily_Growth_GB']:.4f}",
                    'Growth_Percentage': f"{entry['Growth_Percentage']:.2f}"
                })
        
        print(f"SUCCESS: Primary data growth analysis saved to: {growth_file}")
    else:
        print("INFO: No new growth data to save")
    
    return growth_entries

def display_growth_analysis(growth_file: str, show_last_days: int = 7):
    """
    Display recent primary data growth analysis in a formatted table.
    
    Args:
        growth_file (str): Path to the growth analysis CSV file
        show_last_days (int): Number of recent days to display (default: 7)
    """
    if not os.path.exists(growth_file):
        print("WARNING: No growth analysis data available yet.")
        print("INFO: Run the script for a few days to see primary data growth trends!")
        return
    
    # Read growth data
    growth_data = []
    try:
        with open(growth_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                growth_data.append(row)
    except Exception as e:
        print(f"ERROR: Unable to read growth file: {e}")
        return
    
    if not growth_data:
        print("INFO: No growth data available")
        return
    
    print(f"\n{'='*90}")
    print(f"PRIMARY DATA GROWTH ANALYSIS - LAST {show_last_days} DAYS")
    print(f"(Primary storage only - excludes replica growth)")
    print(f"{'='*90}")
    
    # Show last N days
    recent_data = growth_data[-show_last_days:] if len(growth_data) > show_last_days else growth_data
    
    print(f"{'Date':<12} {'Primary (GB)':<12} {'Growth (GB)':<12} {'Growth %':<10} {'Trend':<15}")
    print(f"{'-'*90}")
    
    total_growth = 0
    for i, entry in enumerate(recent_data):
        date = entry['Date']
        # Handle both old and new column names
        primary_size = float(entry.get('Primary_Size_GB') or entry.get('Total_Size_GB', 0))
        daily_growth = float(entry['Daily_Growth_GB'])
        growth_pct = float(entry['Growth_Percentage'])
        total_growth += daily_growth
        
        # Trend indicators based on growth percentage
        if growth_pct > 5:
            trend = "HIGH GROWTH"
        elif growth_pct > 2:
            trend = "GROWING"
        elif growth_pct > 0:
            trend = "STABLE"
        elif growth_pct > -2:
            trend = "DECLINING"
        else:
            trend = "SHARP DROP"
        
        print(f"{date:<12} {primary_size:>10.4f} {daily_growth:>10.4f} {growth_pct:>8.2f}% {trend:<15}")
    
    # Summary statistics
    if len(recent_data) > 1:
        avg_daily_growth = total_growth / len(recent_data)
        print(f"{'-'*90}")
        print(f"PRIMARY DATA GROWTH SUMMARY:")
        print(f"   Average Daily Growth: {avg_daily_growth:>10.4f} GB")
        print(f"   Total Growth (Period): {total_growth:>9.4f} GB")
        
        # Growth rate assessment for primary data
        if avg_daily_growth > 1:
            assessment = "HIGH data growth rate - monitor retention policies"
        elif avg_daily_growth > 0.5:
            assessment = "MODERATE data growth - plan for capacity"
        elif avg_daily_growth > 0:
            assessment = "HEALTHY data growth rate"
        else:
            assessment = "NEGATIVE growth - investigate data retention or deletion"
        
        print(f"   Assessment: {assessment}")
    
    print(f"{'='*90}")
    print("NOTE: This analysis tracks primary data growth only (no replica overhead)")

# =============================================================================
#                               MAIN EXECUTION
# =============================================================================

def main():
    """
    Main execution function - coordinates the entire primary data tracking workflow.
    """
    print("#############################################################################")
    print("#                    Elasticsearch Index Size Tracker                      #")
    print("#                         (Primary Storage Analysis)                       #")
    print("#############################################################################")
    
    try:
        # Initialize tracker
        tracker = ElasticsearchSizeTracker(ES_CLOUD_URL, API_KEY)
        
        # Run the main tracking process for primary storage
        # Set show_zero_sizes=True if you want to see all indices including zero-sized ones
        tracker.run(show_zero_sizes=False)
        
        # Save and display primary data growth analysis
        save_growth_analysis(OUTPUT_FILE, GROWTH_FILE)
        display_growth_analysis(GROWTH_FILE)
        
        # Display output file information
        print(f"\n{'='*60}")
        print(f"OUTPUT FILES CREATED:")
        print(f"   Primary sizes: {OUTPUT_FILE}")
        print(f"   Growth analysis: {GROWTH_FILE}")
        print(f"{'='*60}")
        
    except KeyboardInterrupt:
        print("\nWARNING: Process interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"ERROR: Unexpected error occurred: {e}")
        sys.exit(1)

def display_setup_instructions():
    """
    Display setup instructions for daily automation.
    """
    print(f"\n{'='*70}")
    print(f"DAILY AUTOMATION SETUP:")
    print(f"{'='*70}")
    print("To run this script daily, choose one of these options:")
    print()
    print("1. Cron Job (Linux/Mac):")
    print(f"   crontab -e")
    print(f"   0 9 * * * /usr/bin/python3 {os.path.abspath(__file__)}")
    print()
    print("2. Windows Task Scheduler:")
    print("   - Open Task Scheduler")
    print("   - Create Basic Task")
    print(f"   - Set to run: python3 {os.path.abspath(__file__)}")
    print()
    print("3. Cloud Functions:")
    print("   - AWS Lambda with EventBridge")
    print("   - Google Cloud Functions with Cloud Scheduler")
    print("   - Azure Functions with Timer Trigger")
    print(f"{'='*70}")

if __name__ == "__main__":
    # Run main tracking process
    main()
    
    # Show setup instructions
    display_setup_instructions()
    
    print("\nElasticsearch tracking completed successfully!")
