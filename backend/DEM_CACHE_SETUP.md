# Automatic Mars DEM loading and cache setup

MARSCOPE fetches a site's catalogued official DEM the first time that site is requested through \`GET /api/terrain/{site_id}\`. The frontend already requests this endpoint when a judge selects a mission site, so no judge-side file download or upload is required.

## What the backend does

1. Check the in-process terrain cache.
2. Check the processed local cache.
3. If configured, check the persistent S3-compatible processed cache.
4. Otherwise restore the original source DEM from the persistent bucket, or download the exact HTTPS URL in \`backend/app/mission_sites.py\`.
5. Verify the selected site's geographic footprint, Mars planetary CRS and metre units.
6. Derive only the elevation, slope and local-roughness layers from the measured DEM. NoData cells remain blocked; unavailable science/hazard layers remain unavailable.
7. Store a compact processed-grid cache and preserve the original source DEM plus its SHA-256 provenance.

The source downloader only accepts the four URLs declared in the code catalogue. Redirects are restricted to the official USGS/HiRISE/Zenodo hosts and the object-storage host used by those archives. A failed download or failed validation returns an API error; it never substitutes a synthetic grid or another site's raster.

## Cache options

### Option A — persistent disk

Mount a persistent disk on the backend service and set:

- \`MARS_DEM_CACHE_DIR\` to the disk's mounted directory, for example \`/var/data/marscope-dems\`.

The service writes both original source files and processed grids there. The directory must be writable by the backend process and have room for the original files (the Gale source is about 312 MB).

### Option B — S3-compatible object storage (recommended for redeploy-safe hosting)

Set these backend environment variables:

- \`MARS_DEM_S3_BUCKET\` — bucket name.
- \`AWS_ACCESS_KEY_ID\` — access key with read/write permission for the bucket/prefix.
- \`AWS_SECRET_ACCESS_KEY\` — secret key.
- \`MARS_DEM_S3_REGION\` — bucket region; use the provider's required value.
- \`MARS_DEM_S3_ENDPOINT_URL\` — optional endpoint for S3-compatible providers such as Cloudflare R2.
- \`MARS_DEM_S3_PREFIX\` — optional key prefix; defaults to \`marscope\`.

For AWS S3, leave the endpoint unset and set the actual AWS region. For Cloudflare R2, set the account-specific R2 endpoint and the region value required by R2. Never commit access keys to the repository or expose them as \`VITE_*\` frontend variables.

The bucket is private by default from the application's perspective; the backend reads and writes objects using its server-side credentials. The processed cache and original source file are stored separately so future cold starts can load the compact grid without downloading the full DEM again.

If no persistent disk or bucket is configured, the backend uses an instance-local cache. This works while that backend instance retains its filesystem, but the cache may be lost on restart, scale-out or redeploy and the DEM may need to be fetched again.

## Fork deployment checklist

The frontend must call a backend built from this same fork/branch. The current frontend default still points at the previous shared Render API, which does not contain this automatic-loader change.

1. Deploy the backend from this fork to a separate backend service that you control. Do not repoint or replace a service shared with the teammate's main repository.
2. Configure one persistent cache option above on that backend.
3. Set the Vercel project's \`VITE_API_BASE\` to the new backend's HTTPS base URL, without a trailing slash, then redeploy the frontend.
4. Open the site once for each supported region and allow the initial source download/validation to finish. Later requests should use the processed cache.
5. Check \`GET /api/sites\` for the automatic-loading flag and cache mode, then \`GET /api/terrain/{site_id}\` for a real terrain response with \`status = NASA_OR_USER_SUPPLIED_GEOREFERENCED_DEM\` and \`coordinate_info.site_coverage_verified = true\`.

## Important limits

- The first request for a site can take longer because it downloads and processes the source DEM. The Gale file is about 312 MB.
- The current automatic download limit is 400 MiB per source file.
- Meridiani's catalogued source is a PDS3 HiRISE \`.IMG\`. It loads only if the deployed GDAL/Rasterio build can read its embedded PDS label and planetary mapping. If it fails CRS/coverage validation, the API reports the failure; it does not fabricate data.
- The four source products have different spatial extents and resolutions. The app uses a 96 × 96 route grid derived from the source raster; the original raster and retrieval metadata are retained for provenance.
- Automatic DEM loading supplies terrain elevation and derived slope/roughness only. It does not create measured temperature, radiation, atmosphere, regolith, mineralogy or science-target layers.
