# This script will:
1. Fetch Clinical Trials of selected indication from in-house database (MongoDB) 
2. score and give weight to each trials based on it's current status, phase, number of facility, type of intervention, etc.

This project is expected to identify the up-coming intervention on the market in selected indication. 

Usage:
$ python Select_CT.py "selected_indication"