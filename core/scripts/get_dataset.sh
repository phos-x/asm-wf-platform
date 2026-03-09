#!/bin/bash

set -euo pipefail

pip install yq

# Script to download datasets from registry/datasets.yaml
# Downloads to datasets/raw and handles zip/tar extraction

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(pwd)"
readonly CONFIG_FILE="${PROJECT_ROOT}/core/registry/datasets.yaml"
readonly RAW_DIR="${PROJECT_ROOT}/core/datasets/raw"

# Validate dependencies (Added jq, as Python yq requires it under the hood)
check_dependencies() {
    local deps=("curl" "yq" "jq")
    for cmd in "${deps[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            echo "Error: $cmd is required but not installed." >&2
            exit 1
        fi
    done
}

setup_directories() {
    mkdir -p "$RAW_DIR"
}

download_dataset() {
    local dataset_name="$1"
    local download_link="$2"
    local dataset_dir="${RAW_DIR}/${dataset_name}"
    
    mkdir -p "$dataset_dir"
    
    echo "Downloading ${dataset_name}..."
    
    if [[ "$download_link" == *.tar.gz ]] || [[ "$download_link" == *.tar ]]; then
        curl -L "$download_link" | tar -xz -C "$dataset_dir"
        echo "Extracted tar archive to ${dataset_dir}"
    elif [[ "$download_link" == *.zip ]]; then
        local zip_file="${dataset_dir}/${dataset_name}.zip"
        curl -L -o "$zip_file" "$download_link"
        unzip -q "$zip_file" -d "$dataset_dir"
        rm "$zip_file"
        echo "Extracted zip and removed archive"
    else
        curl -L -o "${dataset_dir}/data" "$download_link"
        echo "Downloaded to ${dataset_dir}"
    fi
}

# Main execution
main() {
    check_dependencies
    
    if [[ ! -f "$CONFIG_FILE" ]]; then
        echo "Error: Config file not found at ${CONFIG_FILE}" >&2
        exit 1
    fi
    
    setup_directories
    
    # Parse yaml and iterate datasets using Python yq (jq) syntax
    while IFS= read -r dataset_name; do
        local link
        # FIX 1: Use -r for raw output, add leading dot, and bracket notation
        link=$(yq -r ".datasets[\"${dataset_name}\"].link" "$CONFIG_FILE")
        
        if [[ -z "$link" ]] || [[ "$link" == "null" ]]; then
            echo "Warning: No link found for dataset ${dataset_name}" >&2
            continue
        fi
        
        download_dataset "$dataset_name" "$link"
        
    # FIX 2: Use -r and jq syntax to get the keys
    done < <(yq -r '.datasets | keys[]' "$CONFIG_FILE")
    
    echo "Dataset download complete!"
}

main "$@"