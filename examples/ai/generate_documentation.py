"""
Example: Generate AI-Powered Dataset Documentation

This example demonstrates how to use IterableData's AI documentation generation
feature to automatically create comprehensive documentation for datasets using
various LLM providers.
"""

import os
import sys
from pathlib import Path

from iterable.ai import doc


def example_basic_markdown():
    """Example 1: Basic markdown documentation generation."""
    print("=" * 70)
    print("Example 1: Basic Markdown Documentation")
    print("=" * 70)
    
    # Check if a file path was provided
    if len(sys.argv) > 1:
        data_file = sys.argv[1]
    else:
        print("Usage: python generate_documentation.py <data_file>")
        print("Example: python generate_documentation.py data.csv")
        return
    
    if not os.path.exists(data_file):
        print(f"Error: File '{data_file}' not found.")
        return
    
    print(f"\nGenerating documentation for: {data_file}")
    print("Using OpenAI provider with latest GPT-4o model...")
    
    try:
        # Generate markdown documentation with latest OpenAI model
        documentation = doc.generate(
            data_file,
            provider="openai",
            model="gpt-4o",  # Latest GPT-4o model
            format="markdown"
        )
        
        # Print documentation
        print("\n" + "-" * 70)
        print("Generated Documentation:")
        print("-" * 70)
        print(documentation)
        
        # Save to file
        output_file = Path(data_file).stem + "_documentation.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(documentation)
        print(f"\n✓ Documentation saved to: {output_file}")
        
    except ImportError as e:
        print(f"\n✗ Error: Missing dependencies. {e}")
        print("Install with: pip install openai")
    except Exception as e:
        print(f"\n✗ Error: {e}")


def example_json_format():
    """Example 2: Generate documentation in JSON format."""
    print("\n" + "=" * 70)
    print("Example 2: JSON Format Documentation")
    print("=" * 70)
    
    if len(sys.argv) > 1:
        data_file = sys.argv[1]
    else:
        return
    
    if not os.path.exists(data_file):
        return
    
    print(f"\nGenerating JSON documentation for: {data_file}")
    
    try:
        # Generate JSON documentation with latest OpenAI model
        result = doc.generate(
            data_file,
            provider="openai",
            model="gpt-4o",  # Latest GPT-4o model
            format="json"
        )
        
        # Access different components
        print("\n" + "-" * 70)
        print("Documentation (markdown):")
        print("-" * 70)
        print(result["documentation"][:500] + "..." if len(result["documentation"]) > 500 else result["documentation"])
        
        print("\n" + "-" * 70)
        print("Schema Information:")
        print("-" * 70)
        if result.get("schema"):
            import json
            print(json.dumps(result["schema"], indent=2, default=str)[:500] + "...")
        
        print("\n" + "-" * 70)
        print("Token Usage:")
        print("-" * 70)
        if result.get("usage"):
            import json
            print(json.dumps(result["usage"], indent=2))
        
        # Save JSON result
        output_file = Path(data_file).stem + "_documentation.json"
        import json
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\n✓ Full JSON result saved to: {output_file}")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")


def example_html_format():
    """Example 3: Generate documentation in HTML format."""
    print("\n" + "=" * 70)
    print("Example 3: HTML Format Documentation")
    print("=" * 70)
    
    if len(sys.argv) > 1:
        data_file = sys.argv[1]
    else:
        return
    
    if not os.path.exists(data_file):
        return
    
    print(f"\nGenerating HTML documentation for: {data_file}")
    
    try:
        # Generate HTML documentation with latest OpenAI model
        html_docs = doc.generate(
            data_file,
            provider="openai",
            model="gpt-4o",  # Latest GPT-4o model
            format="html"
        )
        
        # Save HTML file
        output_file = Path(data_file).stem + "_documentation.html"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_docs)
        print(f"\n✓ HTML documentation saved to: {output_file}")
        print(f"  Open in browser: file://{os.path.abspath(output_file)}")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")


