# Nyaya-Shield (Legal Bot)

Nyaya-Shield is a legal Q&A chatbot. It uses a TF‑IDF similarity model trained on combined legal datasets, with optional LLM enhancements. This README explains how to set up, combine datasets, train the model, and run the app.

## Requirements
- Windows 10/11
- Python 3.9–3.11
- Virtual environment (recommended)

## Quick Start
1) Create and activate venv
```cmd
python -m venv venv
venv\Scripts\activate
```

2) Install backend dependencies
```cmd
cd Nyaya-Shield\backend
pip install --upgrade pip
pip install -r requirements.txt
```

3) (Optional) Disable LLM if you don’t want Torch/Hugging Face
```cmd
set ENABLE_LLM=false
```

## Prepare Dataset
Combine the provided datasets into a single CSV.
```cmd
cd ..\datasets
python combine_datasets.py
```
Outputs:
- combined_legal_dataset.csv
- train_dataset.csv
- validation_dataset.csv

## Train the Model
Train TF‑IDF model using the combined dataset. This creates artifacts used by the bot.
```cmd
cd ..\backend
python -m bot.train_model
```
Artifacts generated in `backend/bot/`:
- chatbot_model.pkl
- vectorizer.pkl

## Run the Web App
Start Flask server and chat via the UI.
```cmd
cd Nyaya-Shield\backend
python app.py
```
Open the printed URL in your browser and ask queries (IPC, divorce, consumer, property, etc.).

## Terminal Chat (CLI)
Run the interactive terminal client.
```cmd
cd Nyaya-Shield\backend
python -m bot.terminal_chat
```

## Optional: LLM (CPU‑only)
If you want LLM features without a GPU, install CPU wheels and compatible libs.
```cmd
pip install torch==2.0.1+cpu torchvision==0.15.2+cpu torchaudio==2.0.2 --index-url https://download.pytorch.org/whl/cpu
pip install transformers==4.30.2 sentence-transformers==2.2.2 "huggingface_hub==0.14.1"
```
Then run the app normally. To disable LLM at any time:
```cmd
set ENABLE_LLM=false
```

## Troubleshooting
- ModuleNotFoundError (relative imports):
  - Run modules from `backend` using `python -m bot.<module>`.
  - Scripts have fallbacks and also work as `python bot\<file>.py`.
- Model not found / generic replies:
  - Ensure training completed and `backend/bot/chatbot_model.pkl` exists.
  - Re-run: `python -m bot.train_model`.
- LLM import errors (torch/huggingface):
  - Disable LLM via `set ENABLE_LLM=false`, or install CPU torch and compatible huggingface_hub.

## Project Structure (key parts)
```
Nyaya-Shield/
  backend/
    app.py                 # Flask server
    bot/
      train_model.py       # Train TF‑IDF model
      bot_controller.py    # Loads model, similarity search, detailed responses
      nlp_service.py       # NLP utilities, enhanced responses
      terminal_chat.py     # CLI chat client
      chatbot_model.pkl    # Trained model (generated)
      vectorizer.pkl       # Trained vectorizer (generated)
  datasets/
    combine_datasets.py    # Merges multiple datasets into one CSV
    combined_legal_dataset.csv
    train_dataset.csv
    validation_dataset.csv
  docs/
    README.md
```

## API (brief)
- POST `/api/chat` with JSON `{ "message": "..." }` returns a structured response with answer, confidence, category, and suggestions.

## Notes
- Always run commands from the indicated folder (especially `backend` for modules).
- Dataset quality strongly affects answer quality. Expand/clean datasets for best results.
