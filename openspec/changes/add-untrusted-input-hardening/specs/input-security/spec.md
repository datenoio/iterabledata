## ADDED Requirements

### Requirement: XML Parsing Without External Entity Resolution

All XML parsing SHALL be performed with external entity resolution and network access disabled, so that untrusted XML cannot trigger XXE (external entity expansion, file disclosure, SSRF) or entity-expansion denial of service. This applies to every lxml/ElementTree call site, including `xml`, `kml`, `gml`, and `kmz`.

#### Scenario: External entity is not resolved

- **WHEN** an XML/KML/GML document declaring an external entity (e.g. `<!ENTITY x SYSTEM "file:///etc/passwd">`) is read
- **THEN** the parser SHALL NOT fetch or expand the external entity
- **AND** the referenced file or URL contents SHALL NOT appear in any yielded record

#### Scenario: No network access during parse

- **WHEN** an XML document references an external DTD or entity over the network
- **THEN** the parser SHALL NOT make a network request

### Requirement: No eval for Type Resolution

Type resolution in validation SHALL NOT use `eval()`. Python type names SHALL be resolved through an explicit lookup table of allowed types.

#### Scenario: Known type resolves without eval

- **WHEN** a validation rule references a supported type name (e.g. `"int"`, `"str"`)
- **THEN** the type SHALL be resolved via the lookup table
- **AND** no `eval()` call SHALL be executed

#### Scenario: Unknown type name is rejected

- **WHEN** a validation rule references an unknown type name
- **THEN** the system SHALL raise a clear error
- **AND** SHALL NOT attempt to evaluate the name as code

### Requirement: Pickle Trust Disclosure

The pickle format SHALL document that loading pickled data executes arbitrary code and is unsafe on untrusted input, in both the class docstring and the format documentation.

#### Scenario: Pickle risk is documented

- **WHEN** a developer reads the `picklef` class docstring or `docs/docs/formats/pickle.md`
- **THEN** it SHALL state that unpickling untrusted data can execute arbitrary code