def example_customization():
    """Example 4: Customize documentation generation."""
    print("\n" + "=" * 70)
    print("Example 4: Customized Documentation")
    print("=" * 70)
    
    if len(sys.argv) > 1:
        data_file = sys.argv[1]
    else:
        return
    
    if not os.path.exists(data_file):
        return
    
    print(f"\nGenerating customized documentation for: {data_file}")
    print("  - More samples (10 instead of default 5)")
    print("  - Lower temperature (0.3 for more deterministic output)")
    print("  - Without schema (faster, less accurate)")
    
    try:
        # Customized generation with latest OpenAI model
        documentation = doc.generate(
            data_file,
            provider="openai",
            model="gpt-4o",  # Latest GPT-4o model
            sample_size=10,
            temperature=0.3,
            include_schema=False  # Faster but less accurate
        )
        
        output_file = Path(data_file).stem + "_documentation_custom.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(documentation)
        print(f"\n✓ Customized documentation saved to: {output_file}")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")


def example_different_providers():
    """Example 5: Use different LLM providers, prioritizing LM Studio (local)."""
    print("\n" + "=" * 70)
    print("Example 5: Different LLM Providers")
    print("=" * 70)
    
    if len(sys.argv) > 1:
        data_file = sys.argv[1]
    else:
        return
    
    if not os.path.exists(data_file):
        return
    
    providers = [
        {
            "name": "LMStudio (Local - Recommended)",
            "provider": "lmstudio",
            "base_url": "http://localhost:1234/v1",
            "model": None  # Will use model loaded in LMStudio
        },
        {
            "name": "OpenAI (Latest GPT-4o)",
            "provider": "openai",
            "api_key_env": "OPENAI_API_KEY",
            "model": "gpt-4o"
        },
        {
            "name": "OpenRouter",
            "provider": "openrouter",
            "api_key_env": "OPENROUTER_API_KEY"
        },
        {
            "name": "Ollama (Local)",
            "provider": "ollama",
            "base_url": "http://localhost:11434",
            "model": "llama2"
        },
        {
            "name": "Perplexity",
            "provider": "perplexity",
            "api_key_env": "PERPLEXITY_API_KEY"
        }
    ]
    
    print("\nAvailable providers:")
    for i, p in enumerate(providers, 1):
        print(f"  {i}. {p['name']} ({p['provider']})")
    
    print("\nNote: This example will try LM Studio first (local, free), then OpenAI.")
    print("To use other providers:")
    print("  - For LM Studio: Start LMStudio, load a model, start local server")
    print("  - For OpenAI: Set OPENAI_API_KEY environment variable")
    print("  - For other providers: Set appropriate API keys")
    
    try:
        # Try LM Studio first (local, free, recommended)
        try:
            import requests
            # Check if LM Studio is running
            response = requests.get("http://localhost:1234/v1/models", timeout=2)
            if response.status_code == 200:
                models = response.json()
                available_models = models.get("data", [])
                if available_models:
                    model_name = available_models[0].get("id", "local-model")
                    print(f"\n✓ LM Studio detected with model: {model_name}")
                    print(f"Trying LM Studio provider (local, free)...")
                    documentation = doc.generate(
                        data_file,
                        provider="lmstudio",
                        base_url="http://localhost:1234/v1",
                        model=model_name
                    )
                    print("✓ Successfully generated with LM Studio (local)")
                    
                    # Save output
                    output_file = Path(data_file).stem + "_documentation_lmstudio.md"
                    with open(output_file, "w", encoding="utf-8") as f:
                        f.write(documentation)
                    print(f"✓ Documentation saved to: {output_file}")
                    return
                else:
                    print("\n⚠ LM Studio is running but no models are loaded.")
                    print("  Load a model in LM Studio and try again.")
        except Exception as e:
            print(f"\n⚠ LM Studio not available: {e}")
        
        # Try OpenAI with latest model
        if os.getenv("OPENAI_API_KEY"):
            print(f"\nTrying OpenAI provider with GPT-4o (latest model)...")
            documentation = doc.generate(
                data_file,
                provider="openai",
                model="gpt-4o"  # Latest GPT-4o model
            )
            print("✓ Successfully generated with OpenAI GPT-4o")
            
            # Save output
            output_file = Path(data_file).stem + "_documentation_openai.md"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(documentation)
            print(f"✓ Documentation saved to: {output_file}")
            return
        
        # Try Ollama if available
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if response.status_code == 200:
                print(f"\nTrying Ollama provider (local)...")
                documentation = doc.generate(
                    data_file,
                    provider="ollama",
                    base_url="http://localhost:11434",
                    model="llama2"
                )
                print("✓ Successfully generated with Ollama")
                return
        except Exception:
            pass
        
        print("\n⚠ No available providers found.")
        print("\nTo use LM Studio (recommended, free):")
        print("  1. Install LM Studio from https://lmstudio.ai")
        print("  2. Download and load a model in LM Studio")
        print("  3. Start the local server (usually port 1234)")
        print("  4. Run this example again")
        print("\nOr set OPENAI_API_KEY environment variable for OpenAI.")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")


