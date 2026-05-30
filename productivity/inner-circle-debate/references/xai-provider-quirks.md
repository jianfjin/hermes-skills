# xAI (Grok) Provider Quirks

**Last updated:** 2026-05-29

## API Key Source
xAI reads API key **only** from `XAI_API_KEY` env var. Profile config `model.api_key` does NOT work.

## `reasoning_effort` Parameter
Both grok-4.20-0309-reasoning and grok-4.20-0309-non-reasoning reject this parameter. Set `reasoning_effort: none` in profile config.yaml.

## Working Profile Config
```yaml
model:
  api_key: ''
  default: grok-4.20-0309-reasoning
  context_length: 65536
  provider: xai
```

## DeepSeek-v4-flash 32K Context Workaround
Override BOTH values or Hermes blocks startup:
```yaml
model:
  context_length: 32768
auxiliary:
  compression:
    context_length: 32768
```
