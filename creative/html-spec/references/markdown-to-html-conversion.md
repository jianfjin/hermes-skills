# Markdown to HTML — Safe Conversion Pattern

## Problem

`read_file(path)` returns content with line-number prefixes:
```
     1|# Title
     2|
     3|Some text
```

Injecting this directly into `<body>` produces unreadable HTML.

## Solution

Use `terminal cat` for clean raw content:

```python
from hermes_tools import terminal
result = terminal("cat /path/to/file.md")
clean_md = result["output"]  # No line numbers
```

## Conversion Pipeline

```python
import re

lines = clean_md.split('\n')
body_parts = []
in_code_block = False

for line in lines:
    s = line.strip()
    
    # Code fences
    if s.startswith('```'):
        if in_code_block:
            body_parts.append('</code></pre>')
            in_code_block = False
        else:
            body_parts.append('<pre><code>')
            in_code_block = True
        continue
    
    if in_code_block:
        body_parts.append(line)
        continue
    
    # Block elements
    if s.startswith('### '): body_parts.append(f'<h3>{s[4:]}</h3>')
    elif s.startswith('## '): body_parts.append(f'<h2>{s[3:]}</h2>')
    elif s.startswith('# '): body_parts.append(f'<h1>{s[2:]}</h1>')
    elif s.startswith('> '): body_parts.append(f'<blockquote>{s[2:]}</blockquote>')
    elif s == '---': body_parts.append('<hr>')
    elif s == '' or s is None: body_parts.append('')
    # Table rows
    elif s.startswith('|') and s.endswith('|'):
        cells = [c.strip() for c in s.split('|')[1:-1]]
        if all(c.startswith('---') or c.startswith(':--') for c in cells):
            pass
        else:
            body_parts.append('<tr>' + ''.join(f'<td>{c}</td>' for c in cells) + '</tr>')
    # List items
    elif s.startswith('- '):
        body_parts.append(f'<li>{s[2:]}</li>')
    # Paragraphs
    else:
        s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
        s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
        body_parts.append(f'<p>{s}</p>')

# Wrap consecutive <td> in <table>
i = 0
while i < len(body_parts):
    if body_parts[i].startswith('<td>'):
        body_parts[i] = '<table>' + body_parts[i]
        j = i + 1
        while j < len(body_parts) and body_parts[j].startswith('<td>'):
            j += 1
        body_parts[j-1] = body_parts[j-1] + '</table>'
        i = j
    else:
        i += 1

body_html = '\n'.join(body_parts)
```

## Key Rules

1. **Never** use `read_file` output directly as HTML content
2. **Always** strip line-number prefixes before conversion
3. **Use** `terminal cat` for clean raw content
4. **Wrap** in html-spec template with proper `<section>` structure
5. **Don't** import markdown libraries — keep it self-contained Python