def example_lmstudio_local():
    """Example 6: Use LM Studio (local, free) for documentation generation."""
    print("\n" + "=" * 70)
    print("Example 6: LM Studio (Local, Free)")
    print("=" * 70)
    
    if len(sys.argv) > 1:
        data_file = sys.argv[1]
    else:
        return
    
    if not os.path.exists(data_file):
        return
    
    print(f"\nGenerating documentation for: {data_file}")
    print("Using LM Studio (local, free, no API key required)...")
    print("\nPrerequisites:")
    print("  1. Install LM Studio from https://lmstudio.ai")
    print("  2. Download and load a model in LM Studio")
    print("  3. Start the local server (usually runs on port 1234)")
    
    try:
        import requests
        
        # Check if LM Studio is running
        print("\nChecking LM Studio connection...")
        try:
            response = requests.get("http://localhost:1234/v1/models", timeout=2)
            if response.status_code == 200:
                models = response.json()
                available_models = models.get("data", [])
                if available_models:
                    model_name = available_models[0].get("id", "local-model")
                    print(f"✓ LM Studio detected!")
                    print(f"  Available model: {model_name}")
                    print(f"  Total models: {len(available_models)}")
                    
                    # Generate documentation
                    print(f"\nGenerating documentation using {model_name}...")
                    documentation = doc.generate(
                        data_file,
                        provider="lmstudio",
                        base_url="http://localhost:1234/v1",
                        model=model_name
                    )
                    
                    # Print first part of documentation
                    print("\n" + "-" * 70)
                    print("Generated Documentation (first 500 chars):")
                    print("-" * 70)
                    print(documentation[:500] + "..." if len(documentation) > 500 else documentation)
                    
                    # Save to file
                    output_file = Path(data_file).stem + "_documentation_lmstudio.md"
                    with open(output_file, "w", encoding="utf-8") as f:
                        f.write(documentation)
                    print(f"\n✓ Documentation saved to: {output_file}")
                    print("\n✓ Success! LM Studio is free and runs locally - no API costs!")
                    return
                else:
                    print("✗ LM Studio is running but no models are loaded.")
                    print("  Please load a model in LM Studio and try again.")
                    return
            else:
                print(f"✗ LM Studio returned status code: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print("✗ Cannot connect to LM Studio.")
            print("\nTo set up LM Studio:")
            print("  1. Download from https://lmstudio.ai")
            print("  2. Install and open LM Studio")
            print("  3. Go to 'Search' tab and download a model (e.g., Llama 3, Mistral)")
            print("  4. Go to 'Local Server' tab")
            print("  5. Click 'Start Server' (usually runs on http://localhost:1234)")
            print("  6. Run this example again")
            return
        except Exception as e:
            print(f"✗ Error connecting to LM Studio: {e}")
            return
            
    except ImportError:
        print("\n✗ Error: Missing 'requests' library.")
        print("Install with: pip install requests")
    except Exception as e:
        print(f"\n✗ Error: {e}")


def example_perplexity():
    """Example 7: Use Perplexity for documentation generation."""
    print("\n" + "=" * 70)
    print("Example 7: Perplexity Provider")
    print("=" * 70)
    
    if len(sys.argv) > 1:
        data_file = sys.argv[1]
    else:
        return
    
    if not os.path.exists(data_file):
        return
    
    print(f"\nGenerating documentation for: {data_file}")
    print("Using Perplexity provider...")
    print("\nPerplexity Features:")
    print("  - Online model with web search capabilities")
    print("  - Good for datasets that may benefit from external context")
    print("  - Uses sonar-pro by default (best for web-grounded conversations)")
    
    # Check for API key
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        print("\n⚠ PERPLEXITY_API_KEY environment variable not set.")
        print("\nTo use Perplexity:")
        print("  1. Sign up at https://www.perplexity.ai/")
        print("  2. Get your API key from https://www.perplexity.ai/settings/api")
        print("  3. Set environment variable: export PERPLEXITY_API_KEY='pplx-...'")
        print("  4. Run this example again")
        return
    
    try:
        # Generate documentation with Perplexity
        print(f"\nGenerating documentation using Perplexity...")
        documentation = doc.generate(
            data_file,
            provider="perplexity",
            model="sonar-pro",  # Default Perplexity model (best for web-grounded conversations)
            api_key=api_key,
            format="markdown"
        )
        
        # Print first part of documentation
        print("\n" + "-" * 70)
        print("Generated Documentation (first 500 chars):")
        print("-" * 70)
        print(documentation[:500] + "..." if len(documentation) > 500 else documentation)
        
        # Save to file
        output_file = Path(data_file).stem + "_documentation_perplexity.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(documentation)
        print(f"\n✓ Documentation saved to: {output_file}")
        
        # Show available models
        print("\nAvailable Perplexity models (Chat Completions API):")
        print("  - sonar-pro (default, best for web-grounded conversations)")
        print("  - sonar (lightweight, faster)")
        print("  - sonar-reasoning (real-time reasoning with search)")
        print("  - sonar-reasoning-pro (powered by DeepSeek-R1)")
        print("  - sonar-deep-research (long-form research)")
        
    except ImportError as e:
        print(f"\n✗ Error: Missing dependencies. {e}")
        print("Install with: pip install openai")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        if "401" in str(e) or "unauthorized" in str(e).lower():
            print("\nThis might be an authentication error.")
            print("Check that your PERPLEXITY_API_KEY is correct and has sufficient credits.")


def example_integration():
    """Example 8: Integration with other IterableData operations."""
    print("\n" + "=" * 70)
    print("Example 8: Integration with Schema Inference")
    print("=" * 70)
    
    if len(sys.argv) > 1:
        data_file = sys.argv[1]
    else:
        return
    
    if not os.path.exists(data_file):
        return
    
    print(f"\nAnalyzing dataset: {data_file}")
    
    try:
        from iterable.ops import schema, stats
        
        # Infer schema first
        print("\n1. Inferring schema...")
        schema_info = schema.infer(data_file, detect_constraints=True)
        print(f"   ✓ Found {len(schema_info.get('fields', {}))} fields")
        
        # Compute basic stats
        print("\n2. Computing statistics...")
        stats_info = stats.compute(data_file)
        print(f"   ✓ Row count: {stats_info.get('row_count', 'N/A')}")
        
        # Generate documentation (will use schema internally)
        print("\n3. Generating AI documentation...")
        documentation = doc.generate(
            data_file,
            provider="openai",
            model="gpt-4o",  # Latest GPT-4o model
            include_schema=True,  # Uses schema.infer() internally
            sample_size=5
        )
        
        output_file = Path(data_file).stem + "_documentation_integrated.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(documentation)
        print(f"\n✓ Integrated documentation saved to: {output_file}")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")


def example_metadata_extraction():
    """Example 9: Extract structured metadata from dataset."""
    print("\n" + "=" * 70)
    print("Example 9: Structured Metadata Extraction")
    print("=" * 70)
    
    if len(sys.argv) > 1:
        data_file = sys.argv[1]
    else:
        return
    
    if not os.path.exists(data_file):
        return
    
    print(f"\nGenerating documentation with metadata extraction for: {data_file}")
    print("Features:")
    print("  - Keywords extraction")
    print("  - Geographic coverage detection")
    print("  - Temporal coverage detection")
    print("  - Language detection")
    print("  - Data theme classification")
    
    try:
        # Generate JSON documentation with metadata
        result = doc.generate(
            data_file,
            provider="openai",
            model="gpt-4o-mini",
            format="json",
            include_metadata=True,  # Enable metadata extraction
            sample_size=10  # More samples for better metadata
        )
        
        print("\n" + "-" * 70)
        print("Extracted Metadata:")
        print("-" * 70)
        
        metadata = result.get("metadata", {})
        if metadata:
            if metadata.get("keywords"):
                print(f"\nKeywords: {', '.join(metadata['keywords'][:10])}")
            
            if metadata.get("geographic_coverage"):
                geo = metadata["geographic_coverage"]
                if geo.get("countries"):
                    print(f"\nCountries: {', '.join(geo['countries'][:5])}")
                if geo.get("regions"):
                    print(f"Regions: {', '.join(geo['regions'][:5])}")
                if geo.get("coordinates_present"):
                    print("Coordinates: Present")
            
            if metadata.get("temporal_coverage"):
                temp = metadata["temporal_coverage"]
                print(f"\nTemporal Coverage:")
                print(f"  Start: {temp.get('start')}")
                print(f"  End: {temp.get('end')}")
                print(f"  Granularity: {temp.get('granularity')}")
            
            if metadata.get("languages"):
                print(f"\nLanguages:")
                for lang in metadata["languages"]:
                    print(f"  {lang.get('code')}: {lang.get('confidence', 0):.2%}")
            
            if metadata.get("data_theme"):
                theme = metadata["data_theme"]
                print(f"\nData Theme: {theme.get('label')}")
                if theme.get("uri"):
                    print(f"  URI: {theme['uri']}")
        else:
            print("No metadata extracted (may require more sample data)")
        
        # Save full result
        output_file = Path(data_file).stem + "_documentation_with_metadata.json"
        import json
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\n✓ Full documentation with metadata saved to: {output_file}")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")


