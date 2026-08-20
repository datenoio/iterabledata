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

Writing is not currently supported for EML format.

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
```

## Parameters

- `encoding` (str): File encoding (default: `utf8`)

## Limitations

1. **Read-only**: EML format does not support writing
2. **Single message**: Each file typically contains one email
3. **Email focus**: Designed for email data, not general data
4. **Complex structure**: Email structure can be complex with multipart content

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

## Related Formats

- [MBOX](mbox.md) - Mailbox format (multiple emails)
- [MHTML](mhtml.md) - Web archive format
