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

   ## Run with Docker

   Run these commands from the backend directory. The environment file is passed
   to the container at runtime; do not copy it into the image.

   ```powershell
   docker build -t ecommerce-api:1.0 .
   docker run --name ecommerce-api --env-file .env.docker -p 8000:8000 ecommerce-api:1.0
   ```

   Ensure `.env.docker` defines `DB_CONNECTION`, `SECRET_KEY`, `ALGORITHM`, `EXP_TIME`,
   and `REFRESH_EXP_TIME`. If PostgreSQL runs on the Windows host, use
   `host.docker.internal` as the database hostname in `DB_CONNECTION` instead
   of `localhost`. In Docker CLI env files, write values without surrounding
   quotes; the quote characters can become part of the environment variable.

   ## Development sample data

   Each service has a `seed_data.json` fixture in its `src/<service>/` folder.
   To insert the related sample records into the database configured by
   `DB_CONNECTION`, run this from the backend directory in PowerShell:

   ```powershell
   $env:APP_ENV = "development"
   python -m scripts.seed_demo_data
   ```

   The command is blocked unless `APP_ENV=development`. It inserts missing
   records without deleting existing data, so it can be run again safely.
   The sample catalog uses remote Unsplash image URLs. Demo customer and admin
   logins are `demo.customer@example.com` and `demo.admin@example.com`; both
   use the password `DemoPass123!`. These accounts and credentials are for
   development/test environments only.

   ## Current API

   - `GET /` returns a message confirming that the server is running.
   - The FastAPI application title is `Ecommerece Backend`.
