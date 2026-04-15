# Setup Instructions

Follow these steps to get the Data Pipeline Agent up and running.

## Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Virtual environment tool (venv or conda)
- Anthropic API key

## Step-by-Step Installation

### 1. Clone or Download the Project

```bash
cd datapipeline-aiagent
```

### 2. Create Virtual Environment

**Using venv (recommended):**
```bash
python -m venv venv

# On Linux/Mac:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

**Using conda:**
```bash
conda create -n pipeline-agent python=3.9
conda activate pipeline-agent
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install all required packages including:
- LangGraph for agent orchestration
- LangChain for LLM integration
- Anthropic SDK for Claude API
- Data processing libraries (pandas, numpy)
- Validation tools (pydantic, great-expectations)
- And more...

### 4. Configure Environment Variables

```bash
# Create your .env file

# Edit the .env file with your settings
nano .env  # or use your preferred editor
```

**Required settings:**
```bash
ANTHROPIC_API_KEY=sk-ant-xxxxx  # Get from https://console.anthropic.com
```

**Optional settings:**
```bash
# Database connections (if needed)
POSTGRESQL_HOST=localhost
POSTGRESQL_PORT=5432
POSTGRESQL_DATABASE=your_db
POSTGRESQL_USERNAME=your_user
POSTGRESQL_PASSWORD=your_password

# Cloud storage (if needed)
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
```

### 5. Verify Installation

```bash
# Run tests to verify everything is working
pytest tests/ -v

# Check the CLI help
python main.py --help
```

### 6. Try the Example

```bash
# Generate a pipeline using the example configuration
python main.py --config examples/ecommerce_pipeline.yaml
```

## Common Issues & Solutions

### Issue: ImportError for langgraph

**Solution:**
```bash
pip install --upgrade langgraph langchain langchain-anthropic
```

### Issue: API Key Not Found

**Solution:**
- Ensure your `.env` file exists and contains `ANTHROPIC_API_KEY`
- Check that the environment variable is loaded: `echo $ANTHROPIC_API_KEY`
- Try setting it directly: `export ANTHROPIC_API_KEY=your_key`

### Issue: Permission Denied on Scripts

**Solution:**
```bash
chmod +x main.py
```

### Issue: Module Not Found Errors

**Solution:**
```bash
# Ensure you're in the project root directory
pwd  # Should show .../datapipeline-aiagent

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

## Directory Structure After Setup

```
datapipeline-aiagent/
├── venv/                     # Virtual environment (created)
├── .env                      # Environment variables (created)
├── src/                      # Source code
├── tests/                    # Test files
├── examples/                 # Example configurations
├── outputs/                  # Generated pipelines (created on first run)
├── logs/                     # Application logs (created on first run)
├── .cache/                   # Cache directory (created on first run)
├── requirements.txt          # Dependencies
├── main.py                   # Entry point
└── README.md                 # Documentation
```

## Next Steps

1. **Read the README**: Understand the architecture and features
2. **Run Examples**: Try the included example configurations
3. **Create Custom Pipeline**: Use interactive mode or create your own YAML
4. **Explore Code**: Check out the agent nodes in `src/agents/`
5. **Run Tests**: Ensure everything works with `pytest tests/`

## Getting Help

- Check the main README.md for detailed documentation
- Review example configurations in `examples/`
- Look at sample outputs to understand what's generated
- Check logs in `logs/pipeline_agent.log` for debugging

## Uninstallation

To remove the project:

```bash
# Deactivate virtual environment
deactivate

# Remove virtual environment
rm -rf venv/

# Remove generated files
rm -rf outputs/ logs/ .cache/

# Remove environment file (optional)
rm .env
```

## System Requirements

- **OS**: Linux, macOS, Windows
- **RAM**: Minimum 4GB, recommended 8GB
- **Disk**: ~500MB for dependencies, varies with usage
- **Network**: Internet connection for API calls

## Security Notes

1. Never commit `.env` file to version control
2. Use environment variables for all credentials
3. Enable dry-run mode initially to test safely
4. Review generated code before executing in production
5. Use resource limits configured in `src/config/settings.py`

## Performance Tips

1. Adjust `MAX_EXECUTION_TIME_SECONDS` in .env for larger pipelines
2. Use batch processing for large datasets
3. Enable caching for repeated operations
4. Monitor logs for performance bottlenecks
5. Tune `temperature` setting for code generation quality

Happy pipeline building! 🚀