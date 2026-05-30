# WhatsApp Media Delivery Limitation

`send_message` with `MEDIA:/path/to/file` syntax silently omits the attachment for WhatsApp.

**Symptom:**
```json
{
  "success": true,
  "warnings": [
    "MEDIA attachments were omitted for whatsapp; native send_message media delivery is currently only supported for telegram, discord, matrix, weixin, signal, yuanbao and feishu"
  ]
}
```

**Supported platforms for native media delivery:** telegram, discord, matrix, weixin, signal, yuanbao, feishu.

**WhatsApp is NOT in this list.** The message body is delivered but the file is stripped.

**Workarounds for delivering files via WhatsApp:**
1. **Paste content inline** (for prose/documents under ~500 lines) — summarize with key excerpts
2. **Use `MEDIA:` for supported platforms** like yuanbao or telegram if the user has those configured
3. **Tell the user the file path** — they can open it locally
4. **For images:** Use `![alt](url)` markdown syntax — these render as photos on WhatsApp
