   # Ecommerce Backend

   FastAPI backend for the ecommerce project.

   ## Requirements

   - Python 3.10 or later
   - PowerShell on Windows

   ## Install

   Run these commands from the backend directory:

   ```powershell
   python -m venv env
   .\env\Scripts\activate
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   fastapi dev main.py --reload
   ```

   If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that terminal, then activate the environment again.

   ## Run

   ```powershell
   fastapi dev main.py
   ```

   The API is available at `http://127.0.0.1:8000`. Interactive API documentation is at `http://127.0.0.1:8000/docs`.

   ## Current API

   - `GET /` returns a message confirming that the server is running.
   - The FastAPI application title is `Ecommerece Backend`.
