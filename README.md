# Prompt Engineering Platform

A professional, Streamlit-based platform for creating, testing, versioning, and optimizing prompts for large language models, leveraging DSPy for programmatic optimization.

## 🌟 Features

- **Unified Interface**: A single, professional Streamlit application for all prompt engineering tasks.
- **Prompt Management**: Create, view, and manage the entire lifecycle of your prompts.
- **Interactive Testing**: A chat-based interface to test prompts with custom inputs in real-time.
- **DSPy Optimization**: Use feedback to programmatically optimize prompts for better performance.
- **Versioning & Lineage**: Automatically track prompt versions and view the entire history of a prompt lineage.
- **Configurable Backend**: Easily configure the platform to use different models via environment variables.
- **Training Data Management**: Store and manage training examples for prompt optimization.
- **Error Handling**: Robust error handling and logging for reliable operation.

## 🚀 Quick Start

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Install dependencies:**
    For production, install the core dependencies:
    ```bash
    pip install -r requirements.txt
    ```
    
    For a full development environment, install both sets of requirements:
    ```bash
    pip install -r requirements.txt -r requirements-dev.txt
    ```

3.  **Configure your environment:**
    Create a `.env` file in the root directory and add your API credentials:
    ```env
    # .env
    API_TOKEN="your_perplexity_or_openai_api_key"
    API_BASE_URL="https://api.perplexity.ai" # Or your custom API base
    DEFAULT_MODEL="llama-3-sonar-large-32k-online" # Or another supported model
    DATABASE_URL="sqlite:///prompt_storage.db" # Default SQLite database
    ```
    
    **Supported Models**:
    - `llama-3-sonar-large-32k-online` (Default)
    - `llama-3-sonar-large-32k` (Offline version)
    - `llama-3-sonar-medium-32k`
    - `llama-3-sonar-medium-32k-online`
    - `llama-3-sonar-small-32k`
    - `llama-3-sonar-small-32k-online`
    
    See `prompt_platform/config.py` for all supported models.

4.  **Run the Streamlit application:**
    ```bash
    streamlit run prompt_platform/streamlit_app.py
    ```
    The application will open in your web browser.

## Project Structure

```
prompt_platform/
├── streamlit_app.py     # Main application entrypoint
├── pages/
│   └── 1_Manager.py     # The core prompt management UI
├── api_client.py        # Handles all interactions with the LLM API
├── prompt_generator.py  # Core logic for creating, improving, and optimizing prompts
├── database.py          # SQLAlchemy-based database layer for persistence
├── version_manager.py   # Manages prompt versioning and lineage
├── config.py            # Loads and validates application configuration
├── schemas.py           # Pydantic schemas for data validation
└── tests/              # Test suite for all components
```

## 📖 How It Works

### Creating Prompts
1. **Initial Prompt Generation**
   - Enter your task description
   - The system generates an initial prompt with proper structure and placeholders
   - Example: "Act as an expert on {task}. Respond to the following: {{input}}"

2. **Prompt Testing**
   - Test prompts with different inputs
   - View real-time responses from the model
   - Collect feedback for optimization

3. **Prompt Optimization**
   - Use DSPy to programmatically optimize prompts
   - Provide feedback on responses
   - Automatically generate improved versions

### Version Control
- Each prompt has a unique `lineage_id`
- Versions are automatically incremented
- Full history is preserved in the database
- Easy rollback to previous versions

### Data Management
- Prompts are stored in a SQLite database
- Training examples are managed as JSON
- Lineage tracking for version history
- Support for multiple models

## 🔧 Customization

### Using Different Models
1. Add the model name to the `SUPPORTED_MODELS` dictionary in `prompt_platform/config.py`
2. Set the `DEFAULT_MODEL` environment variable in your `.env` file
3. Restart the application

### Using Different Database
1. Install the required database driver (e.g., `psycopg2-binary` for PostgreSQL)
2. Set the `DATABASE_URL` environment variable in your `.env` file
3. Example for PostgreSQL:
   ```env
   DATABASE_URL="postgresql://user:password@localhost/prompt_db"
   ```

## 🛠️ Development

### Running Tests
```bash
pytest
```

### Test Coverage
- Database operations
- Prompt generation
- DSPy integration
- API client interactions
- Error handling scenarios

### Code Style
- Follows PEP 8 guidelines
- Type hints for all functions
- Comprehensive docstrings
- Logging for debugging

## 🤝 Contributing

1. Fork the repository
2. Create a new feature branch
3. Commit your changes
4. Submit a pull request

Please ensure your code follows the existing style and includes appropriate tests.

## 📄 License

This project is licensed under the MIT License.

## Support

For support, please open an issue in the repository or contact the maintainers.

---
**Last Updated: June 2025**

## 📖 How It Works

- The main **`streamlit_app.py`** serves as the landing page and provides global actions in the sidebar for creating or improving prompts.
- The **`Manager`** page is where you can see all your prompts, test them in a dialog, trigger optimizations, and view their version history.
- All prompts and their metadata are stored in a local SQLite database (`prompt_storage.db`), making the state persistent across sessions.

## 🔧 Customization

### Using a Different Model
You can use any model supported by the Perplexity API or a compatible OpenAI-style API.
1.  Add the model name to the `SUPPORTED_MODELS` dictionary in `prompt_platform/config.py`.
2.  Set the `DEFAULT_MODEL` environment variable in your `.env` file to your new model's name.

### Using a Different Database
The application uses SQLite by default. To switch to PostgreSQL or another SQLAlchemy-supported database:
1.  Install the required database driver (e.g., `psycopg2-binary` for PostgreSQL).
2.  Set the `DATABASE_URL` environment variable in your `.env` file to your database connection string.

## 🤝 Contributing

1.  Fork the repository.
2.  Create a new feature branch.
3.  Commit your changes.
4.  Submit a pull request.

## 📄 License

This project is licensed under the MIT License.

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Git
- SQLite (or compatible database)
- Text editor or IDE

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-directory>
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment:
Create a `.env` file with your API credentials:
```env
API_TOKEN="your_api_key"
API_BASE_URL="https://api.perplexity.ai"
DEFAULT_MODEL="llama-3-sonar-large-32k-online"
DATABASE_URL="sqlite:///prompt_storage.db"
```

5. Run the application:
```bash
streamlit run prompt_platform/streamlit_app.py
```

## 🛠️ Development

### Running Tests

```bash
pytest --cov=prompt_platform
```

### Code Style

- Follows PEP 8 guidelines
- Type hints for all functions
- Comprehensive docstrings
- Logging for debugging

### Debugging

The application uses Python's logging module. Set the desired log level in your `.env` file:
```env
LOG_LEVEL="DEBUG"  # Options: DEBUG, INFO, WARNING, ERROR
```

## 📝 Documentation

### API Documentation

All API endpoints are documented using docstrings. Use `help()` in Python to view them:
```python
help(prompt_platform.api_client.APIClient)
```

### Database Schema

The database schema is defined in `prompt_platform/database.py`. Key fields include:
- `id`: Unique identifier for each prompt
- `lineage_id`: Tracks prompt versions
- `version`: Version number
- `task`: The task description
- `prompt`: The actual prompt text
- `training_data`: JSON array of training examples
- `created_at`: Timestamp of creation
- `model`: The model used for generation

## Support

For support, please:
1. Check the documentation
2. Search existing issues
3. Open a new issue if needed
4. Include error messages and steps to reproduce

---
**Last Updated: June 2025**
