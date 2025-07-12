import concurrent.futures
import json
import subprocess
import time
from collections import Counter
from pathlib import Path


def analyze_focal_lengths_parallel(folder, max_workers=4):
    """
    Analyze focal lengths in a folder and return the data.
    Optimized version that uses a single exiftool process and better threading.

    Args:
        folder (str): Path to the folder containing images
        max_workers (int): Number of parallel workers for processing results

    Returns:
        dict: Dictionary containing focal length data and statistics
    """
    folder_path = Path(folder)

    # Collect all image files
    image_files = []
    for ext in [
        "*.nef",
        "*.NEF",
        "*.jpg",
        "*.JPG",
        "*.jpeg",
        "*.JPEG",
        "*.png",
        "*.PNG",
        "*.heic",
        "*.HEIC",
        "*.heif",
        "*.HEIF",
    ]:
        image_files.extend(folder_path.glob(ext))

    if not image_files:
        print("No image files found in the specified folder.")
        return {
            "focal_lengths": [],
            "counter": Counter(),
            "total_images": 0,
            "images_with_focal_length": 0,
        }

    # Convert to string paths for exiftool
    file_paths = [str(f) for f in image_files]

    print(f"Found {len(file_paths)} images. Starting analysis...")

    # Use a single exiftool process for all files
    # This is much faster than multiple subprocess calls
    args = [
        "exiftool",
        "-fast2",  # Fast mode
        "-j",  # JSON output
        "-n",  # Numeric output
        "-FocalLength",
        "-q",  # Quiet mode
        "-m",  # Minor warnings only
    ] + file_paths

    try:
        print("Running exiftool...")
        start_time = time.time()

        # Run exiftool once for all files
        result = subprocess.run(
            args, capture_output=True, check=True, text=True, bufsize=65536
        )

        exiftool_time = time.time() - start_time
        print(f"Exiftool completed in {exiftool_time:.2f} seconds")

        # Parse JSON output
        print("Parsing results...")
        parse_start = time.time()
        metadata = json.loads(result.stdout)
        parse_time = time.time() - parse_start
        print(f"JSON parsing completed in {parse_time:.2f} seconds")

        # Extract focal lengths using threading for better performance
        def process_metadata_chunk(chunk):
            """Process a chunk of metadata to extract focal lengths."""
            focal_lengths = []
            for item in chunk:
                if item.get("FocalLength"):
                    focal_lengths.append(item["FocalLength"])
            return focal_lengths

        # Split metadata into chunks for parallel processing
        chunk_size = max(1, len(metadata) // max_workers)
        metadata_chunks = [
            metadata[i : i + chunk_size] for i in range(0, len(metadata), chunk_size)
        ]

        print(
            f"Processing {len(metadata)} metadata entries with {max_workers} workers..."
        )
        process_start = time.time()

        all_focal_lengths = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(process_metadata_chunk, chunk)
                for chunk in metadata_chunks
            ]

            for future in concurrent.futures.as_completed(futures):
                focal_lengths = future.result()
                all_focal_lengths.extend(focal_lengths)

        process_time = time.time() - process_start
        print(f"Parallel processing completed in {process_time:.2f} seconds")

        # Count and return results
        counter = Counter(all_focal_lengths)

        total_time = time.time() - start_time
        print(f"Total analysis time: {total_time:.2f} seconds")
        print(f"Found {len(all_focal_lengths)} images with focal length data")

        return {
            "focal_lengths": all_focal_lengths,
            "counter": counter,
            "total_images": len(image_files),
            "images_with_focal_length": len(all_focal_lengths),
        }

    except subprocess.CalledProcessError as e:
        print(f"Exiftool error: {e}")
        print(f"Error output: {e.stderr}")
        return {
            "focal_lengths": [],
            "counter": Counter(),
            "total_images": len(image_files),
            "images_with_focal_length": 0,
        }
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        return {
            "focal_lengths": [],
            "counter": Counter(),
            "total_images": len(image_files),
            "images_with_focal_length": 0,
        }
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {
            "focal_lengths": [],
            "counter": Counter(),
            "total_images": len(image_files),
            "images_with_focal_length": 0,
        }


# Alternative version for very large folders - processes files in batches
def analyze_focal_lengths_batched(folder, batch_size=1000, max_workers=4):
    """
    Analyze focal lengths in very large folders by processing files in batches.
    This prevents memory issues with extremely large folders.

    Args:
        folder (str): Path to the folder containing images
        batch_size (int): Number of files to process in each batch
        max_workers (int): Number of parallel workers

    Returns:
        dict: Dictionary containing focal length data and statistics
    """
    folder_path = Path(folder)

    # Collect all image files
    image_files = []
    for ext in [
        "*.nef",
        "*.NEF",
        "*.jpg",
        "*.JPG",
        "*.jpeg",
        "*.JPEG",
        "*.png",
        "*.PNG",
        "*.heic",
        "*.HEIC",
        "*.heif",
        "*.HEIF",
    ]:
        image_files.extend(folder_path.glob(ext))

    if not image_files:
        print("No image files found in the specified folder.")
        return {
            "focal_lengths": [],
            "counter": Counter(),
            "total_images": 0,
            "images_with_focal_length": 0,
        }

    # Convert to string paths
    file_paths = [str(f) for f in image_files]

    print(f"Found {len(file_paths)} images. Processing in batches of {batch_size}...")

    def process_batch(batch_paths):
        """Process a batch of files with exiftool."""
        args = [
            "exiftool",
            "-fast2",
            "-j",
            "-n",
            "-FocalLength",
            "-q",
            "-m",
        ] + batch_paths

        try:
            result = subprocess.run(
                args, capture_output=True, check=True, text=True, bufsize=65536
            )
            metadata = json.loads(result.stdout)
            return [item["FocalLength"] for item in metadata if item.get("FocalLength")]
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            return []

    # Split files into batches
    batches = [
        file_paths[i : i + batch_size] for i in range(0, len(file_paths), batch_size)
    ]

    print(f"Created {len(batches)} batches")

    all_focal_lengths = []
    start_time = time.time()

    # Process batches in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_batch, batch) for batch in batches]

        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            focal_lengths = future.result()
            all_focal_lengths.extend(focal_lengths)

            # Progress update
            if (i + 1) % max(1, len(batches) // 10) == 0:
                print(f"Processed {i + 1}/{len(batches)} batches...")

    total_time = time.time() - start_time
    print(f"Total analysis time: {total_time:.2f} seconds")
    print(f"Found {len(all_focal_lengths)} images with focal length data")

    # Count and return results
    counter = Counter(all_focal_lengths)

    return {
        "focal_lengths": all_focal_lengths,
        "counter": counter,
        "total_images": len(image_files),
        "images_with_focal_length": len(all_focal_lengths),
    }


# For testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        folder_path = sys.argv[1]
        print(f"Testing focal length analysis on: {folder_path}")

        start_time = time.time()
        result = analyze_focal_lengths_parallel(folder_path, max_workers=4)
        end_time = time.time()

        print(f"Time taken: {end_time - start_time:.2f} seconds")
        print(f"Results: {result}")
    else:
        print("Usage: python focal_length.py <folder_path>")
