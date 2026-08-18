# iCal Format

## Description

iCal (iCalendar) is a standard format (RFC 5545) for calendar data exchange. It's used by calendar applications like Google Calendar, Apple Calendar, and Microsoft Outlook. iCal files contain calendar events, todos, and other calendar components.

## File Extensions

- `.ical` - iCalendar files
- `.ics` - iCalendar files (alias)

## Implementation Details

### Reading

The iCal implementation:
- Uses `icalendar` or `ics` library for parsing
- Parses iCalendar format
- Extracts calendar events (VEVENT components)
- Converts events to dictionaries
- Handles event properties (start, end, summary, etc.)

### Writing

Writing support:
- Creates iCalendar format
- Writes calendar events
- Supports event properties

### Key Features

- **Calendar format**: Designed for calendar data
- **Standard format**: RFC 5545 standard
- **Event extraction**: Extracts calendar events
- **Nested data**: Supports complex calendar structures
- **Date handling**: Properly handles dates and times

## Usage

```python
from iterable import open_iterable

# Basic reading
source = open_iterable('calendar.ics')
for event in source:
    print(event)  # Contains event properties
source.close()

# Writing
dest = open_iterable('output.ics', mode='w')
dest.write({
    'summary': 'Meeting',
    'dtstart': '20240101T120000Z',
    'dtend': '20240101T130000Z'
})
dest.close()
```

## Parameters

- `encoding` (str): File encoding (default: `utf8`)

## Limitations

1. **Dependency**: Requires `icalendar` or `ics` package
2. **Calendar focus**: Designed for calendar data, not general data
3. **Memory usage**: Entire calendar may be loaded into memory
4. **Format complexity**: Complex calendar structures may require manual handling

## Compression Support

iCal files can be compressed with all supported codecs:
- GZip (`.ics.gz`)
- BZip2 (`.ics.bz2`)
- LZMA (`.ics.xz`)
- LZ4 (`.ics.lz4`)
- ZIP (`.ics.zip`)
- Brotli (`.ics.br`)
- ZStandard (`.ics.zst`)

## Use Cases

- **Calendar applications**: Working with calendar data
- **Event management**: Processing calendar events
- **Scheduling**: Calendar scheduling systems
- **Data migration**: Migrating calendar data

## Related Formats

- [VCF](vcf.md) - vCard format (contact information)
- [EML](eml.md) - Email format
