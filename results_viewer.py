from flask import Flask, render_template, send_file, jsonify
import os
import json
from pathlib import Path
import zipfile
import io

app = Flask(__name__, template_folder='results_templates')

# Path to TARGET_CODE directory
TARGET_CODE_DIR = Path(__file__).parent / "TARGET_CODE"

@app.route('/')
def index():
    """Main page showing results and download options"""
    results = get_results_summary()
    return render_template('results_index.html', results=results)

@app.route('/results')
def results():
    """Detailed results page"""
    results = get_detailed_results()
    return render_template('results_detail.html', results=results)

@app.route('/download')
def download_target_code():
    """Download TARGET_CODE as ZIP"""
    if not TARGET_CODE_DIR.exists():
        return "TARGET_CODE directory not found", 404

    # Create in-memory ZIP file
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for file_path in TARGET_CODE_DIR.rglob('*'):
            if file_path.is_file():
                # Add file to ZIP with relative path
                relative_path = file_path.relative_to(TARGET_CODE_DIR.parent)
                zip_file.write(file_path, relative_path)

    zip_buffer.seek(0)

    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name='target_code_results.zip'
    )

@app.route('/api/results')
def api_results():
    """JSON API for results"""
    return jsonify(get_results_summary())

def get_results_summary():
    """Get summary of results from TARGET_CODE"""
    results = {
        'pipeline_summary': {},
        'target_code_files': [],
        'has_results': False
    }

    if not TARGET_CODE_DIR.exists():
        return results

    # Read pipeline results summary
    summary_file = TARGET_CODE_DIR / "pipeline_results_summary.json"
    if summary_file.exists():
        try:
            with open(summary_file, 'r') as f:
                results['pipeline_summary'] = json.load(f)
                results['has_results'] = True
        except Exception as e:
            results['pipeline_summary'] = {'error': f'Failed to load summary: {str(e)}'}

    # List target code files
    if TARGET_CODE_DIR.exists():
        for file_path in TARGET_CODE_DIR.iterdir():
            if file_path.is_file() and file_path.name not in ['pipeline_results_summary.json']:
                results['target_code_files'].append({
                    'name': file_path.name,
                    'size': file_path.stat().st_size,
                    'modified': file_path.stat().st_mtime
                })

    return results

def get_detailed_results():
    """Get detailed results from all result files"""
    results = {}

    if not TARGET_CODE_DIR.exists():
        return results

    # Read all JSON result files
    for file_path in TARGET_CODE_DIR.glob('*.json'):
        if file_path.name != 'pipeline_results_summary.json':
            try:
                with open(file_path, 'r') as f:
                    results[file_path.stem] = json.load(f)
            except Exception as e:
                results[file_path.stem] = {'error': f'Failed to load: {str(e)}'}

    # Read text result files
    for file_path in TARGET_CODE_DIR.glob('*.txt'):
        try:
            with open(file_path, 'r') as f:
                results[file_path.stem] = {'content': f.read()}
        except Exception as e:
            results[file_path.stem] = {'error': f'Failed to load: {str(e)}'}

    return results

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)