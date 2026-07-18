# Contributing to PQ-Oracle

Thank you for your interest in contributing to `PQ-Oracle`!

## How to Set Up Development Environment

1. Clone the repository:
   ```bash
   git clone https://github.com/ahmed-el5hatib/PQ-Oracle.git
   cd PQ-Oracle
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the full benchmark pipeline:
   ```bash
   python run_all.py
   ```

## Guidelines for Contributions
- Keep algorithm naming consistent (`ML-DSA-44`, `Falcon-512`, `SLH-DSA-SHA2-128s`).
- Ensure all CSV and PNG outputs are refreshed by running `python run_all.py` before opening a pull request.
- Ensure Solidity contracts adhere to the Checks-Effects-Interactions pattern and include access controls.
