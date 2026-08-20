# EML Format (Email)

## Description

EML (Email) format represents a single email message in RFC 822 format. EML files contain email headers and body content, and may include attachments. Each EML file typically represents one email message.

## File Extensions

- `.eml` - Email message files

## Implementation Details

### Reading

The EML implementation:
- Uses Python's built-in `email` module
- Parses RFC 822 email format
- Extracts email headers (From, To, Subject, Date, etc.)
- Handles email body (text and HTML)
- Extracts attachments
- Converts email to dictionary

### Writing

Writing support:
- Builds an RFC 822 message from header fields (`from`, `to`, `subject`, …)
- Uses `body` or `body_text` as the message content

### Key Features

- **Email format**: Single email message format
- **Header extraction**: Extracts all email headers
- **Body handling**: Handles text and HTML body
- **Attachment support**: Extracts attachment information
- **Date parsing**: Parses email dates

## Usage

```python
from iterable import open_iterable

# Basic reading
with open_iterable('message.eml') as source:
    for email in source:
        print(email)  # Contains email headers and body

# Writing
with open_iterable('output.eml', mode='w') as dest:
    dest.write({
        'from': 'a@example.com',
        'to': 'b@example.com',
        'subject': 'Hello',
        'body': 'Message text',
    })
```

## Parameters

- `encoding` (str): File encoding (default: `utf8`)

## Limitations

1. **Single message**: Each file typically contains one email
2. **Email focus**: Designed for email data, not general data
3. **Complex structure**: Email structure can be complex with multipart content

## Compression Support

EML files can be compressed with all supported codecs:
- GZip (`.eml.gz`)
- BZip2 (`.eml.bz2`)
- LZMA (`.eml.xz`)
- LZ4 (`.eml.lz4`)
- ZIP (`.eml.zip`)
- Brotli (`.eml.br`)
- ZStandard (`.eml.zst`)

## Use Cases

- **Email processing**: Processing individual email messages
- **Email archiving**: Archiving email messages
- **Email analysis**: Analyzing email content
- **Data migration**: Migrating email data


## Error Handling

- **Missing dependency**: optional libraries raise `ImportError` with an install hint (`pip install 'iterabledata[<extra>]'` when an extra exists).
- **Write mode**: read-only formats raise `WriteNotSupportedError` or `ValueError` when opened with `mode="w"`.
- **Bad or unsupported input**: may raise `ValueError`, `OSError`, or library-specific errors.
- See [Troubleshooting](/getting-started/troubleshooting) for decoding, detection, and engine issues.

## Related Formats

- [MBOX](mbox.md) - Mailbox format (multiple emails)
- [MHTML](mhtml.md) - Web archive format
