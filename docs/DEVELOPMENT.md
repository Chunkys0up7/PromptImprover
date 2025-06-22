# Development Guide

## Setting Up Local Development Environment

### Database Setup

1. **Local SQLite Database**
   - The application uses SQLite as the default database.
   - Create a `.env` file in the root directory with the following content:
     ```
     DATABASE_URL=sqlite:///./prompt_storage.db
     ```
   - The database will be created automatically when you run the application.
   - You can use SQLite browser tools like DB Browser for SQLite to inspect the database.

2. **Alternative Databases**
   - To use a different database, modify the `DATABASE_URL` in your `.env` file:
     - PostgreSQL: `postgresql://user:password@localhost:5432/prompt_db`
     - MySQL: `mysql://user:password@localhost:3306/prompt_db`

### GitHub Integration Setup

1. **Prerequisites**
   - GitHub account
   - GitHub Personal Access Token (PAT) with `repo` scope
   - Git installed on your system

2. **Configuration**
   - Add the following to your `.env` file:
     ```
     GITHUB_TOKEN=your_github_pat
     GITHUB_REPO_OWNER=your_username
     GITHUB_REPO_NAME=prompt-storage
     ```

3. **Using GitHub Integration**
   - The application provides two ways to store prompts:
     1. Local Database (default)
     2. GitHub Repository (optional)

   - To enable GitHub integration:
     ```python
     from prompt_platform.config import set_github_integration
     
     # Enable GitHub integration
     set_github_integration(True)
     ```

### Development Workflow

1. **Local Development**
   ```bash
   # Install dependencies
   pip install -e .
   
   # Run tests
   pytest tests/
   
   # Run the application
   streamlit run streamlit_app.py
   ```

2. **Database Operations**
   - The database will be automatically created and migrated when you first run the application.
   - To manually run migrations:
     ```bash
     alembic upgrade head
     ```

3. **GitHub Operations**
   - Push prompts to GitHub:
     ```python
     from prompt_platform.version_manager import push_to_github
     
     # Push a specific prompt
     push_to_github(prompt_id)
     
     # Push all prompts
     push_to_github()
     ```

### Best Practices

1. **Database Versioning**
   - Always use database migrations for schema changes.
   - Never modify the database schema directly.

2. **GitHub Integration**
   - Use descriptive commit messages when pushing prompts.
   - Consider using branches for different prompt versions.
   - Regularly sync your local database with GitHub.

3. **Security**
   - Never commit your `.env` file to version control.
   - Use environment variables for sensitive information.
   - Rotate your GitHub tokens periodically.

### Troubleshooting

1. **Database Issues**
   - If you encounter database connection issues, check:
     - Database URL in `.env`
     - Database file permissions
     - Database existence

2. **GitHub Integration Issues**
   - If GitHub operations fail, check:
     - GitHub token validity
     - Repository permissions
     - Network connectivity

### Example Usage

```python
from prompt_platform.prompt_generator import PromptGenerator
from prompt_platform.database import db
from prompt_platform.version_manager import push_to_github

# Initialize components
prompt_generator = PromptGenerator()

# Generate a new prompt
new_prompt = await prompt_generator.generate_initial_prompt("Create a summary prompt")

# Save to local database
await db.save_prompt(new_prompt)

# Push to GitHub (if configured)
push_to_github(new_prompt["id"])
```
