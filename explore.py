from flask import render_template, request, send_from_directory, Blueprint, current_app, redirect, url_for, send_file
import os
from werkzeug.utils import secure_filename

bp = Blueprint('explore', __name__, url_prefix='/explore')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def get_absolute_path(relative_path):
    upload_folder = current_app.config['UPLOAD_FOLDER']
    if not relative_path:
        return os.path.abspath(upload_folder)
    
    full_path = os.path.join(upload_folder, relative_path)
    abs_upload = os.path.abspath(upload_folder)
    abs_full_path = os.path.abspath(full_path)
    
    abs_upload = os.path.normpath(abs_upload)
    abs_full_path = os.path.normpath(abs_full_path)
    
    if not abs_full_path.startswith(abs_upload):
        return None
    return abs_full_path

@bp.route('/', defaults={'subpath': ''})
@bp.route('/<path:subpath>')
def index(subpath):
    abs_path = get_absolute_path(subpath)
    if abs_path is None or not os.path.exists(abs_path):
        return "Path not found", 404
    
    if os.path.isfile(abs_path):
        return redirect(url_for('explore.serve_file', filename=subpath))
    
    files = []
    dirs = []
    for item in os.listdir(abs_path):
        item_abs_path = os.path.join(abs_path, item)
        if os.path.isdir(item_abs_path):
            dir_path = os.path.join(subpath, item) if subpath else item
            dirs.append((item, dir_path))
        else:
            file_path = os.path.join(subpath, item) if subpath else item
            files.append((item, file_path))
    
    breadcrumbs = []
    if subpath:
        parts = subpath.split('/')
        path_so_far = ""
        for part in parts:
            path_so_far = os.path.join(path_so_far, part) if path_so_far else part
            breadcrumbs.append((path_so_far, part))
    
    return render_template('index.html', dirs=dirs, files=files, current_path=subpath, breadcrumbs=breadcrumbs)

@bp.route('/files/<path:filename>')
def serve_file(filename):
    abs_path = get_absolute_path(filename)
    if abs_path is None or not os.path.isfile(abs_path):
        return "File not found", 404
    
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

@bp.route('/upload', methods=['POST'])
def upload_file():
    subpath = request.form.get('current_path', '')
    abs_path = get_absolute_path(subpath)
    if abs_path is None or not os.path.isdir(abs_path):
        return 'Invalid path', 400
    
    if 'file' not in request.files:
        return 'No file part'
    
    file = request.files['file']
    if file.filename == '':
        return 'No selected file'
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(abs_path, filename))
        return redirect(url_for('explore.index', subpath=subpath))
    
    return 'Invalid file type'

@bp.route('/mkdir', methods=['POST'])
def mkdir():
    subpath = request.form.get('current_path', '')
    abs_path = get_absolute_path(subpath)
    if abs_path is None or not os.path.isdir(abs_path):
        return 'Invalid path', 400
    
    dirname = request.form.get('dirname', '')
    if not dirname:
        return 'Invalid folder name'
    
    dirname = secure_filename(dirname)
    if not dirname:
        return 'Invalid folder name'
    
    new_dir = os.path.join(abs_path, dirname)
    if not os.path.exists(new_dir):
        os.makedirs(new_dir)
    
    return redirect(url_for('explore.index', subpath=subpath))

@bp.route('/rename', methods=['POST'])
def rename():
    subpath = request.form.get('current_path', '')
    abs_path = get_absolute_path(subpath)
    if abs_path is None or not os.path.isdir(abs_path):
        return 'Invalid path', 400
    
    old_name = request.form.get('old_name')
    new_name = request.form.get('new_name')
    if not old_name or not new_name:
        return 'Invalid names'

    old_name = secure_filename(old_name)
    new_name = secure_filename(new_name)
    if not old_name or not new_name:
        return 'Invalid names'
    
    old_path = os.path.join(abs_path, old_name)
    new_path = os.path.join(abs_path, new_name)
    
    if not os.path.exists(old_path):
        return 'File or folder not found', 404
    
    if os.path.exists(new_path):
        return 'New name already exists', 400
    
    os.rename(old_path, new_path)
    return redirect(url_for('explore.index', subpath=subpath))
