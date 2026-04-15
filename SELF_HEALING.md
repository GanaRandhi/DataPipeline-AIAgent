# Self-Healing and Auto-Upgrade Features 🔄

## Overview

The Data Pipeline Agent now includes advanced **self-healing** and **auto-upgrade** capabilities that enable it to:

1. **Automatically recover from failures** without human intervention
2. **Incrementally upgrade pipelines** to improve performance and reliability
3. **Learn from past failures** to prevent future issues
4. **Maintain version history** with rollback capabilities

## Why Self-Healing?

### The Problem
Traditional data pipelines fail for various reasons:
- Connection timeouts
- Memory errors
- Schema changes
- Rate limiting
- Authentication expiration
- Deadlocks

**Manual intervention is slow, expensive, and error-prone.**

### The Solution
Our self-healing system:
✅ Detects failures automatically  
✅ Identifies error patterns  
✅ Applies appropriate recovery strategies  
✅ Learns from successful recoveries  
✅ Prevents recurring issues  

## Features

### 1. Automatic Error Recovery

The agent can automatically recover from common failure scenarios:

| Error Type | Recovery Strategy |
|------------|------------------|
| **Connection Timeout** | Exponential backoff retry (2s → 4s → 8s) |
| **Memory Error** | Reduce batch size by 50% |
| **Rate Limit** | Wait and retry with reduced frequency |
| **Data Quality** | Apply automatic cleaning and null handling |
| **Schema Mismatch** | Attempt automatic schema reconciliation |
| **Deadlock** | Retry with randomized delay |
| **Authentication** | Refresh credentials (if configured) |
| **Disk Full** | Clean temporary files and caches |

### 2. Incremental Upgrades

The system identifies and applies non-breaking improvements:

**Upgrade Types:**
- 🚀 **Performance**: Parallel processing, caching, connection pooling
- 🔒 **Security**: Environment variables, credential encryption, access control
- 🐛 **Bug Fix**: Error handling, validation, edge cases
- ✨ **Feature**: Logging, monitoring, documentation
- 📊 **Schema**: Idempotent operations, versioning

**Each upgrade includes:**
- Estimated improvement percentage
- Risk level assessment
- Rollback plan
- Validation before deployment

### 3. Health Monitoring

Continuous monitoring tracks:
- Success rate (%)
- Average execution time
- Error frequency
- Memory usage
- CPU utilization
- Consecutive failures

**Health Status Levels:**
- 🟢 **Healthy**: No issues
- 🟡 **Degraded**: Minor issues
- 🟠 **Failing**: Significant problems
- 🔴 **Critical**: Multiple consecutive failures

### 4. Version Management

Full version control with semantic versioning:
- **Major** (1.0.0 → 2.0.0): Breaking changes, schema updates
- **Minor** (1.1.0 → 1.2.0): New features, performance improvements
- **Patch** (1.1.1 → 1.1.2): Bug fixes

## Usage

### Basic Usage with Self-Healing

```bash
# Build pipeline with self-healing enabled
python main_enhanced.py --config examples/ecommerce_pipeline.yaml --enable-healing

# Build with both self-healing and auto-upgrades
python main_enhanced.py --config examples/ecommerce_pipeline.yaml --enable-healing --enable-upgrades
```

### Apply Upgrades

```bash
# Apply performance upgrade (dry run first)
python main_enhanced.py --upgrade ecommerce_analytics --type performance --dry-run

# Apply security upgrade (for real)
python main_enhanced.py --upgrade ecommerce_analytics --type security

# Apply bug fix upgrade
python main_enhanced.py --upgrade ecommerce_analytics --type bug_fix
```

### Rollback

```bash
# Rollback to previous version
python main_enhanced.py --rollback ecommerce_analytics

# Rollback to specific version
python main_enhanced.py --rollback ecommerce_analytics --version 1.2.0
```

### View History

```bash
# View upgrade and health history
python main_enhanced.py --history ecommerce_analytics
```

## Python API

### Using Self-Healing in Code

```python
from src.agents.enhanced_agent import SelfHealingPipelineAgent

# Initialize with self-healing enabled
agent = SelfHealingPipelineAgent(
    enable_self_healing=True,
    enable_auto_upgrade=True
)

# Build pipeline (will auto-heal on failures)
requirements = {
    "name": "my_pipeline",
    "description": "My data pipeline",
    # ... other configuration
}

result = agent.build_pipeline(requirements, max_healing_attempts=3)

# Check result
if result["status"] == "completed":
    print(f"Pipeline created: {result['output_path']}")
    print(f"Health: {result['health_status']}")
    
    # View suggested upgrades
    for upgrade in result.get("suggested_upgrades", []):
        print(f"- {upgrade['type']}: {upgrade['description']}")
```

### Manual Healing

```python
from src.agents.self_healing import SelfHealingEngine

# Create healing engine
healing_engine = SelfHealingEngine()

# Attempt to heal from specific error
success, action = healing_engine.attempt_self_heal(
    pipeline_name="my_pipeline",
    error="Connection timeout after 30s",
    context={"retry_count": 1}
)

if success:
    print(f"Healing action: {action}")
```

### Apply Upgrades Programmatically

```python
from src.agents.enhanced_agent import SelfHealingPipelineAgent

agent = SelfHealingPipelineAgent()

# Apply performance upgrade
result = agent.apply_upgrade(
    pipeline_name="my_pipeline",
    upgrade_type="performance",
    dry_run=False  # Set to True to test first
)

print(result["message"])
```

## How It Works

### Self-Healing Flow

```
Pipeline Execution
        ↓
    [Fails?]
        ↓
Identify Error Pattern
        ↓
Match Recovery Strategy
        ↓
Apply Recovery Action
        ↓
Retry Execution
        ↓
    [Success?]
        ↓
   Log Learning
```