def example_field_descriptions():
    """Example 10: Generate field-level descriptions."""
    print("\n" + "=" * 70)
    print("Example 10: Field-Level Descriptions")
    print("=" * 70)
    
    if len(sys.argv) > 1:
        data_file = sys.argv[1]
    else:
        return
    
    if not os.path.exists(data_file):
        return
    
    print(f"\nGenerating field-level descriptions for: {data_file}")
    print("This will generate individual AI descriptions for each field.")
    
    try:
        # Generate documentation with field descriptions
        result = doc.generate(
            data_file,
            provider="openai",
            model="gpt-4o-mini",
            format="json",
            include_field_descriptions=True,  # Enable field descriptions
            language="English"
        )
        
        print("\n" + "-" * 70)
        print("Field Descriptions:")
        print("-" * 70)
        
        field_descriptions = result.get("field_descriptions", {})
        if field_descriptions:
            for field, description in field_descriptions.items():
                print(f"\n{field}:")
                print(f"  {description}")
        else:
            print("No field descriptions generated")
        
        # Save full result
        output_file = Path(data_file).stem + "_documentation_with_fields.json"
        import json
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\n✓ Documentation with field descriptions saved to: {output_file}")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")


def example_semantic_types_pii():
    """Example 11: Semantic types and PII detection."""
    print("\n" + "=" * 70)
    print("Example 11: Semantic Types and PII Detection")
    print("=" * 70)
    
    if len(sys.argv) > 1:
        data_file = sys.argv[1]
    else:
        return
    
    if not os.path.exists(data_file):
        return
    
    print(f"\nDetecting semantic types and PII for: {data_file}")
    print("Note: Requires Metacrafter CLI tool to be installed")
    print("  Install from: https://github.com/metacrafter/metacrafter")
    
    try:
        # Generate documentation with semantic types and PII detection
        result = doc.generate(
            data_file,
            provider="openai",
            model="gpt-4o-mini",
            format="json",
            semantic_types=True,  # Enable semantic type detection
            pii_detect=True,  # Enable PII detection
            pii_mask_samples=True,  # Mask PII in sample data
            sample_size=5
        )
        
        print("\n" + "-" * 70)
        print("Semantic Types:")
        print("-" * 70)
        
        semantic_types = result.get("semantic_types", {})
        if semantic_types:
            for field, types in semantic_types.items():
                if types:
                    type_names = [t.get("type", "") for t in types]
                    print(f"\n{field}: {', '.join(type_names)}")
        else:
            print("No semantic types detected (Metacrafter may not be available)")
        
        print("\n" + "-" * 70)
        print("PII Fields:")
        print("-" * 70)
        
        pii_fields = result.get("pii_fields", [])
        if pii_fields:
            for pii_field in pii_fields:
                print(f"\n{pii_field.get('field')}:")
                print(f"  Type: {pii_field.get('type', 'Unknown')}")
                if pii_field.get("confidence"):
                    print(f"  Confidence: {pii_field['confidence']}")
        else:
            print("No PII fields detected")
        
        # Show masked samples
        if pii_mask_samples and pii_fields:
            print("\n" + "-" * 70)
            print("Sample Data (PII Masked):")
            print("-" * 70)
            samples = result.get("samples", [])
            import json
            print(json.dumps(samples[:3], indent=2, default=str))
        
        # Save full result
        output_file = Path(data_file).stem + "_documentation_with_semantic.json"
        import json
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\n✓ Documentation with semantic types saved to: {output_file}")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")


