#!/bin/bash
# Upload real estate images to Cloudflare R2
# Images are organized by property folder

IMAGES_DIR="/Users/nathanaeljohnson/Desktop/R_E_V/real-estate-images"
BUCKET="sabanreality"

echo "Starting upload to Cloudflare R2 bucket: $BUCKET"
echo "=============================================="

# Upload Listings
echo ""
echo "Uploading Listings..."
echo "---------------------"

cd "$IMAGES_DIR/Listings"
for dir in */; do
    # Convert folder name to slug (lowercase, hyphens)
    folder_name="${dir%/}"
    slug=$(echo "$folder_name" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | tr -cd '[:alnum:]-')

    echo "Processing: $folder_name -> listings/$slug"

    for file in "$dir"*; do
        if [ -f "$file" ]; then
            filename=$(basename "$file")
            # Skip .DS_Store files
            if [[ "$filename" != .DS_Store ]]; then
                key="listings/$slug/$filename"
                echo "  Uploading: $key"
                wrangler r2 object put "$BUCKET/$key" --file "$file" 2>/dev/null
            fi
        fi
    done
done

# Upload Rentals
echo ""
echo "Uploading Rentals..."
echo "--------------------"

cd "$IMAGES_DIR/Rentals"
for dir in */; do
    # Convert folder name to slug (lowercase, hyphens)
    folder_name="${dir%/}"
    slug=$(echo "$folder_name" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | tr -cd '[:alnum:]-')

    echo "Processing: $folder_name -> rentals/$slug"

    for file in "$dir"*; do
        if [ -f "$file" ]; then
            filename=$(basename "$file")
            # Skip .DS_Store files
            if [[ "$filename" != .DS_Store ]]; then
                key="rentals/$slug/$filename"
                echo "  Uploading: $key"
                wrangler r2 object put "$BUCKET/$key" --file "$file" 2>/dev/null
            fi
        fi
    done
done

echo ""
echo "=============================================="
echo "Upload complete!"
echo ""
echo "Verify with: wrangler r2 object list $BUCKET | head -50"
