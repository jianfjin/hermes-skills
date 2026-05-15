---
name: google-drive-whisper-pipeline
description: Pipeline for downloading audio from Google Drive via gcloud and transcribing with OpenAI Whisper, handling auth scopes and large file timeouts.
---

# Google Drive Audio Transcription Pipeline

This skill describes the process of downloading audio files from Google Drive using the gcloud CLI and transcribing them using OpenAI Whisper, specifically handling authentication hurdles and large file constraints.

## Trigger Conditions
- User provides a Google Drive folder/file link for audio transcription.
- Environment requires gcloud CLI for access.
- Audio files exceed the direct-upload size limits of the messaging platform.

## Step-by-Step Workflow

### 1. Authentication & Access
Standard browser-based Drive interaction often fails due to bot detection or UI complexity. Use the Google Cloud SDK for programmatic access.
- **Account Login:** `gcloud auth login`
- **Application Default Credentials (ADC):** `gcloud auth application-default login --scopes="https://www.googleapis.com/auth/cloud-platform,https://www.googleapis.com/auth/drive.readonly"`
- **Impersonation:** If needed, use `--impersonate-service-account="USER_EMAIL"`.

### 2. File Retrieval
Use the `google-api-python-client` to locate and download files.
- **Library Installation:** `pip install --break-system-packages google-api-python-client google-auth-httplib2 google-auth-oauthlib`
- **Search Logic:** Filter by `folder_id` and `trashed = false` to find specific file names (e.g., `d1.MP3`).
- **Download:** Use `MediaIoBaseDownload` to save the binary content locally.

### 3. Transcription via Whisper
- **Installation:** `pip install --break-system-packages openai-whisper`
- **Execution:** For files that may cause timeouts ( > 20MB), do NOT use foreground terminal commands. 
- **Optimization:** Use the `tiny` or `base` model for faster processing if high precision isn't critical, as larger models significantly increase render time.
- **Handling Timeouts:** Run the transcription script as a background process (via `terminal(background=True)`) to avoid platform timeouts.

## Pitfalls & Solutions
- **Dependency Conflicts:** Use `--break-system-packages` if working in an externally managed environment where virtualenvs aren't pre-configured.
- **Authorization Errors:** "Gaia id not found" or "Scope required" errors usually occur when the base `cloud-platform` scope is missing. Always include both platform and drive scopes.
- **Sandbox vs Terminal:** Libraries installed in the terminal may not be visible to `execute_code`. Run critical scripts as standalone Python files via `python3 script.py` in the terminal.
- **Processing Time:** Whisper is CPU/GPU intensive. For long audio files, the process will almost certainly time out in a standard foreground call. Always use background execution for files > 10 minutes.

## Verification
- Confirm files exist: `ls -lh *.txt`
- Verify content: `head -n 20 d1.txt`
