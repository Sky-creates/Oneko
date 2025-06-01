#!/bin/bash

# Configuration variables
THEME="orange_cat"         # Change this to create different themes
SOURCE_DIR="gif"           # Source directory containing .gif files
OUTPUT_DIR="theme_${THEME}" # Output directory

# Colors
ORANGE="#000000"           # edge color
DEEP_GOLD="#FED883"        # body color

echo "Starting batch processing with theme: $THEME"
echo "Source directory: $SOURCE_DIR"
echo "Output directory: $OUTPUT_DIR"
echo "Orange color: $ORANGE"
echo "Deep gold color: $DEEP_GOLD"
echo ""

# Check if source directory exists
if [ ! -d "$SOURCE_DIR" ]; then
    echo "Error: Source directory '$SOURCE_DIR' does not exist!"
    exit 1
fi

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Counter for processed files
count=0

# Process all .gif files in source directory (case insensitive)
for file in "$SOURCE_DIR"/*.gif "$SOURCE_DIR"/*.GIF; do
    # Check if file exists (handles case where no files match pattern)
    if [ ! -f "$file" ]; then
        continue
    fi
    
    # Get just the filename without path
    filename=$(basename "$file")
    
    echo "Processing: $filename"
    
    # Apply edge thinning and color transformations using magick
    magick "$file" \
        -fuzz 8% -fill "$ORANGE" -opaque black \
        -fuzz 12% -fill "$DEEP_GOLD" -opaque white \
        "$OUTPUT_DIR/$filename"
    
    if [ $? -eq 0 ]; then
        echo "✓ Successfully processed: $filename -> $OUTPUT_DIR/$filename"
        ((count++))
    else
        echo "✗ Error processing: $filename"
    fi
done

echo ""
echo "Batch processing complete!"
echo "Processed $count files"
echo "Output files are in the '$OUTPUT_DIR' folder"