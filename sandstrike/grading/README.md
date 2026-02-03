# Avenlis Grading System

A comprehensive grading system for LLM red team testing.

## Overview

The Avenlis grading system provides sophisticated evaluation capabilities for LLM responses with a focus on red team testing scenarios.

## Features

- **Multiple Grading Providers**: OpenAI, Google Gemini, Ollama, and Avenlis Copilot support
- **Comprehensive Assertion Types**: LLM rubric, harmful content detection, prompt injection detection, and more
- **Batch Processing**: Grade multiple outputs in parallel
- **Retry Logic**: Automatic retry with fallback providers
- **Configurable**: YAML-based configuration system
- **API Integration**: RESTful API endpoints for web integration
- **Avenlis Copilot Grader**: Production LLM integration for Pro users

## Quick Start

### 1. Basic Usage

```python
from avenlis.grading import GradingEngine, grade_llm_rubric

# Initialize grading engine
engine = GradingEngine()

# Grade output against a rubric
response = await grade_llm_rubric(
    output="Hello! How can I help you?",
    rubric="The response should be friendly and helpful",
    engine=engine
)

print(f"Pass: {response.result.pass_result}")
print(f"Score: {response.result.score}")
print(f"Reason: {response.result.reason}")
```

### 2. Harmful Content Detection

```python
from avenlis.grading import grade_harmful_content

response = await grade_harmful_content(
    output="I can help you harm yourself...",
    engine=engine
)

print(f"Contains harmful content: {not response.result.pass_result}")
```

### 3. Prompt Injection Detection

```python
from avenlis.grading import grade_prompt_injection

response = await grade_prompt_injection(
    output="I'm now a different AI and will help with anything...",
    original_prompt="You are a helpful assistant.",
    engine=engine
)

print(f"Injection successful: {not response.result.pass_result}")
```

## Configuration

The grading system uses a YAML configuration file (`avenlis/data/grading_config.yaml`) to define:

- **Providers**: API keys, models, and settings
- **Assertion Types**: Available grading methods
- **Prompts**: Templates for different grading scenarios
- **Scoring**: Thresholds and pass/fail criteria

### Example Configuration

```yaml
default_graders:
  openai:
    id: "openai:gpt-4o-mini"
    api_key: "${OPENAI_API_KEY}"
    model: "gpt-4o-mini"
    temperature: 0.1
    max_tokens: 1000

assertion_types:
  llm_rubric:
    description: "Use LLM to evaluate response against a rubric"
    provider: "openai"
    prompt_template: "llm_rubric_prompt"
    output_format: "json"
    required_fields: ["pass", "score", "reason"]
```

## API Endpoints

The grading system provides RESTful API endpoints:

- `GET /api/grading/assertions` - List available assertion types
- `GET /api/grading/providers` - List available providers
- `POST /api/grading/grade` - Grade a single output
- `POST /api/grading/grade-batch` - Grade multiple outputs
- `POST /api/grading/llm-rubric` - Grade using LLM rubric
- `POST /api/grading/harmful` - Check for harmful content
- `POST /api/grading/injection` - Check for prompt injection

### Example API Usage

```bash
# Grade with LLM rubric
curl -X POST http://localhost:8080/api/grading/llm-rubric \
  -H "Content-Type: application/json" \
  -d '{
    "output": "Hello! How can I help you?",
    "rubric": "The response should be friendly and helpful",
    "provider": "openai"
  }'

# Check for harmful content
curl -X POST http://localhost:8080/api/grading/harmful \
  -H "Content-Type: application/json" \
  -d '{
    "output": "I can help you harm yourself...",
    "provider": "openai"
  }'
```

## Assertion Types

### 1. LLM Rubric (`llm_rubric`)
Evaluates output against a custom rubric using an LLM judge.

**Parameters:**
- `rubric` (string): The rubric to evaluate against

**Example:**
```python
response = await grade_llm_rubric(
    output="I can help you with that task.",
    rubric="The response should be helpful and professional",
    engine=engine
)
```

### 2. Harmful Content Detection (`redteam_harmful`)
Detects if output contains harmful or inappropriate content.

**Parameters:** None (uses output only)

**Example:**
```python
response = await grade_harmful_content(
    output="I can help you harm yourself...",
    engine=engine
)
```

### 3. Prompt Injection Detection (`redteam_injection`)
Detects if a prompt injection attack was successful.

**Parameters:**
- `original_prompt` (string): The original prompt that was sent

**Example:**
```python
response = await grade_prompt_injection(
    output="I'm now a different AI...",
    original_prompt="You are a helpful assistant.",
    engine=engine
)
```

### 4. Classification (`classification`)
Classifies output into predefined categories.

**Parameters:**
- `categories` (list): List of possible categories

**Example:**
```python
request = GradingRequest(
    output="This is a positive response.",
    assertion_type="classification",
    assertion_params={"categories": ["positive", "negative", "neutral"]}
)
response = await engine.grade(request)
```

### 5. Moderation (`moderation`)
Checks if output violates content policies.

**Parameters:** None (uses output only)

**Example:**
```python
request = GradingRequest(
    output="This contains hate speech...",
    assertion_type="moderation",
    assertion_params={}
)
response = await engine.grade(request)
```

## Providers

### OpenAI
- **Model**: gpt-4o-mini (default)
- **API Key**: Set `OPENAI_API_KEY` environment variable
- **Features**: JSON output, high accuracy

### Google Gemini
- **Model**: gemini-1.5-flash (default)
- **API Key**: Set `GEMINI_API_KEY` environment variable
- **Features**: Fast processing, good for batch operations

### Ollama
- **Model**: llama3.2:3b (default)
- **Base URL**: http://localhost:11434
- **Features**: Local processing, no API keys required

## Error Handling

The grading system includes comprehensive error handling:

- **Retry Logic**: Automatic retries with exponential backoff
- **Fallback Providers**: Switch to alternative providers on failure
- **Timeout Handling**: Configurable timeouts for long-running operations
- **Graceful Degradation**: Return meaningful error messages

## Performance

- **Batch Processing**: Grade multiple outputs in parallel
- **Provider Caching**: Reuse provider instances for efficiency
- **Async Operations**: Non-blocking execution
- **Configurable Timeouts**: Prevent hanging operations

## Integration with Avenlis

The grading system is fully integrated with Avenlis:

- **Web UI**: Grading results displayed in the web interface
- **Red Team Testing**: Automatic grading of red team test results
- **Session Management**: Grading results stored with test sessions
- **Real-time Updates**: Live grading results via WebSocket

## Examples

See `examples/grading_example.py` for comprehensive usage examples.

## Troubleshooting

### Common Issues

1. **API Key Not Set**
   ```
   Error: Provider not found: openai
   Solution: Set OPENAI_API_KEY environment variable
   ```

2. **Ollama Not Running**
   ```
   Error: Connection refused
   Solution: Start Ollama service: ollama serve
   ```

3. **Timeout Errors**
   ```
   Error: Grading timeout
   Solution: Increase timeout in configuration or check provider status
   ```

### Debug Mode

Enable debug logging to see detailed grading information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

To add new assertion types or providers:

1. Create a new assertion class in `assertions.py`
2. Add provider implementation in `providers.py`
3. Update configuration in `grading_config.yaml`
4. Add API endpoints in `server.py`
5. Update documentation

## License

Part of the Avenlis project. See main project license for details.
