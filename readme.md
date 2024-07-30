# Python MT5 Bot Setup Guide

## Requirements
- **Python Installation**: Install Python (recommended version: 3.11 or higher). During installation, ensure Python can be referenced using the command `python` (not `python3`).

## Installation Steps

1. **Install Python**:
    - Download and install Python from the official website.
    - Ensure the installation adds Python to your system PATH.
    - Verify the installation by opening a terminal and typing `python`. The Python interpreter should start.

2. **Extract Bot Files**:
    - Right-click on `pymt5bot-1.0.tar.gz` and select "Extract Here" using WinRAR.
    - Ensure the extracted folder structure is `pymt5bot-1.0/` with the necessary files inside it.

3. **Configure the Bot**:
    - Navigate to `pymt5bot/configs`.
    - Fill in your login details and update `config.json` with your desired parameters. The bot supports timeframes m1, m5, m15, and h1.

## Running the Bot

1. **Execute the Bot**:
    - Run the bot by executing the provided script. This will install the necessary libraries (`metatrader`, `pandas`, `ta`) and start the MT5 terminal.

2. **Operation**:
    - Keep both the Windows terminal and MetaTrader 5 terminal open to ensure the bot functions correctly.
    - The bot will perform operations based on the selected timeframe (e.g., calculating RSI every minute for M1).

3. **Monitoring and Stopping**:
    - Monitor the bot's logs via `output.log`, preferably using an editor like Notepad++ that supports real-time updates.
    - To stop the bot, press `CTRL+C` in the Windows terminal and confirm with `Y` + Enter.

## Additional Information
- For advanced modifications, consider using an IDE like IntelliJ.
- Feel free to ask for further assistance if you need to customize the bot beyond the provided configurations.

