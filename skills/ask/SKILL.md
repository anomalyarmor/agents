---
name: armor-ask
description: Ask natural language questions about your data. Handles "what tables contain", "tell me about", "explain", "what do you know about", "describe".
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "python ${CLAUDE_PLUGIN_ROOT}/scripts/ensure-auth.py"
          once: true
---

# Ask About Your Data

Ask natural language questions about your database structure, lineage, and metadata using AnomalyArmor Intelligence.

## Prerequisites

- AnomalyArmor API key configured (`~/.armor/config.yaml` or `ARMOR_API_KEY` env var)
- Python SDK installed (`pip install anomalyarmor`)
- Intelligence generated for the asset (use `/armor:analyze` if needed)

## When to Use

- "What tables contain customer data?"
- "Tell me about the orders table"
- "What are the upstream dependencies of this table?"
- "Which columns have PII?"
- "Explain the data model for finance"
- "What do you know about the users table?"

## Steps

1. Identify the asset to query (database/warehouse)
2. Formulate the question (3-2000 characters)
3. Call `client.intelligence.ask()`
4. Present the answer with confidence and sources

## Example Usage

### Basic Question

```python
from anomalyarmor import Client

client = Client()

# Ask about your data
answer = client.intelligence.ask(
    asset="postgresql.analytics",
    question="What tables contain customer data?"
)

print(f"Answer: {answer.answer}")
print(f"Confidence: {answer.confidence}")
print(f"Sources: {answer.sources}")
```

### Question About Specific Table

```python
from anomalyarmor import Client

client = Client()

answer = client.intelligence.ask(
    asset="postgresql.analytics",
    question="Describe the orders table and its columns"
)

print(answer.answer)
```

### Cross-Database Query

```python
from anomalyarmor import Client

client = Client()

# Include related assets for cross-database context
answer = client.intelligence.ask(
    asset="postgresql.analytics",
    question="What data flows from staging to production?",
    include_related_assets=True
)

print(answer.answer)
```

### Get Structured Response for Automation

```python
from anomalyarmor import Client
import json

client = Client()

# Ask for JSON format in your question
answer = client.intelligence.ask(
    asset="postgresql.analytics",
    question="List all tables with PII columns as a JSON array with table_name and columns fields"
)

# Parse the JSON response
try:
    pii_tables = json.loads(answer.answer)
    for table in pii_tables:
        print(f"Table: {table['table_name']}")
        print(f"  PII Columns: {table['columns']}")
except json.JSONDecodeError:
    print(answer.answer)
```

## Example Questions

| Category | Example Questions |
|----------|-------------------|
| Schema | "What columns are in the orders table?" |
| Lineage | "Where does the revenue column come from?" |
| PII | "Which tables contain email addresses?" |
| Relationships | "What tables join with customers?" |
| Purpose | "What is the orders table used for?" |
| Quality | "What data quality issues exist in this database?" |

## Tips for Better Answers

1. **Be specific**: "Describe the orders table" is better than "Tell me about orders"
2. **Ask for JSON**: If you need structured data for automation
3. **Use table names**: Include schema.table format when possible
4. **Include context**: Mention the specific aspect you're interested in

## If No Intelligence Available

If you get an error about missing intelligence:

1. Check if intelligence has been generated for the asset
2. Use `/armor:analyze` to trigger intelligence generation
3. Wait for the job to complete (typically 1-5 minutes)
4. Try asking again

## Follow-up Actions

- Use `/armor:analyze` to generate or refresh intelligence
- Use `/armor:status` to check overall health
- Explore lineage in AnomalyArmor dashboard for visual representation
