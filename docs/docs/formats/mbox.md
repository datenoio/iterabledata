# MBOX Format (Mailbox)

## Description

MBOX is a format for storing collections of email messages. It's a simple format where multiple email messages are concatenated in a single file, with each message starting with a "From " line. MBOX is commonly used by email clients like Thunderbird.

## File Extensions

- `.mbox` - MBOX mailbox files

## Implementation Details

### Reading

The MBOX implementation:
- Uses Python's built-in `mailbox` module
- Parses MBOX format
- Extracts individual email messages
- Converts each email to a dictionary
- Handles email headers and body
- Requires file path (not stream)

### Writing

Writing support:
- Creates MBOX files
- Writes email messages to mailbox
- Requires file path (not stream)

### Key Features

- **Multiple messages**: Can contain multiple email messages
- **Email format**: Designed for email storage
- **Header extraction**: Extracts email headers
- **Body handling**: Handles email body content
- **Nested data**: Supports complex email structures

## Usage

```python
from iterable import open_iterable

# Basic reading
source = open_iterable('mailbox.mbox')
for email in source:
    print(email)  # Contains email headers and body
source.close()

# Writing
dest = open_iterable('output.mbox', mode='w')
dest.write({
    'from': 'sender@example.com',
    'to': 'recipient@example.com',
    'subject': 'Test',
    'body': 'Message body'
})
dest.close()
```

## Parameters

- `encoding` (str): File encoding (default: `utf8`)

## Limitations

1. **File path required**: Requires filename, not stream
2. **Email focus**: Designed for email data, not general data
3. **Format complexity**: Email structure can be complex
4. **Memory usage**: Large mailboxes may use significant memory

## Compression Support

MBOX files can be compressed with all supported codecs:
- GZip (`.mbox.gz`)
- BZip2 (`.mbox.bz2`)
- LZMA (`.mbox.xz`)
- LZ4 (`.mbox.lz4`)
- ZIP (`.mbox.zip`)
- Brotli (`.mbox.br`)
- ZStandard (`.mbox.zst`)

## Use Cases

- **Email archiving**: Archiving email messages
- **Email migration**: Migrating email between systems
- **Email analysis**: Analyzing email collections
- **Backup**: Backing up email messages

## Related Formats

- [EML](eml.md) - Single email format
- [MHTML](mhtml.md) - Web archive format
