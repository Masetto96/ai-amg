#!/bin/bash

echo "Looking for Muse device..."
# Run 'muselsl list' and store the output
output=$(muselsl list)

# Check if the output contains "MAC Address"
if [[ $output == *"MAC Address"* ]]; then
    # Extract the MAC address using grep and awk
    mac_address=$(echo "$output" | grep "MAC Address" | awk -F 'MAC Address ' '{print $2}')

    # Run the stream command with the extracted MAC address
    echo "Connecting to device with MAC Address: $mac_address"
    muselsl stream --address "$mac_address"

    echo "Starting python script to connect ableton and stuff"
    python main_neurofeedback.py
else
    echo "No Muse device found. Is your bluetooth on?"
    exit 1
fi
