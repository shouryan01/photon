# photon

![cropped](https://github.com/user-attachments/assets/2d3db094-76fe-4fe4-88e7-0a8f1a8b294f)

Utilities for Photographers

## Features

- Add borders to images.
- Select border color and width for each side.
- Save and load border settings for difference workflows.
- Batch apply edits to photos.
- **Focal Length Analysis**: Analyze focal length distribution in your photo collections with optimized performance.

## Performance Optimizations

### Focal Length Analysis Speed Improvements

The focal length analysis feature has been significantly optimized for speed:

#### Key Optimizations:

1. **Single exiftool Process**: Instead of multiple subprocess calls, we now use a single exiftool process for all files, dramatically reducing overhead.
2. **Efficient Threading**: Parallel processing of metadata parsing using ThreadPoolExecutor.
3. **Two Analysis Methods**:
   - **Fast Method**: Single exiftool process for folders with up to ~10,000 images
   - **Batched Method**: For very large folders, processes files in configurable batches

#### Optimized Defaults:

- **Method**: Always uses batched processing for optimal performance
- **Thread Count**: 4 parallel workers
- **Batch Size**: 100 files per batch

#### Expected Performance Gains:

- **Small folders (< 1,000 images)**: 3-5x faster
- **Medium folders (1,000-10,000 images)**: 5-10x faster
- **Large folders (> 10,000 images)**: 10-20x faster

#### Testing Performance:

```bash
python test_performance.py /path/to/your/images
```

## Coming Soon

- Batch rename images
- EXIF data scrubber
- Presets for crops
- "Polaroid" preset images.

## Screenshots

<img width="1203" alt="image" src="https://github.com/user-attachments/assets/5c5f737c-2125-445e-80a1-8f315108b5f6" />
