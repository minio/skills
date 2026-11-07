---
tags: [docs]
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit]
---

write a TROUBLESHOOTING.md for our cli `bktsync` that copies a local dir to an s3 bucket. the 3 problems users hit most:
1. AccessDenied -> their key lacks s3:PutObject on the bucket, fix the IAM policy
2. "x509: certificate signed by unknown authority" -> self-signed cert on their minio, they pass --ca-file /path/ca.pem (or --insecure for testing only, never prod)
3. sync seems to hang on big dirs -> it's actually listing the bucket first, use --progress to see it, and --exclude to skip node_modules etc
