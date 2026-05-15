---
name: gcloud-drive-adc-access
description: Workflow for enabling AI agent access to Google Drive via gcloud CLI and Application Default Credentials.
---

# GCloud Drive ADC Access Workflow

This skill describes the process of enabling an AI agent to access Google Drive files using the Google Cloud CLI and Application Default Credentials (ADC).

## Trigger Conditions
- Need to access files in Google Drive programmatically from a terminal environment.
- User has gcloud CLI installed and has a Google project.
- **If the file is shared with "Anyone with the link", try the direct curl approach first (see Alternative below).**

## Alternative: Direct curl download (try first for public files)

If the Google Drive file is shared with "Anyone with the link" access, skip the entire
gcloud/ADC flow and use curl directly:

```bash
# Extract file ID from the sharing URL
# https://drive.google.com/file/d/FILE_ID/view?usp=drive_link
curl -L -o output.pdf "https://drive.google.com/uc?export=download&id=FILE_ID"
```

This is much faster than setting up ADC and works for any publicly shared file.
Only fall back to the ADC flow below if the file requires authentication.

## Step-by-Step Process

1. **Standard Authentication**:
   Run `gcloud auth login` to authenticate the primary account in the browser.

2. **Application Default Credentials (ADC)**:
   Set up credentials that libraries (like `google-api-python-client`) can use automatically. Use a combined scope to avoid "cloud-platform scope required" errors:
   ```bash
   gcloud auth application-default login --scopes="https://www.googleapis.com/auth/cloud-platform,https://www.googleapis.com/auth/drive.readonly"
   ```

3. **Impersonation (Advanced)**:
   If simple ADC fails, use the `--impersonate-service-account` flag, but ensure the account is a valid service account identity.

4. **Python Implementation**:
   Use `google.auth.default()` to load credentials and `googleapiclient.discovery.build` to interact with the Drive API.

## Pitfalls & Lessons Learned
- **Scope Errors**: Google Cloud often rejects requests that don't include `https://www.googleapis.com/auth/cloud-platform` alongside custom scopes.
- **Impersonation Failures**: Impersonating a standard @gmail.com account via `--impersonate-service-account` typically fails with "Gaia id not found" because standard accounts are not service accounts. Standard accounts should use the `application-default login` flow instead.
- **Library Installation**: In restricted environments, avoid `pip install` on system Python. Use `--break-system-packages` if necessary or use a virtual environment.
- **Sandbox Isolation**: Be aware that some execution sandboxes may not share the same site-packages directory as the main terminal; verify imports using `python3 -c "import ..."` before running complex scripts.

## Verification
- Run a small script using `google.auth.default()` to ensure no `DefaultCredentialsError` is thrown.
- List files in a known folder to verify `drive.readonly` permissions.