### Upgrade Flow

```
Analyze Pipeline
        ↓
Identify Issues
        ↓
Generate Candidates
        ↓
Validate Changes
        ↓
Backup Current
        ↓
Apply Upgrade
        ↓
Test Execution
        ↓
[Success?] → Commit
[Failure?] → Rollback
```

## Configuration

### Guardrails (in `.env`)

```bash
# Self-healing settings
ENABLE_SELF_HEALING=true
MAX_HEALING_ATTEMPTS=3
HEALING_BACKOFF_MULTIPLIER=2

# Auto-upgrade settings
ENABLE_AUTO_UPGRADE=true
AUTO_UPGRADE_DRY_RUN=true  # Test upgrades first
REQUIRE_UPGRADE_APPROVAL=true

# Resource limits (for recovery strategies)
MAX_MEMORY_MB=2048
MIN_BATCH_SIZE=100
MAX_EXECUTION_TIME_SECONDS=300
```

### Pipeline-Specific Settings

```yaml
# In your pipeline YAML
name: my_pipeline
description: My pipeline

# Self-healing configuration
self_healing:
  enabled: true
  max_attempts: 3
  retry_strategies:
    connection_timeout:
      max_retries: 5
      backoff: exponential
    memory_error:
      min_batch_size: 100

# Auto-upgrade preferences
auto_upgrade:
  enabled: true
  allowed_types:
    - performance
    - bug_fix
    - security
  auto_apply: false  # Require approval
  risk_tolerance: medium  # low, medium, high
```

## Best Practices

### 1. Start with Dry Run
Always test upgrades with `--dry-run` first:

```bash
python main_enhanced.py --upgrade my_pipeline --type performance --dry-run
```

### 2. Monitor Health Regularly
Check pipeline health after changes:

```bash
python main_enhanced.py --history my_pipeline
```

### 3. Set Appropriate Limits
Configure max healing attempts based on criticality:
- **Critical pipelines**: 5-10 attempts
- **Normal pipelines**: 3 attempts
- **Experimental**: 1 attempt

### 4. Version Everything
The system automatically versions changes, but you should:
- Keep version backups
- Document major changes
- Test rollbacks periodically

### 5. Learn from Failures
Review healing logs to identify systemic issues:

```bash
tail -f logs/pipeline_agent.log | grep "Self-heal"
```

## Advanced Features

### Custom Recovery Strategies

You can add custom recovery strategies:

```python
from src.agents.self_healing import SelfHealingEngine

class CustomHealingEngine(SelfHealingEngine):
    def __init__(self):
        super().__init__()
        # Add custom strategy
        self.recovery_strategies["custom_error"] = self._recover_custom_error
    
    def _recover_custom_error(self, pipeline_name, error, context):
        # Your custom recovery logic
        return True, "Applied custom recovery"
```

### Predictive Healing

The system learns from past failures:

```python
# Get failure patterns
patterns = healing_engine.failure_patterns

# Patterns with high counts indicate recurring issues
for pattern, count in patterns.items():
    if count > 5:
        print(f"Recurring issue: {pattern} ({count} times)")
```

## Limitations

**Self-healing cannot recover from:**
- Hardware failures
- Network outages (beyond retries)
- Permanent credential revocation
- Severe data corruption
- System-level issues

**Auto-upgrades won't:**
- Make breaking changes without approval
- Modify core business logic
- Change data semantics
- Affect data integrity

## Troubleshooting

### Issue: Healing not working

**Check:**
1. Is `--enable-healing` flag set?
2. Are max attempts reached?
3. Is the error pattern recognized?

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python main_enhanced.py --config pipeline.yaml --enable-healing
```

### Issue: Upgrade fails validation

**Solution:**
Review validation errors and adjust:

```python
# Check what failed
result = agent.apply_upgrade("pipeline", "performance", dry_run=True)
print(result["message"])
```

### Issue: Rollback not found

**Solution:**
Ensure versions are being saved:

```bash
# Check version backups
ls -la outputs/my_pipeline/versions/
```

## Performance Impact

**Self-healing overhead:**
- First attempt: ~0-5 seconds
- Each retry: Varies by strategy (1-60 seconds)
- Total: Usually < 2 minutes for recovery

**Auto-upgrade overhead:**
- Analysis: ~5-10 seconds
- Application: ~10-30 seconds
- Validation: ~5-10 seconds
- Total: Usually < 1 minute per upgrade

## Monitoring & Metrics

Key metrics to track:
- **Healing Success Rate**: % of failures auto-recovered
- **Average Recovery Time**: Time to recover from failure
- **Upgrade Adoption Rate**: % of suggested upgrades applied
- **Rollback Frequency**: How often rollbacks are needed
- **Health Score Trend**: Overall pipeline health over time

## Future Enhancements

Planned features:
- 🤖 **AI-powered root cause analysis**
- 🔮 **Predictive failure prevention**
- 📊 **Advanced anomaly detection**
- 🌐 **Distributed healing coordination**
- 🧪 **A/B testing for upgrades**
- 📱 **Mobile alerts for critical failures**

## Contributing

To add new recovery strategies or upgrade types, see:
- `src/agents/self_healing.py` - Core healing logic
- `src/agents/enhanced_agent.py` - Agent integration

## Support

For issues with self-healing or auto-upgrades:
1. Check logs: `logs/pipeline_agent.log`
2. Review history: `python main_enhanced.py --history <pipeline>`
3. Create GitHub issue with logs and configuration

---

**Remember**: Self-healing is powerful but not magic. Always monitor your pipelines and review auto-applied changes.