#!/usr/bin/env python3
"""
Test script to demonstrate the performance improvements of the optimized focal length analysis.
"""

import sys
import time
from pathlib import Path

from focal_length import analyze_focal_lengths_batched, analyze_focal_lengths_parallel
from focal_length import analyze_focal_lengths_batched, analyze_focal_lengths_parallel


def test_performance(folder_path):
    """Test both methods and compare performance."""

    print(f"Testing focal length analysis on: {folder_path}")
    print("=" * 60)

    # Test the optimized single-process method
    print("\n1. Testing FAST method (single exiftool process):")
    print("-" * 50)
    start_time = time.time()
    try:
        result_fast = analyze_focal_lengths_parallel(folder_path, max_workers=4)
        fast_time = time.time() - start_time
        print(f"✓ FAST method completed in {fast_time:.2f} seconds")
        print(f"  - Found {result_fast['total_images']} images")
        print(f"  - {result_fast['images_with_focal_length']} had focal length data")
        print(f"  - {len(set(result_fast['focal_lengths']))} unique focal lengths")
    except Exception as e:
        print(f"✗ FAST method failed: {e}")
        fast_time = float("inf")
        result_fast = None

    # Test the batched method
    print("\n2. Testing BATCHED method (for large folders):")
    print("-" * 50)
    start_time = time.time()
    try:
        result_batched = analyze_focal_lengths_batched(
            folder_path, batch_size=1000, max_workers=4
        )
        batched_time = time.time() - start_time
        print(f"✓ BATCHED method completed in {batched_time:.2f} seconds")
        print(f"  - Found {result_batched['total_images']} images")
        print(f"  - {result_batched['images_with_focal_length']} had focal length data")
        print(f"  - {len(set(result_batched['focal_lengths']))} unique focal lengths")
    except Exception as e:
        print(f"✗ BATCHED method failed: {e}")
        batched_time = float("inf")
        result_batched = None

    # Performance comparison
    print("\n3. Performance Comparison:")
    print("-" * 50)
    if fast_time != float("inf") and batched_time != float("inf"):
        if fast_time < batched_time:
            improvement = ((batched_time - fast_time) / batched_time) * 100
            print(f"✓ FAST method is {improvement:.1f}% faster than BATCHED method")
        else:
            improvement = ((fast_time - batched_time) / fast_time) * 100
            print(f"✓ BATCHED method is {improvement:.1f}% faster than FAST method")

        print("\nRecommendation:")
        if fast_time < batched_time:
            print("  Use FAST method for this folder size")
        else:
            print("  Use BATCHED method for this folder size")
    else:
        print("✗ Could not compare performance due to errors")

    # Show focal length distribution if available
    if result_fast and result_fast["focal_lengths"]:
        print("\n4. Focal Length Distribution (from FAST method):")
        print("-" * 50)
        from collections import Counter

        counter = Counter(result_fast["focal_lengths"])
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
