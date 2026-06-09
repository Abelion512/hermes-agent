#!/bin/bash
# Linux dependency management for Hermes CLI

set -e

DISTRO=$(grep '^ID=' /etc/os-release 2>/dev/null | cut -d= -f2 | tr -d '"')

install_common_tools() {
    echo "Installing common development tools..."
    case "$DISTRO" in
        ubuntu|debian)
            apt-get update -qq
            apt-get install -y -qq git curl wget build-essential python3-dev
            ;;
        fedora|centos|rhel)
            dnf install -y git curl wget gcc python3-devel
            ;;
        arch|manjaro)
            pacman -S --noconfirm git curl wget base-devel
            ;;
        *)
            echo "Unsupported distribution: $DISTRO"
            exit 1
            ;;
    esac
}

install_clipboard_tools() {
    echo "Installing clipboard tools..."
    case "$DISTRO" in
        ubuntu|debian)
            apt-get install -y -qq xclip xsel wl-clipboard 2>/dev/null || true
            ;;
        fedora|centos|rhel)
            dnf install -y xclip xsel wl-clipboard 2>/dev/null || true
            ;;
        arch|manjaro)
            pacman -S --noconfirm xclip xsel wl-clipboard 2>/dev/null || true
            ;;
    esac
}

install_browser_deps() {
    echo "Installing browser dependencies..."
    case "$DISTRO" in
        ubuntu|debian)
            apt-get install -y -qq chromium-browser || apt-get install -y -qq chromium 2>/dev/null || true
            ;;
        fedora)
            dnf install -y chromium 2>/dev/null || true
            ;;
        arch|manjaro)
            pacman -S --noconfirm chromium 2>/dev/null || true
            ;;
    esac
}

check_python() {
    if ! command -v python3 &> /dev/null; then
        echo "Python 3 not found. Installing..."
        case "$DISTRO" in
            ubuntu|debian)
                apt-get install -y python3 python3-pip python3-venv
                ;;
            fedora|centos|rhel)
                dnf install -y python3 python3-pip
                ;;
            arch|manjaro)
                pacman -S --noconfirm python python-pip
                ;;
        esac
    fi
    python3 --version
}

setup_uv() {
    if ! command -v uv &> /dev/null; then
        echo "Installing uv package manager..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
    fi
    uv --version
}

case "${1:-all}" in
    common)
        install_common_tools
        ;;
    clipboard)
        install_clipboard_tools
        ;;
    browser)
        install_browser_deps
        ;;
    python)
        check_python
        ;;
    uv)
        setup_uv
        ;;
    all)
        install_common_tools
        install_clipboard_tools
        check_python
        setup_uv
        echo "All dependencies installed successfully!"
        ;;
    *)
        echo "Usage: $0 {common|clipboard|browser|python|uv|all}"
        exit 1
        ;;
esac
