#!/usr/bin/env python3
"""
Setup and run the complete RAG application
This script will help you install dependencies and run both backend and frontend
"""
import subprocess
import sys
import os
import time

def install_requirements():
    """Install required packages"""
    print("Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install dependencies: {e}")
        return False

def check_ollama():
    """Check if Ollama is running"""
    print("\nChecking Ollama service...")
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✓ Ollama is running")
            return True
        else:
            print("✗ Ollama is not responding properly")
            return False
    except Exception as e:
        print("✗ Ollama is not running or not accessible")
        print("Please start Ollama with: ollama serve")
        print("And pull the model with: ollama pull llama3.2:3b")
        return False

def run_backend():
    """Run the backend server"""
    print("\n" + "="*50)
    print("STARTING BACKEND SERVER")
    print("="*50)
    os.system(f"{sys.executable} run_backend.py")

def main():
    print("RAG Application Setup and Runner")
    print("="*40)
    
    # Install dependencies
    if not install_requirements():
        return
    
    # Check Ollama
    ollama_running = check_ollama()
    if not ollama_running:
        print("\nWARNING: Ollama is not running. The application will not work properly.")
        print("Please:")
        print("1. Install Ollama from https://ollama.ai")
        print("2. Run: ollama serve")
        print("3. Run: ollama pull llama3.2:3b")
        
        choice = input("\nDo you want to continue anyway? (y/n): ")
        if choice.lower() != 'y':
            return
    
    print("\n" + "="*50)
    print("SETUP COMPLETE!")
    print("="*50)
    print("\nTo run the application:")
    print("1. Backend: python run_backend.py")
    print("2. Frontend: python run_frontend.py")
    print("\nOr run backend now? (y/n): ", end="")
    
    choice = input()
    if choice.lower() == 'y':
        run_backend()

if __name__ == "__main__":
    main()