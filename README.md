# AI-Powered Data Pipeline Agent 🤖

A production-ready agentic AI system for building, validating, and deploying end-to-end data pipelines using LangGraph.

## 🎯 Why LangGraph?

**LangGraph was chosen over CrewAI for the following reasons:**

1. **Lightweight & Minimal Dependencies**: LangGraph has fewer dependencies and a smaller footprint
2. **Fine-grained Control**: Explicit state management and control flow with graph-based architecture
3. **Better Observability**: Clear visualization of agent decision paths and state transitions
4. **Production-Ready**: Built-in checkpointing, error recovery, and streaming support
5. **Flexibility**: Easy to customize node behavior and add conditional edges
6. **Type Safety**: Better TypeScript/Python typing support for enterprise applications

## 🏗️ Architecture

```
Pipeline Agent (Supervisor)
    ├── Requirements Analyzer (Understands user needs)
    ├── Schema Designer (Designs data models)
    ├── Pipeline Builder (Generates ETL code)
    ├── Validator (Tests and validates)
    └── Deployment Manager (Prepares for production)
```

## 📁 Folder Structure

```
datapipeline-AIagent/                          # ROOT (32 total files)
│
├── 📄 Documentation (6 files)
│   ├── README.md                             # Main overview
│   ├── PROJECT_SUMMARY.md                    # Quick summary
│   ├── SETUP.md                              # Installation guide
│   ├── ARCHITECTURE.md                       # Technical details
│   ├── SELF_HEALING.md                       # Self-healing guide
│   └── FOLDER_STRUCTURE.md                   # This reference!
│
├── 🐍 Entry Points (2 files)
│   ├── main.py                               # Basic CLI
│   └── main_enhanced.py                      # Self-healing CLI
│
├── 📂 src/ - SOURCE CODE (11 files)
│   ├── agents/                               # AI AGENTS (5 files)
│   │   ├── pipeline_agent.py                 # Main LangGraph agent
│   │   ├── enhanced_agent.py                 # Self-healing wrapper
│   │   ├── self_healing.py                   # Healing & upgrade engines
│   │   └── state.py                          # State management
│   │
│   ├── tools/                                # REUSABLE TOOLS (2 files)
│   │   └── pipeline_tools.py                 # Schema, code gen, validation
│   │
│   ├── utils/                                # UTILITIES (3 files)
│   │   ├── logger.py                         # Structured logging
│   │   └── validators.py                     # Input validation
│   │
│   └── config/                               # CONFIGURATION (2 files)
│       └── settings.py                       # App config & guardrails
│
├── 📂 tests/                                 # UNIT TESTS (2 files)
│   └── test_agents.py                        # Pytest tests
│
├── 📂 examples/                              # EXAMPLES (3 files)
│   ├── ecommerce_pipeline.yaml               # Example config
│   ├── sample_output_*.py                    # Sample generated code
│   └── sample_output_README.md               # Sample docs
│
├── 📂 outputs/                               # GENERATED PIPELINES (runtime)
│   └── [pipeline_name]/
│       ├── [pipeline_name].py                # Generated code
│       ├── [pipeline_name]_README.md         # Generated docs
│       └── versions/                         # Version backups
│
├── 📂 logs/                                  # LOGS (runtime)
│   └── pipeline_agent.log                    # Application logs
│
└── ⚙️ Config Files (4 files)
    ├── requirements.txt                      # Python dependencies
    ├── .env.example                          # Environment template
    └── .gitignore                            # Git ignore
    
```

## 🚀 Quick Start

### 1. Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Set Environment Variables

```bash
# Create .env file
cp .env.example .env

# Add your API keys
ANTHROPIC_API_KEY=your_api_key_here
```

### 3. Run the Agent

```bash
# Basic usage
python main.py

# With custom configuration
python main.py --config examples/ecommerce_pipeline.yaml

# Interactive mode
python main.py --interactive
```

## 💡 Features

### Core Capabilities
- ✅ **Automated Pipeline Design**: AI-driven schema and architecture design
- ✅ **Multi-Source Support**: SQL, NoSQL, APIs, Files (CSV, JSON, Parquet)
- ✅ **Transform Logic**: Custom transformations, aggregations, joins
- ✅ **Data Quality**: Built-in validation, profiling, and anomaly detection
- ✅ **Error Handling**: Retry logic, dead letter queues, alerting
- ✅ **Monitoring**: Logging, metrics, and observability

### Production Features
- 🔒 **Security**: Credential management, encryption, access control
- 📊 **Scalability**: Batch processing, parallel execution, streaming
- 🔄 **Idempotency**: Deduplication and checkpointing
- 📝 **Documentation**: Auto-generated docs and data lineage
- 🧪 **Testing**: Unit tests, integration tests, data quality tests

## 📖 Usage Examples

### Example 1: E-commerce Analytics Pipeline

```python
from src.agents.pipeline_agent import DataPipelineAgent

# Initialize agent
agent = DataPipelineAgent()

# Define requirements
requirements = {
    "name": "ecommerce_analytics",
    "description": "Daily sales and inventory analytics",
    "sources": [
        {
            "type": "postgresql",
            "name": "transactional_db",
            "tables": ["orders", "customers", "products"]
        },
        {
            "type": "s3",
            "name": "clickstream_data",
            "format": "parquet"
        }
    ],
    "transformations": [
        "Calculate daily revenue by product category",
        "Aggregate customer lifetime value",
        "Identify trending products"
    ],
    "destination": {
        "type": "snowflake",
        "schema": "analytics"
    },
    "schedule": "daily at 2am UTC"
}

# Generate pipeline
result = agent.build_pipeline(requirements)
print(f"Pipeline created: {result['output_path']}")
```

### Example 2: Real-time Fraud Detection

```python
requirements = {
    "name": "fraud_detection",
    "description": "Real-time transaction monitoring",
    "sources": [
        {
            "type": "kafka",
            "topic": "transactions",
            "format": "json"
        }
    ],
    "transformations": [
        "Calculate transaction velocity per user",
        "Check against blacklist",
        "Score fraud probability using ML model"
    ],
    "destination": {
        "type": "redis",
        "stream": "fraud_alerts"
    },
    "mode": "streaming"
}

result = agent.build_pipeline(requirements)
```

## 🛡️ Guardrails & Safety

The agent includes multiple safety mechanisms:

1. **Input Validation**: Validates all configuration before processing
2. **Resource Limits**: Prevents excessive memory/CPU usage
3. **Rate Limiting**: Controls API calls and external requests
4. **Code Review**: AI reviews generated code for security issues
5. **Dry Run Mode**: Test without executing actual operations
6. **Rollback Support**: Automated rollback on failures

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test suite
pytest tests/test_agents.py -v
```

## 📊 Monitoring

View logs and metrics:

```bash
# Tail logs
tail -f logs/pipeline_agent.log

# View generated pipelines
ls -la outputs/
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

- Documentation: [docs/](docs/)
- Issues: GitHub Issues
- Discussions: GitHub Discussions

## 🔄 Changelog

### v1.0.0 (2024-04-15)
- Initial release
- LangGraph-based architecture
- Support for SQL, NoSQL, and file sources
- Production-ready guardrails and monitoring