# How to Add New Properties to Saban Realty

This guide documents the step-by-step process for adding new property listings to the website.

---

## Overview

The website uses a single JSON file (`data/listings.json`) as its database. Property images are hosted on Cloudflare R2. To add a new property, you need to:

1. Prepare property photos
2. Upload photos to Cloudflare R2
3. Add the property entry to `data/listings.json`
4. Push changes to GitHub (auto-deploys via GitHub Pages)

---

## CSV Spreadsheet to JSON Field Mapping

Your Airtable/spreadsheet uses these columns. Here's how each maps to the JSON:

| Spreadsheet Column     | JSON Field         | Notes                                           |
|------------------------|--------------------|-------------------------------------------------|
| Listing Name           | `title`            | Exact property name                             |
| Listing Name           | `id`               | Converted to lowercase-slug (see below)         |
| Location               | `location`         | e.g. "Zions Hill, Saba"                         |
| Listing Description    | `description`      | Full property description text                  |
| Property Type          | `type`             | Must be: `villa`, `cottage`, or `land`          |
| Thumbnail              | `images[0]`        | First image in the images array (auto-used)     |
| Gallery                | `images`           | All photo URLs as an array                      |
| Price                  | `price`            | Numeric only, no `$` or commas (e.g. `450000`)  |
| Price                  | `priceFormatted`   | Display string (e.g. `"$450,000"` or `"SOLD"`)  |
| Bedrooms               | `bedrooms`         | Number (e.g. `3`)                               |
| *(not in spreadsheet)* | `bathrooms`        | Number - must be added manually                 |
| Youtube link           | `youtubeLink`      | Full YouTube URL (optional)                     |
| Availability Status    | `status`           | Must be: `for-sale` or `sold`                   |

---

## Step-by-Step Process

### Step 1: Prepare Property Photos

1. Collect all property photos
2. Create a folder named after the property on your desktop:
   ```
   /Users/nathanaeljohnson/Desktop/R_E_V/real-estate-images/Listings/Property Name Here/
   ```
   - For rentals, use the `Rentals/` subfolder instead of `Listings/`
3. Name photos with a numeric prefix to control order:
   ```
   1main-photo.jpg
   2kitchen.jpg
   3bedroom.jpg
   4bathroom.jpg
   5exterior.jpg
   ```
   The first image (lowest number) becomes the thumbnail on listing pages.

### Step 2: Upload Photos to Cloudflare R2

Run the upload script from the project root:

```bash
cd /Users/nathanaeljohnson/GitHub/sabanrealty
bash scripts/upload-to-r2.sh
```

This script will:
- Read all folders in your `Listings/` and `Rentals/` directories
- Convert folder names to URL slugs (lowercase, hyphens, no special chars)
- Upload each image to R2 under `listings/{slug}/` or `rentals/{slug}/`

**After uploading**, your image URLs will follow this pattern:
```
https://pub-78b56158b83942189fa28a4d5939bb79.r2.dev/listings/{slug}/{filename}
```

**Example:** A property named "Ocean View Cottage" with a photo `1front.jpg`:
```
https://pub-78b56158b83942189fa28a4d5939bb79.r2.dev/listings/ocean-view-cottage/1front.jpg
```

### Step 3: Create the Property ID (Slug)

Convert the property name to a URL-friendly slug:
- Lowercase everything
- Replace spaces with hyphens
- Remove special characters

| Property Name               | Slug (ID)                  |
|-----------------------------|----------------------------|
| Hidden Treasure Villa       | `hidden-treasure-villa`    |
| STATIA Poolhouse            | `statia-poolhouse`         |
| Ocean View Cottage          | `ocean-view-cottage`       |

### Step 4: Add Entry to listings.json

Open `data/listings.json` and add a new object to the `"properties"` array (or `"rentals"` array for vacation rentals).

#### Template for a Property (For Sale):

```json
{
  "id": "your-property-slug",
  "title": "Your Property Name",
  "location": "Area, Island",
  "price": 450000,
  "priceFormatted": "$450,000",
  "status": "for-sale",
  "type": "villa",
  "bedrooms": 3,
  "bathrooms": 2,
  "description": "Full property description here. Paste from the Listing Description column in the spreadsheet.",
  "images": [
    "https://pub-78b56158b83942189fa28a4d5939bb79.r2.dev/listings/your-property-slug/1photo.jpg",
    "https://pub-78b56158b83942189fa28a4d5939bb79.r2.dev/listings/your-property-slug/2photo.jpg",
    "https://pub-78b56158b83942189fa28a4d5939bb79.r2.dev/listings/your-property-slug/3photo.jpg"
  ]
}
```

