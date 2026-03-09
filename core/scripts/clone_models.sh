#!/bin/bash

set -euo pipefail

# ============================================================================
# clone_models.sh - Clone and setup model repositories
# ============================================================================
# Usage: ./clone_models.sh [root_directory]
# ============================================================================

# Configuration
readonly ROOT_DIR="${1:-.}"
readonly CONFIG_FILE="config/models.yaml"
readonly COLORS_GREEN='\033[0;32m'
readonly COLORS_CYAN='\033[0;36m'
readonly COLORS_RED='\033[0;31m'
readonly COLORS_NC='\033[0m'  # No Color


PROJECT_ROOT="" #project root is defined in main()

# ============================================================================
# Logging Functions
# ============================================================================

log_info() {
    echo -e "${COLORS_CYAN}[INFO]${COLORS_NC} $*"
}

log_success() {
    echo -e "${COLORS_GREEN}[SUCCESS]${COLORS_NC} $*"
}

log_error() {
    echo -e "${COLORS_RED}[ERROR]${COLORS_NC} $*" >&2
}

# ============================================================================
# Utility Functions
# ============================================================================

safe_mkdir() {
    local path="$1"
    if [[ ! -d "$path" ]]; then
        mkdir -p "$path" || {
            log_error "Failed to create directory: $path"
            return 1
        }
    fi
}

verify_file_exists() {
    local file="$1"
    local description="$2"
    if [[ ! -f "$file" ]]; then
        log_error "$description not found: $file"
        return 1
    fi
}

# ============================================================================
# Model Processing
# ============================================================================

