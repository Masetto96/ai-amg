#!/bin/bash
echo "Looking for Muse device ... it takes a few seconds"
# Run 'muselsl list' and store the output
output=$(muselsl list)
# Check if the output contains "MAC Address"
if [[ $output == *"MAC Address"* ]]; then
    # Extract the MAC address using grep and awk
    mac_address=$(echo "$output" | grep "MAC Address" | awk -F 'MAC Address ' '{print $2}')
    echo "Found Muse device with MAC Address: $mac_address"
    
    # Prompt user for confirmation
    read -p "Do you want to connect to this device? (y/n): " confirm
    
    # Check user's response
    if [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]]; then
        echo "Connecting: $mac_address"
        muselsl stream --address "$mac_address"
    else
        echo "Connection cancelled by user."
        exit 0
    fi
else
    echo "No Muse device found. Is your bluetooth on?"
    exit 1
fi