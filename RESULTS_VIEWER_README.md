# Results Viewer WebApp

A simple Flask webapp to display AI testing results and allow downloading of target code.

## Features

- **Results Summary**: Clean overview of pipeline results
- **Detailed Results**: In-depth analysis of all result files
- **Download Functionality**: Download all target code and results as ZIP
- **JSON API**: Programmatic access to results
- **Responsive Design**: Works on desktop and mobile

## Setup

1. Install dependencies:
```bash
pip install -r results_viewer_requirements.txt
```

2. Run the webapp:
```bash
python results_viewer.py
```

3. Open browser to `http://localhost:5001`

## File Structure

- `results_viewer.py` - Main Flask application
- `results_viewer_requirements.txt` - Python dependencies
- `results_templates/` - HTML templates
  - `results_index.html` - Main summary page
  - `results_detail.html` - Detailed results page

## API Endpoints

- `GET /` - Main results summary page
- `GET /results` - Detailed results page
- `GET /download` - Download ZIP of all results
- `GET /api/results` - JSON API for results

## Data Sources

The app reads results from the `TARGET_CODE/` directory:
- `pipeline_results_summary.json` - Main summary
- Other JSON/TXT files - Detailed results
- All files are included in the download ZIP

## Deployment

This is a standalone webapp that can be deployed independently. Configure your web server to serve it on the desired port.