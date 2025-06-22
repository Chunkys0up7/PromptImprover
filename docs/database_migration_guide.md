# Database Migration Guide

This guide provides instructions for migrating the Prompt Platform's database from SQLite to a production-grade PostgreSQL instance.

## Why Migrate?

- **Concurrency:** SQLite is a serverless, file-based database that is not suitable for applications with multiple concurrent users, as it can lead to file locking issues. PostgreSQL is a client-server RDBMS designed to handle many simultaneous connections gracefully.
- **Scalability:** PostgreSQL offers superior performance and scalability for larger datasets and higher traffic loads.
- **Features:** It provides a rich set of features, including advanced indexing, connection pooling, and robust backup/recovery options.

## Migration Steps

### 1. Set up PostgreSQL

First, you need a running PostgreSQL server. You can install it locally, use a managed service (like AWS RDS, Google Cloud SQL, or Heroku Postgres), or run it in a Docker container.

**Example using Docker:**
```bash
docker run --name prompt-postgres -e POSTGRES_PASSWORD=mysecretpassword -e POSTGRES_USER=user -e POSTGRES_DB=promptdb -p 5432:5432 -d postgres
```

### 2. Install the Database Driver

The application requires the `psycopg2` driver to connect to PostgreSQL. This is already included in `requirements.txt`. Ensure your environment is up to date:

```bash
pip install -r requirements.txt
```

### 3. Configure the `DATABASE_URL`

The application is configured via the `DATABASE_URL` environment variable. To switch to PostgreSQL, set this variable in your `.env` file or your deployment environment.

The format is: `postgresql://<user>:<password>@<host>:<port>/<dbname>`

**Example for the Docker container above:**
```
DATABASE_URL=postgresql://user:mysecretpassword@localhost:5432/promptdb
```

### 4. Run the Application

When you start the Streamlit application with the new `DATABASE_URL`, the `database.py` module will automatically:
- Detect the `postgresql` scheme.
- Create a new engine with production-ready connection pooling.
- Create all the necessary tables in your PostgreSQL database if they don't already exist.

```bash
streamlit run prompt_platform/streamlit_app.py
```

The application will now be using PostgreSQL as its data store.

**(Optional) Data Migration:**

This guide does not cover migrating existing data from an old SQLite database to the new PostgreSQL database. This typically requires a separate ETL (Extract, Transform, Load) script using tools like `pandas` or a dedicated data migration tool.

## Verifying the Connection

You can verify that the application is connected to PostgreSQL by:
1.  Checking the logs of your PostgreSQL server for connection activity from the new user.
2.  Connecting to your PostgreSQL database with a tool like `psql` or a GUI client (e.g., DBeaver, Postico) and inspecting the `prompts` table after you've created a prompt in the application.

```sql
-- Using psql to connect and check the table
\c prompt_platform_db;
\dt; -- Should list the 'prompts' table
SELECT * FROM prompts LIMIT 5;
```

That's it! Your application is now using PostgreSQL for its data persistence, providing better scalability and reliability for production environments. 