process_model() {
    local model_key="$1"
    local repo="$2"
    local branch="$3"
    local target_dir="$4"
    local train_script="$5"
    local infer_script="$6"
    local config_path="$7"
    local run_setup="$8"
    shift 8
    local setup_commands=("$@")

    log_info "Processing model '$model_key' from $repo (branch: $branch)"
    
    # Validation
    if [[ -z "$repo" || -z "$branch" || -z "$target_dir" ]]; then
        log_error "Missing required fields for model '$model_key'"
        return 1
    fi

    local full_target_dir="${PROJECT_ROOT}/${target_dir}"
    local full_train_path="${full_target_dir}/${train_script}"
    local full_infer_path="${full_target_dir}/${infer_script}"
    local full_config_path="${full_target_dir}/${config_path}"

    # Clone or update repository
    if [[ ! -d "${full_target_dir}/.git" ]]; then
        log_info "   Cloning into $full_target_dir..."
        
        # FIX: Create parent directory, not the target dir, to avoid git clone failure
        safe_mkdir "$(dirname "$full_target_dir")" || return 1
        
        git clone -b "$branch" "$repo" "$full_target_dir" || {
            log_error "Failed to clone repository: $repo"
            return 1
        }
    else
        log_info "   Repository exists, updating branch '$branch'..."
        (
            cd "$full_target_dir" || exit 1
            git fetch origin || { log_error "Failed to fetch from origin"; exit 1; }
            git checkout "$branch" || { log_error "Failed to checkout branch: $branch"; exit 1; }
            git pull origin "$branch" || { log_error "Failed to pull from origin/$branch"; exit 1; }
        ) || return 1
    fi

    # Verify required files (Optional: disable if files are expected to be generated during setup)
    if [[ -n "$train_script" ]]; then verify_file_exists "$full_train_path" "Train script" || return 1; fi
    if [[ -n "$infer_script" ]]; then verify_file_exists "$full_infer_path" "Infer script" || return 1; fi
    if [[ -n "$config_path" ]]; then verify_file_exists "$full_config_path" "Config file" || return 1; fi

    # Run setup if enabled
    if [[ "$run_setup" == "true" && ${#setup_commands[@]} -gt 0 ]]; then
        log_info "   Running setup commands for '$model_key'..."
        (
            cd "$full_target_dir" || exit 1
            for cmd in "${setup_commands[@]}"; do
                log_info "     > $cmd"
                bash -c "$cmd" || { log_error "Setup command failed: $cmd"; exit 1; }
            done
        ) || return 1
    else
        log_info "   Setup skipped for '$model_key'."
    fi

    log_success "Model '$model_key' processed successfully"
}

# ============================================================================
# YAML Parsing
# ============================================================================

# ============================================================================
# YAML Parsing
# ============================================================================

parse_yaml() {
    local yaml_file="$1"
    local model_key="" repo="" branch="" target_dir="" train_script="" infer_script="" config_path="" run_setup="false"
    local setup_commands=()
    local in_setup=false

    # Read line by line, allowing for files with no trailing newline
    while IFS= read -r line || [[ -n "$line" ]]; do
        
        # Strip carriage returns
        line="${line//[$'\r']/}"
        
        # Skip empty lines, comments, AND the root "models:" key
        [[ -z "${line// /}" || "$line" =~ ^[[:space:]]*# || "$line" =~ ^models:[[:space:]]*$ ]] && continue

        # 1. Extract model key (nested under models: -> exactly 2 spaces indentation)
        if [[ "$line" =~ ^[[:space:]]{2}([a-zA-Z_][a-zA-Z0-9_]*):[[:space:]]*$ ]]; then
            # Process previous model if exists
            if [[ -n "$model_key" ]]; then
                process_model "$model_key" "$repo" "$branch" "$target_dir" "$train_script" "$infer_script" "$config_path" "$run_setup" "${setup_commands[@]:-}"
            fi
            
            # Reset variables for new model
            model_key="${BASH_REMATCH[1]}"
            repo="" branch="" target_dir="" train_script="" infer_script="" config_path="" run_setup="false"
            setup_commands=()
            in_setup=false
            continue
        fi

        # 2. Extract list items (setup commands, indented 4+ spaces with a '-')
        if [[ "$line" =~ ^[[:space:]]{4,}-[[:space:]]+(.*)$ ]]; then
            if [[ "$in_setup" == true ]]; then
                local cmd="${BASH_REMATCH[1]}"
                # Strip quotes
                cmd="${cmd%\"}"; cmd="${cmd#\"}"
                cmd="${cmd%\'}"; cmd="${cmd#\'}"
                setup_commands+=("$cmd")
            fi
            continue
        fi

        # 3. Extract standard properties (indented 4+ spaces)
        if [[ "$line" =~ ^[[:space:]]{4,}([a-zA-Z_][a-zA-Z0-9_]*):[[:space:]]*(.*)$ ]]; then
            local key="${BASH_REMATCH[1]}"
            local value="${BASH_REMATCH[2]}"
            
            # Trim quotes
            value="${value%\"}"; value="${value#\"}"
            value="${value%\'}"; value="${value#\'}"
            
            if [[ "$key" == "setup" ]]; then
                in_setup=true
            else
                in_setup=false # turn off setup reading
                case "$key" in
                    repo)         repo="$value" ;;
                    branch)       branch="$value" ;;
                    target_dir)   target_dir="$value" ;;
                    train_script) train_script="$value" ;;
                    infer_script) infer_script="$value" ;;
                    config_path)  config_path="$value" ;;
                    run_setup)    run_setup="$value" ;;
                esac
            fi
        fi
    done < "$yaml_file"

    # Process the final model left in the buffer
    if [[ -n "$model_key" ]]; then
        process_model "$model_key" "$repo" "$branch" "$target_dir" "$train_script" "$infer_script" "$config_path" "$run_setup" "${setup_commands[@]:-}"
    fi
}

# ============================================================================
# Main
# ============================================================================

main() {
    PROJECT_ROOT="$(cd "${ROOT_DIR}/core" && pwd)" || {
        log_error "Invalid root directory: $ROOT_DIR"
        exit 1
    }

    local config_path="${PROJECT_ROOT}/${CONFIG_FILE}"

    if [[ ! -f "$config_path" ]]; then
        log_error "Config file not found: $config_path"
        exit 1
    fi

    log_info "Starting model cloning process..."
    parse_yaml "$config_path"
    log_success "Model cloning process completed"
}

main "$@"