def example_yaml_text_formats():
    """Example 12: YAML and text output formats."""
    print("\n" + "=" * 70)
    print("Example 12: YAML and Text Output Formats")
    print("=" * 70)
    
    if len(sys.argv) > 1:
        data_file = sys.argv[1]
    else:
        return
    
    if not os.path.exists(data_file):
        return
    
    print(f"\nGenerating documentation in YAML and text formats for: {data_file}")
    
    try:
        # Generate YAML documentation
        print("\n1. Generating YAML format...")
        yaml_docs = doc.generate(
            data_file,
            provider="openai",
            model="gpt-4o-mini",
            format="yaml",
            include_metadata=True
        )
        
        output_file_yaml = Path(data_file).stem + "_documentation.yaml"
        with open(output_file_yaml, "w", encoding="utf-8") as f:
            f.write(yaml_docs)
        print(f"   ✓ YAML documentation saved to: {output_file_yaml}")
        
        # Generate text documentation
        print("\n2. Generating text format...")
        text_docs = doc.generate(
            data_file,
            provider="openai",
            model="gpt-4o-mini",
            format="text"
        )
        
        output_file_text = Path(data_file).stem + "_documentation.txt"
        with open(output_file_text, "w", encoding="utf-8") as f:
            f.write(text_docs)
        print(f"   ✓ Text documentation saved to: {output_file_text}")
        
        # Show preview
        print("\n" + "-" * 70)
        print("Text Format Preview (first 300 chars):")
        print("-" * 70)
        print(text_docs[:300] + "..." if len(text_docs) > 300 else text_docs)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")


