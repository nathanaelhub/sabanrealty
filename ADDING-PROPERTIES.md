# How to Add New Properties to Saban Realty

This guide documents the step-by-step process for adding new property listings to the website.

---

## Admin page (no terminal needed)

`https://sabanrealty.com/admin/` lets someone with the passphrase add a for-sale listing (photos, details, YouTube link) and make quick changes: price, under contract, sold, back on the market, hide, unhide. It goes live in a few minutes. Vacation rentals, and edits to an existing listing's photos or description, still use the manual steps below.

How it works:

1. `admin/index.html` shrinks each photo in the browser (max 1600 px JPEG, EXIF removed) and builds the description HTML.
2. The Cloudflare Worker in `scripts/admin-worker/` checks the passphrase, stores photos in R2 under `listings/<id>/` (it never overwrites a file), and sends the change to GitHub.
3. `.github/workflows/admin-publish.yml` runs `scripts/admin/apply_change.py`, which validates the change, edits `data/listings.json`, regenerates the listing pages and updates `sitemap.xml`. It then runs the static site checks, commits as "Admin: …", pushes, and mentions @nathanaelhub in a commit comment.

One-time setup:

```bash
cd scripts/admin-worker
npx wrangler login
npx wrangler deploy                        # prints the Worker address
npx wrangler secret put ADMIN_PASSPHRASE   # 16+ characters; four or more random words
npx wrangler secret put GITHUB_TOKEN       # fine-grained PAT, this repo only: Contents read/write, Actions read
```

Then put the Worker address in `WORKER_URL` near the top of the script in `admin/index.html`, and merge to `main` (the workflow only runs from the default branch).

Upkeep:

- **Change the passphrase:** `npx wrangler secret put ADMIN_PASSPHRASE`. Every device has to enter the new one.
- **GitHub token expiry:** fine-grained tokens expire. When publishing starts failing with "Could not reach the website publisher", create a new token and run `npx wrangler secret put GITHUB_TOKEN`.
- **A publish failed:** GitHub emails the failed "Admin publish" run. The admin page shows the reason when the change was refused (for example, hiding a listing that is on the homepage).
- **Undo a mistaken listing:** hide it from the admin page, then remove the entry by hand and delete its photos with `node scripts/r2-manage.js delete-folder listings/<id>`.
- **Test without publishing:** run the "Admin publish" workflow by hand with a JSON payload; it defaults to a dry run that prints the diff. Locally: `python3 scripts/admin/apply_change.py --payload change.json --skip-image-check`, and `python3 -m unittest scripts/admin/test_apply_change.py`.
- **Local page testing:** copy `.dev.vars.example` to `.dev.vars`, run `npx wrangler dev --port 8787 --local` in `scripts/admin-worker/` and `python3 -m http.server 8899` in the repo root, then open `http://localhost:8899/admin/`.

`apply_change.py` also works for manual adds: it does steps 4 to 5 below plus page generation and the sitemap in one go.

---

## Overview

The website uses a single JSON file (`data/listings.json`) as its database. Property images are hosted on Cloudflare R2. To add a new property, you need to:

1. Prepare property photos
2. Upload photos to Cloudflare R2
3. Add the property entry to `data/listings.json`
4. Run `python3 scripts/generate-listing-pages.py` and add the listing's `<url>` block to `sitemap.xml`
5. Push changes to GitHub (auto-deploys via GitHub Pages)

---

## CSV Spreadsheet to JSON Field Mapping

Your Airtable/spreadsheet uses these columns. Here's how each maps to the JSON:

| Spreadsheet Column     | JSON Field         | Notes                                           |
|------------------------|--------------------|-------------------------------------------------|
| Listing Name           | `title`            | Exact property name                             |
| Listing Name           | `id`               | Converted to lowercase-slug (see below)         |
| Location               | `location`         | e.g. "Zions Hill, Saba"                         |
| Listing Description    | `description`      | Full property description text                  |
| Property Type          | `type`             | Must be: `villa`, `cottage`, `land`, `commercial` |
| Thumbnail              | `images[0]`        | First image in the images array (auto-used)     |
| Gallery                | `images`           | All photo URLs as an array                      |
| Price                  | `price`            | Numeric only, no `$` or commas (e.g. `450000`)  |
| Price                  | `priceFormatted`   | Display string (e.g. `"$450,000"` or `"SOLD"`)  |
| Bedrooms               | `bedrooms`         | Number (e.g. `3`)                               |
| *(not in spreadsheet)* | `bathrooms`        | Number - must be added manually                 |
| Youtube link           | `videos`           | `[{"label": "Property Tour", "id": "<11-char YouTube id>", "uploadDate": "<ISO date from the watch page>"}]` (optional) |
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

Run the upload script from the project root (reads R2 credentials from `.env`):

```bash
cd /Users/nathanaeljohnson/GitHub/sabanrealty
node scripts/r2-manage.js upload <localPhotoDir> listings/<slug>   # rentals use rentals/<slug>
node scripts/r2-manage.js list listings/<slug>                    # verify the uploaded keys
```

This uploads every file in the folder to R2 under `listings/{slug}/` (or `rentals/{slug}/`).

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
  "description": "<h2>Your Property Name — Area, Island</h2>\n<p><strong>Location:</strong> Area, Island</p>\n<h3>Property Overview:</h3>\n<p>Description paragraphs as HTML.</p>",
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

### Step 6: Generate the page and update the sitemap

```bash
python3 scripts/generate-listing-pages.py     # writes properties/<slug>/index.html
```

Add the listing's `<url>` block to `sitemap.xml` with today's date as `lastmod` (priority 0.8 for sale, 0.5 sold, 0.7 rentals). Then check with `bash scripts/site-test/run.sh`.

### Step 7: Deploy

Commit and push to GitHub:

```bash
cd /Users/nathanaeljohnson/GitHub/sabanrealty
git add data/listings.json sitemap.xml properties/
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
| `type`      | `"villa"`, `"cottage"`, `"land"`, `"commercial"` |
| `bedrooms`  | Any number (`1`, `2`, `3`, `4`, etc.)     |
| `bathrooms` | Any number (`1`, `2`, `3`, etc.)          |
| `price`     | Number with no formatting (`450000`)      |

---

## Quick Checklist for Adding a Property

- [ ] Photos collected and numbered (1photo.jpg, 2photo.jpg, etc.)
- [ ] Photos placed in `Desktop/R_E_V/real-estate-images/Listings/Property Name/`
- [ ] Ran `node scripts/r2-manage.js upload <dir> listings/<slug>` to upload to R2
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
| Image upload script   | `scripts/r2-manage.js` (`upload` / `list` / `delete`)             |
| Local images folder   | `/Users/nathanaeljohnson/Desktop/R_E_V/real-estate-images/`       |
| R2 base URL           | `https://pub-78b56158b83942189fa28a4d5939bb79.r2.dev/`            |
| Admin page            | `admin/index.html`                                                 |
| Admin backend         | `scripts/admin-worker/` (Worker), `scripts/admin/apply_change.py`, `.github/workflows/admin-publish.yml` |
| Buy page              | `buy/index.html`                                                   |
| Rent page             | `rent/index.html`                                                  |
| Property detail page  | `property-detail.html`                                             |
| CSS styles            | `css/styles.css`                                                   |
| JS logic              | `js/main.min.js`                                                   |