#### Template for a Rental:

```json
{
  "id": "your-rental-slug",
  "title": "Your Rental Name",
  "location": "Area, Island",
  "nightlyRate": 295,
  "nightlyRateFormatted": "$295/night",
  "status": "available",
  "type": "villa",
  "bedrooms": 3,
  "bathrooms": 2,
  "maxGuests": 6,
  "description": "Full property description here.",
  "features": [
    "Ocean Views",
    "Private Pool",
    "Fully Furnished",
    "WiFi"
  ],
  "images": [
    "https://pub-78b56158b83942189fa28a4d5939bb79.r2.dev/rentals/your-rental-slug/1photo.jpg",
    "https://pub-78b56158b83942189fa28a4d5939bb79.r2.dev/rentals/your-rental-slug/2photo.jpg"
  ]
}
```

### Step 5: Validate the JSON

Before pushing, make sure your JSON is valid. You can check with:

```bash
python3 -c "import json; json.load(open('data/listings.json')); print('JSON is valid!')"
```

Common mistakes:
- Missing comma between properties
- Trailing comma after the last property in the array
- Unescaped quotes inside the description (use `\"` or smart quotes)
- Missing closing brackets `]` or `}`

### Step 6: Deploy

Commit and push to GitHub:

```bash
cd /Users/nathanaeljohnson/GitHub/sabanrealty
git add data/listings.json
git commit -m "Add new listing: Property Name Here"
git push
```

The site deploys automatically via GitHub Pages. Changes are typically live within 1-2 minutes.

---

## Updating an Existing Property

### Mark a Property as Sold
Change these two fields in the property's JSON entry:
```json
"price": 0,
"priceFormatted": "SOLD",
"status": "sold",
```

### Update the Price
Change both `price` (numeric) and `priceFormatted` (display string):
```json
"price": 525000,
"priceFormatted": "$525,000",
```

### Add More Photos
Append new image URLs to the `"images"` array.

### Remove a Property
Delete the entire object `{ ... }` for that property from the array. Make sure to also remove the trailing comma from the previous entry if it was the last one.

---

## Valid Values Reference

| Field       | Accepted Values                           |
|-------------|-------------------------------------------|
| `status`    | `"for-sale"`, `"sold"`                    |
| `type`      | `"villa"`, `"cottage"`, `"land"`          |
| `bedrooms`  | Any number (`1`, `2`, `3`, `4`, etc.)     |
| `bathrooms` | Any number (`1`, `2`, `3`, etc.)          |
| `price`     | Number with no formatting (`450000`)      |

---

## Quick Checklist for Adding a Property

- [ ] Photos collected and numbered (1photo.jpg, 2photo.jpg, etc.)
- [ ] Photos placed in `Desktop/R_E_V/real-estate-images/Listings/Property Name/`
- [ ] Ran `bash scripts/upload-to-r2.sh` to upload to R2
- [ ] Created slug/ID from property name (lowercase, hyphens)
- [ ] Added JSON entry to `data/listings.json` with all fields
- [ ] Verified JSON is valid (`python3 -c "import json; ..."`)
- [ ] Committed and pushed to GitHub
- [ ] Verified property appears on the live site

---

## File Locations

| What                  | Where                                                              |
|-----------------------|--------------------------------------------------------------------|
| Property data         | `data/listings.json`                                               |
| Image upload script   | `scripts/upload-to-r2.sh`                                         |
| Local images folder   | `/Users/nathanaeljohnson/Desktop/R_E_V/real-estate-images/`       |
| R2 base URL           | `https://pub-78b56158b83942189fa28a4d5939bb79.r2.dev/`            |
| Buy page              | `buy.html`                                                         |
| Rent page             | `rent.html`                                                        |
| Property detail page  | `property-detail.html`                                             |
| CSS styles            | `css/styles.css`                                                   |
| JS logic              | `js/main.js`                                                       |