def example_statistics_integration():
    """Example 13: Statistics integration."""
    print("\n" + "=" * 70)
    print("Example 13: Statistics Integration")
    print("=" * 70)
    
    if len(sys.argv) > 1:
        data_file = sys.argv[1]
    else:
        return
    
    if not os.path.exists(data_file):
        return
    
    print(f"\nGenerating documentation with statistics for: {data_file}")
    
    try:
        # Generate documentation with statistics
        result = doc.generate(
            data_file,
            provider="openai",
            model="gpt-4o-mini",
            format="json",
            include_statistics=True,  # Enable statistics
            sample_size=10
        )
        
        print("\n" + "-" * 70)
        print("Statistics:")
        print("-" * 70)
        
        statistics = result.get("statistics", {})
        if statistics:
            for field, stats in list(statistics.items())[:10]:
                print(f"\n{field}:")
                if stats.get("unique_count") is not None:
                    print(f"  Unique values: {stats['unique_count']}")
                if stats.get("count") is not None:
                    print(f"  Total count: {stats['count']}")
                if stats.get("null_count") is not None:
                    print(f"  Null values: {stats['null_count']}")
                if stats.get("min") is not None:
                    print(f"  Min: {stats['min']}")
                if stats.get("max") is not None:
                    print(f"  Max: {stats['max']}")
                if stats.get("mean") is not None:
                    print(f"  Mean: {stats['mean']:.2f}")
        else:
            print("No statistics available")
        
        # Save full result
        output_file = Path(data_file).stem + "_documentation_with_stats.json"
        import json
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\n✓ Documentation with statistics saved to: {output_file}")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")


