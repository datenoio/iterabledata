#!/usr/bin/env python3
"""Example: declarative conversion planning with iterable.ai.plan."""

from iterable.ai.plan import plan_conversion

if __name__ == "__main__":
    plan = plan_conversion("fixtures/2cols6rows.csv", "fixtures/out.parquet")
    print("Source format:", plan["source"]["format"])
    print("Target format:", plan["target"]["format"])
    print("Warnings:", plan["warnings"])
    print("Steps:")
    for step in plan["steps"]:
        print(f"  - {step['action']}: {step['detail']}")
