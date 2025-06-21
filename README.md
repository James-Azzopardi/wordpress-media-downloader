# 🗂️ WordPress Media Downloader

This Python script parses a WordPress export XML file (`wordpress-export.xml`), extracts media URLs (including image variants), and downloads them locally while preserving the original folder structure.

✅ Supports:

-   Original media from `<wp:attachment_url>`
-   Alternate image sizes from serialized `_wp_attachment_metadata`
-   Embedded images/links from post content
-   Multithreaded downloads
-   SSL bypass for self-signed certificates
-   Progress bar with `tqdm`

---

## 📦 Requirements

### Install dependencies:

```bash
pip install -r requirements.txt
```

or

```bash
pip install requests beautifulsoup4 lxml phpserialize tqdm
```

## 🚀 Usage

Export your WordPress site as an XML file:

WordPress Admin → Tools → Export → All content

Save it as wordpress-export.xml in this directory.

Run the script:

```bash
python download_wp_assets.py
```

All assets will be downloaded to the wp-assets/ folder, preserving their upload structure (e.g., wp-assets/2023/06/image.jpg).

## ⚙️ Configuration

You can change:

| Setting        | Description                        |
| -------------- | ---------------------------------- |
| `XML_FILE`     | Path to the WordPress XML export   |
| `DOWNLOAD_DIR` | Target directory for saving assets |
| `MAX_WORKERS`  | Number of threads for downloading  |

## ⚠️ SSL Notes

This script disables SSL certificate verification (useful for legacy WordPress sites with expired/self-signed certs). For trusted public domains, you can enable SSL validation by removing:

```python
verify=False
```

## License

MIT — feel free to use, modify, or contribute.