def example_multilingual():
    """Example 14: Multilingual documentation generation."""
    print("\n" + "=" * 70)
    print("Example 14: Multilingual Documentation")
    print("=" * 70)
    
    if len(sys.argv) > 1:
        data_file = sys.argv[1]
    else:
        return
    
    if not os.path.exists(data_file):
        return
    
    print(f"\nGenerating documentation in different languages for: {data_file}")
    
    languages = ["English", "Spanish", "French", "German"]
    
    try:
        for lang in languages:
            print(f"\nGenerating {lang} documentation...")
            documentation = doc.generate(
                data_file,
                provider="openai",
                model="gpt-4o-mini",
                format="markdown",
                language=lang,
                include_metadata=True,
                include_field_descriptions=True
            )
            
            lang_code = lang.lower()[:2]
            output_file = Path(data_file).stem + f"_documentation_{lang_code}.md"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(documentation)
            print(f"   ✓ {lang} documentation saved to: {output_file}")
        
        print("\n✓ Multilingual documentation generation complete!")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")


def example_comprehensive():
    """Example 15: Comprehensive documentation with all features."""
    print("\n" + "=" * 70)
    print("Example 15: Comprehensive Documentation (All Features)")
    print("=" * 70)
    
    if len(sys.argv) > 1:
        data_file = sys.argv[1]
    else:
        return
    
    if not os.path.exists(data_file):
        return
    
    print(f"\nGenerating comprehensive documentation for: {data_file}")
    print("Features enabled:")
    print("  ✓ Schema inference")
    print("  ✓ Sample data")
    print("  ✓ Metadata extraction")
    print("  ✓ Field descriptions")
    print("  ✓ Statistics")
    print("  ✓ Semantic types (if Metacrafter available)")
    print("  ✓ PII detection (if Metacrafter available)")
    
    try:
        # Generate comprehensive documentation
        result = doc.generate(
            data_file,
            provider="openai",
            model="gpt-4o-mini",
            format="json",
            include_schema=True,
            include_samples=True,
            sample_size=10,
            include_metadata=True,
            include_field_descriptions=True,
            include_statistics=True,
            semantic_types=True,  # Will skip if Metacrafter unavailable
            pii_detect=True,  # Will skip if Metacrafter unavailable
            pii_mask_samples=True,
            language="English"
        )
        
        print("\n" + "-" * 70)
        print("Documentation Summary:")
        print("-" * 70)
        
        print(f"\nDocumentation length: {len(result.get('documentation', ''))} characters")
        
        if result.get("schema"):
            schema_fields = result["schema"].get("fields", {})
            print(f"Schema fields: {len(schema_fields)}")
        
        if result.get("samples"):
            print(f"Sample records: {len(result['samples'])}")
        
        if result.get("metadata"):
            metadata = result["metadata"]
            print(f"\nMetadata:")
            if metadata.get("keywords"):
                print(f"  Keywords: {len(metadata['keywords'])}")
            if metadata.get("geographic_coverage"):
                print(f"  Geographic coverage: Yes")
            if metadata.get("temporal_coverage"):
                print(f"  Temporal coverage: Yes")
            if metadata.get("languages"):
                print(f"  Languages detected: {len(metadata['languages'])}")
            if metadata.get("data_theme"):
                print(f"  Data theme: {metadata['data_theme'].get('label')}")
        
        if result.get("field_descriptions"):
            print(f"\nField descriptions: {len(result['field_descriptions'])}")
        
        if result.get("statistics"):
            print(f"\nStatistics: {len(result['statistics'])} fields")
        
        if result.get("semantic_types"):
            semantic_count = sum(len(types) for types in result["semantic_types"].values())
            print(f"\nSemantic types: {semantic_count} annotations")
        
        if result.get("pii_fields"):
            print(f"\nPII fields detected: {len(result['pii_fields'])}")
        
        if result.get("usage"):
            usage = result["usage"]
            print(f"\nToken usage:")
            print(f"  Prompt tokens: {usage.get('prompt_tokens', 'N/A')}")
            print(f"  Completion tokens: {usage.get('completion_tokens', 'N/A')}")
            print(f"  Total tokens: {usage.get('total_tokens', 'N/A')}")
        
        # Save comprehensive result
        output_file = Path(data_file).stem + "_documentation_comprehensive.json"
        import json
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\n✓ Comprehensive documentation saved to: {output_file}")
        
        # Also save markdown version
        markdown_docs = doc.generate(
            data_file,
            provider="openai",
            model="gpt-4o-mini",
            format="markdown",
            include_schema=True,
            include_samples=True,
            sample_size=10,
            include_metadata=True,
            include_field_descriptions=True,
            include_statistics=True,
            language="English"
        )
        
        output_file_md = Path(data_file).stem + "_documentation_comprehensive.md"
        with open(output_file_md, "w", encoding="utf-8") as f:
            f.write(markdown_docs)
        print(f"✓ Comprehensive markdown documentation saved to: {output_file_md}")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("IterableData AI Documentation Generation Examples")
    print("=" * 70)
    
    if len(sys.argv) < 2:
        print("\nUsage: python generate_documentation.py <data_file> [example_number]")
        print("\nExamples:")
        print("  python generate_documentation.py data.csv")
        print("  python generate_documentation.py data.csv 1")
        print("  python generate_documentation.py data.csv 2")
        print("\nExample numbers:")
        print("  1 - Basic markdown documentation with GPT-4o (default)")
        print("  2 - JSON format documentation")
        print("  3 - HTML format documentation")
        print("  4 - Customized documentation")
        print("  5 - Different LLM providers (tries LM Studio first)")
        print("  6 - LM Studio local example (free, no API key)")
        print("  7 - Perplexity provider (online model with web search)")
        print("  8 - Integration with schema inference")
        print("  9 - Structured metadata extraction")
        print("  10 - Field-level descriptions")
        print("  11 - Semantic types and PII detection")
        print("  12 - YAML and text output formats")
        print("  13 - Statistics integration")
        print("  14 - Multilingual documentation")
        print("  15 - Comprehensive documentation (all features)")
        print("\nPrerequisites:")
        print("  - Install AI dependencies: pip install openai")
        print("  - Option 1 (Recommended): Use LM Studio (local, free)")
        print("    - Install from https://lmstudio.ai")
        print("    - Load a model and start local server")
        print("  - Option 2: Set OpenAI API key: export OPENAI_API_KEY='sk-...'")
        print("    - Uses latest GPT-4o model")
        print("  - Option 3: Set Perplexity API key: export PERPLEXITY_API_KEY='pplx-...'")
        print("    - Get key from https://www.perplexity.ai/settings/api")
        return
    
    example_num = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    
    examples = {
        1: example_basic_markdown,
        2: example_json_format,
        3: example_html_format,
        4: example_customization,
        5: example_different_providers,
        6: example_lmstudio_local,
        7: example_perplexity,
        8: example_integration,
        9: example_metadata_extraction,
        10: example_field_descriptions,
        11: example_semantic_types_pii,
        12: example_yaml_text_formats,
        13: example_statistics_integration,
        14: example_multilingual,
        15: example_comprehensive,
    }
    
    if example_num in examples:
        examples[example_num]()
    else:
        print(f"Invalid example number: {example_num}")
        print("Valid examples: 1-15")


if __name__ == "__main__":
    main()
