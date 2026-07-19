# Kithula Backend API

A robust backend REST API built with FastAPI and PostgreSQL, featuring secure JWT authentication, relational data persistence, and AWS S3 cloud storage integration.

---

## Prerequisites

Before starting, ensure you have the following installed on your machine:
* Python 3.12+
* PostgreSQL Server
* Git

---

## Getting Started

Follow these step-by-step instructions to set up your local development environment.

### 1. Repository Setup
Clone the project repository to your local machine and navigate into the project root directory:
```powershell
git clone <repository-url>
cd kithula-backend
2. Virtual Environment Configuration
Create and activate a isolated Python virtual environment (.venv) to manage the project dependencies securely.

On Windows (PowerShell):

PowerShell
# Create the virtual environment
python -m venv .venv

# Activate the virtual environment
.\.venv\Scripts\Activate.ps1
On Linux / macOS:

Bash
# Create the virtual environment
python3 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate
Note: Once activated, your terminal prompt will display (.venv).

3. Dependencies Installation
Upgrade package managers and install all required modules including email-validator and uvicorn:

PowerShell
pip install --upgrade pip
pip install -r requirements.txt
Environment Variables Configuration
The application requires an environment file to manage secrets and connections securely.

Create a file named .env in the root directory of your project (D:\CClarke\kithula-backend\.env).

Copy and paste the configuration block below into the file:

Code snippet
# DB_CONNECTION
DB_CONNECTION=postgresql
POSTGRES_DB=kithula
POSTGRES_USERNAME=postgres
POSTGRES_PASSWORD=your_postgres_password_here
DB_HOST=127.0.0.1
DB_PORT=5432

# AWS_CONNECTION
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here
AWS_BUCKET_NAME=your aws bucket name
AWS_REGION=eu-north-1

# JWT_SECRETKEY
SECRET_KEY=your_generated_jwt_secret_key_here
💡 Tip: Replace the placeholder text (e.g., your_postgres_password_here) with your actual local system credentials. Keep the .env file excluded from your Git commits for security.

Running the Application
With your virtual environment active and your .env configured, fire up the Uvicorn development server with hot-reloading:

PowerShell
uvicorn app.main:app --reload
The API documentation will be available at:

Interactive Swagger UI: http://127.0.0.1:8000/docs

Alternative ReDoc UI: http://127.0.0.1:8000/redoc

Project Authorship
Author Initial: AK
