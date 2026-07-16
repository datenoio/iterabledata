import zipfile

zip_path = "/Users/ibegtin/workspace/data/rmsp/data-10122025-structure-10062025.zip"

try:
    with zipfile.ZipFile(zip_path, "r") as z:
        print(f"Files in zip: {len(z.namelist())}")
        xml_files = [f for f in z.namelist() if f.endswith(".xml")]
        print(f"XML files in zip: {len(xml_files)}")
        if xml_files:
            first_xml = xml_files[0]
            print(f"Reading first XML: {first_xml}")
            with z.open(first_xml) as f:
                head = f.read(1000).decode("utf-8", errors="ignore")
                print("--- Start of XML ---")
                print(head)
                print("--- End of XML ---")
except Exception as e:
    print(f"Error: {e}")
