#!/usr/bin/env python3
"""
Test script to demonstrate the performance improvements of the optimized focal length analysis.
"""

import sys
import time
from pathlib import Path

from focal_length import analyze_focal_lengths_batched, analyze_focal_lengths_parallel


def test_performance(folder_path):
    """Test both methods and compare performance."""

    print(f"Testing focal length analysis on: {folder_path}")
    print("=" * 60)

    # Test the optimized batched method (default settings)
    print("\n1. Testing OPTIMIZED method (batched with 4 threads, batch size 100):")
    print("-" * 70)
    start_time = time.time()
    try:
        result_optimized = analyze_focal_lengths_batched(
            folder_path, batch_size=100, max_workers=4
        )
        optimized_time = time.time() - start_time
        print(f"✓ OPTIMIZED method completed in {optimized_time:.2f} seconds")
        print(f"  - Found {result_optimized['total_images']} images")
        print(
            f"  - {result_optimized['images_with_focal_length']} had focal length data"
        )
        print(f"  - {len(set(result_optimized['focal_lengths']))} unique focal lengths")
    except Exception as e:
        print(f"✗ OPTIMIZED method failed: {e}")
        optimized_time = float("inf")
        result_optimized = None

    # Test the single-process method for comparison
    print("\n2. Testing SINGLE-PROCESS method (for comparison):")
    print("-" * 50)
    start_time = time.time()
    try:
        result_single = analyze_focal_lengths_parallel(folder_path, max_workers=4)
        single_time = time.time() - start_time
        print(f"✓ SINGLE-PROCESS method completed in {single_time:.2f} seconds")
        print(f"  - Found {result_single['total_images']} images")
        print(f"  - {result_single['images_with_focal_length']} had focal length data")
        print(f"  - {len(set(result_single['focal_lengths']))} unique focal lengths")
    except Exception as e:
        print(f"✗ SINGLE-PROCESS method failed: {e}")
        single_time = float("inf")
        result_single = None

    # Performance comparison
    print("\n3. Performance Comparison:")
    print("-" * 50)
    if optimized_time != float("inf") and single_time != float("inf"):
        if optimized_time < single_time:
            improvement = ((single_time - optimized_time) / single_time) * 100
            print(
                f"✓ OPTIMIZED method is {improvement:.1f}% faster than SINGLE-PROCESS method"
            )
        else:
            improvement = ((optimized_time - single_time) / optimized_time) * 100
            print(
                f"✓ SINGLE-PROCESS method is {improvement:.1f}% faster than OPTIMIZED method"
            )

        print("\nRecommendation:")
        if optimized_time < single_time:
            print("  OPTIMIZED method is recommended for this folder size")
        else:
            print("  SINGLE-PROCESS method might be better for this folder size")
    else:
        print("✗ Could not compare performance due to errors")

    # Show focal length distribution if available
    if result_optimized and result_optimized["focal_lengths"]:
        print("\n4. Focal Length Distribution:")
        print("-" * 50)
        from collections import Counter

        counter = Counter(result_optimized["focal_lengths"])
        for focal_length, count in sorted(counter.items()):
            print(f"  {focal_length}mm: {count} images")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_performance.py <folder_path>")
        print("\nExample: python test_performance.py /path/to/your/images")
        sys.exit(1)

    folder_path = sys.argv[1]

    if not Path(folder_path).exists():
        print(f"Error: Folder '{folder_path}' does not exist")
        sys.exit(1)

    test_performance(folder_path)
