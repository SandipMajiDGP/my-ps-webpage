import logging
from flask import Flask, request, jsonify, render_template, Blueprint
import mysql
from flask_cors import CORS
from db import get_connection
from cryptography.fernet import Fernet
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from functools import wraps
import time  

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[logging.StreamHandler()]
)

URL_CONTEXT = '/psm'
app = Flask(__name__, static_url_path=f'{URL_CONTEXT}/static', static_folder='static')
CORS(app, resources={r"/*": {"origins": "*"}})
fernet = Fernet(b'8Fsrl6tt6KkJzE3qCxxM7TT7H73na3_b_6Iv5b4ubmE=')  # Encryption key
SECRET_KEY = "supersecretkey123!"  # Use env var in production

context_changer = Blueprint('context_changer', __name__, url_prefix=URL_CONTEXT)

@app.route(URL_CONTEXT)
def index():
    logging.info("Rendering index page.")
    return render_template('login.html', url_context=URL_CONTEXT)

@app.route(f"{URL_CONTEXT}/dashboard")
def dashboard_page():
    return render_template('dashboard.html', url_context=URL_CONTEXT)

@app.route(f"{URL_CONTEXT}/admin")
def admin_page():
    return render_template('admin.html', url_context=URL_CONTEXT)

@app.before_request
def log_request_info():
    request.start_time = time.time()
    logging.info(f"Request started: {request.method} {request.url}")

@app.after_request
def log_response_info(response):
    duration = time.time() - request.start_time
    logging.info(f"Request completed: {request.method} {request.url} | Status: {response.status_code} | Duration: {duration:.4f} seconds")
    return response

# JWT Utilities
def generate_token(user_id, role):
    payload = {
        'user_id': user_id,
        'role': role,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=12)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    logging.info(f"Generated JWT for user_id: {user_id} with role: {role}")
    return token

def verify_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        logging.info(f"Token verified for user_id: {payload['user_id']}, role: {payload.get('role')}")
        return payload
    except jwt.ExpiredSignatureError:
        logging.warning("Token expired.")
        return None
    except jwt.InvalidTokenError:
        logging.warning("Invalid token.")
        return None

def jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', None)
        if not auth_header or not auth_header.startswith('Bearer '):
            logging.warning("Missing or invalid Authorization header.")
            return jsonify({'error': 'Missing or invalid Authorization header'}), 401
        token = auth_header.split(" ")[1]
        payload = verify_token(token)
        if not payload:
            logging.warning("Invalid or expired JWT token.")
            return jsonify({'error': 'Invalid or expired token'}), 401
        request.user_id = payload['user_id']
        request.user_role = payload.get('role', 'user')
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if getattr(request, 'user_role', 'user') != 'admin':
            logging.warning(f"User {request.user_id} is not an admin.")
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated

# Disable public registration
@app.route(f"{URL_CONTEXT}/register", methods=['POST'])
def register_disabled():
    logging.warning("Attempt to access disabled public registration endpoint.")
    return jsonify({"error": "Registration is restricted to admin users only."}), 403

# Admin-only registration
@app.route(f"{URL_CONTEXT}/admin/register", methods=['POST'])
@jwt_required
@admin_required
def admin_register_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'user')  # Default role

    if not username or not password:
        logging.warning("Admin registration failed: missing username or password.")
        return jsonify({'error': 'Missing username or password'}), 400

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
    if cursor.fetchone():
        logging.warning(f"Admin registration failed: username '{username}' already exists.")
        return jsonify({'error': 'Username already exists'}), 409

    password_hash = generate_password_hash(password)
    cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)", (username, password_hash, role))
    conn.commit()
    cursor.close()
    conn.close()
    logging.info(f"Admin user {request.user_id} created user '{username}' with role '{role}'.")
    return jsonify({'message': 'User created successfully'}), 201
# Fetch users
@app.route(f"{URL_CONTEXT}/admin/users", methods=["GET"])
@jwt_required
@admin_required
def get_all_users():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, username, role FROM users")  # Removed where clause to include all users
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    logging.info(f"Admin {request.user_id} fetched all users.")
    return jsonify(users), 200

@app.route(f"{URL_CONTEXT}/admin/change_role", methods=["POST"])
@jwt_required
@admin_required
def change_user_role():
    data = request.get_json()
    username = data.get("username")
    new_role = data.get("role")

    if not username or new_role not in ["user", "admin"]:
        logging.warning("Invalid request to change user role.")
        return jsonify({"error": "Missing or invalid username/role"}), 400

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Check if user exists
    cursor.execute("SELECT id, role FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()

    if not user:
        logging.warning(f"Attempted to change role for non-existent user '{username}'.")
        cursor.close()
        conn.close()
        return jsonify({"error": "User not found"}), 404

    # Prevent changing own role
    if user['id'] == request.user_id:
        logging.warning("Admin attempted to change their own role.")
        cursor.close()
        conn.close()
        return jsonify({"error": "You cannot change your own role"}), 403

    # No change needed
    if user["role"] == new_role:
        logging.info(f"User '{username}' already has role '{new_role}'.")
        cursor.close()
        conn.close()
        return jsonify({"message": f"User already has role '{new_role}'"}), 200

    # Update role
    cursor.execute("UPDATE users SET role = %s WHERE username = %s", (new_role, username))
    conn.commit()
    cursor.close()
    conn.close()

    logging.info(f"Admin {request.user_id} changed role of '{username}' to '{new_role}'.")
    return jsonify({"message": f"User '{username}' role updated to '{new_role}'"}), 200

@app.route(f"{URL_CONTEXT}/admin/delete_user", methods=["DELETE"])
@jwt_required
@admin_required
def delete_user():
    data = request.get_json()
    username = data.get("username")

    if not username:
        logging.warning("No username provided for user deletion.")
        return jsonify({"error": "Missing username"}), 400

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Check if user exists
    cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()

    if not user:
        logging.warning(f"Attempted to delete non-existent user '{username}'.")
        cursor.close()
        conn.close()
        return jsonify({"error": "User not found"}), 404

    # Prevent deleting self
    if user["id"] == request.user_id:
        logging.warning("Admin attempted to delete their own account.")
        cursor.close()
        conn.close()
        return jsonify({"error": "You cannot delete your own account"}), 403

    # Delete user
    cursor.execute("DELETE FROM users WHERE username = %s", (username,))
    conn.commit()
    cursor.close()
    conn.close()

    logging.info(f"Admin {request.user_id} deleted user '{username}'.")
    return jsonify({"message": f"User '{username}' deleted successfully"}), 200



# Login
@app.route(f"{URL_CONTEXT}/login", methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, password_hash, role FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user and check_password_hash(user['password_hash'], password):
        logging.info(f"User '{username}' logged in successfully.")
        token = generate_token(user['id'], user['role'])
        return jsonify({'token': token})
    else:
        logging.warning(f"Login failed for username '{username}'.")
        return jsonify({'error': 'Invalid credentials'}), 401


# Admin grants module access
@app.route(f"{URL_CONTEXT}/admin/grant_access", methods=['POST'])
@jwt_required
@admin_required
def grant_module_access():
    data = request.get_json()
    user_id = data.get('user_id')
    module = data.get('module')

    if not user_id or not module:
        return jsonify({"error": "Missing user_id or module"}), 400

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    # Check if the module is created by an admin
    cursor.execute("""
        SELECT u.role FROM credentials c JOIN users u ON c.user_id = u.id WHERE c.module = %s
    """, (module,))
    creator = cursor.fetchone()
    if not creator or creator['role'] != 'admin':
        cursor.close()
        conn.close()
        return jsonify({"error": "Cannot grant access to non-admin module"}), 403
    # Step 1: Check if the user already has access to the module
    cursor.execute("SELECT * FROM user_module_access WHERE user_id = %s AND module = %s", (user_id, module))
    existing_access = cursor.fetchone()
    # Step 2: Check if the user owns the module
    cursor.execute("SELECT * FROM credentials WHERE user_id = %s AND module = %s", (user_id, module))
    owned_module = cursor.fetchone()
    if existing_access:
        logging.warning(f"User {user_id} already has access to module '{module}'.")
        cursor.close()
        conn.close()
        return jsonify({"error": "User already has access to this module"}), 409
    if owned_module:
        logging.warning(f"User {user_id} owns the module '{module}' and cannot be granted access to it.")
        cursor.close()
        conn.close()
        return jsonify({"error": "User cannot be granted access to their own module"}), 403
    try:
        # Step 3: Insert the new access record for the user
        cursor.execute("INSERT INTO user_module_access (user_id, module) VALUES (%s, %s)", (user_id, module))
        conn.commit()
        logging.info(f"Admin granted user {user_id} access to module '{module}'.")
    except mysql.connector.errors.IntegrityError as e:
        logging.error(f"Duplicate entry error: {str(e)}")
        cursor.close()
        conn.close()
        return jsonify({"error": "Duplicate entry detected. The user might already have access to the module."}), 409
    except Exception as e:
        logging.error(f"Error occurred while granting access: {str(e)}")
        cursor.close()
        conn.close()
        return jsonify({"error": "Failed to grant module access due to an internal error."}), 500
    cursor.close()
    conn.close()
    return jsonify({"message": "Access granted successfully"}), 201


@app.route(f"{URL_CONTEXT}/admin/revoke_access", methods=['POST'])
@jwt_required
@admin_required
def revoke_module_access():
    data = request.get_json()
    user_id = data.get('user_id')
    module = data.get('module')

    if not user_id or not module:
        return jsonify({"error": "Missing user_id or module"}), 400

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Step 1: Check if the user owns the module
    cursor.execute("SELECT * FROM credentials WHERE user_id = %s AND module = %s", (user_id, module))
    owned_module = cursor.fetchone()

    if owned_module:
        # User owns the module, so access cannot be revoked
        logging.warning(f"Cannot revoke access for user {user_id} to module '{module}' as they own it.")
        cursor.close()
        conn.close()
        return jsonify({"error": "User owns this module and cannot have access revoked"}), 403

    # Step 2: Check if the module still exists in credentials
    cursor.execute("SELECT 1 FROM credentials WHERE module = %s", (module,))
    module_exists = cursor.fetchone()
    if not module_exists:
        # If the module no longer exists, also remove all user_module_access records for this module
        cursor.execute("DELETE FROM user_module_access WHERE module = %s", (module,))
        conn.commit()
        logging.info(f"Module '{module}' no longer exists. All access records for this module have been removed.")
        cursor.close()
        conn.close()
        return jsonify({"message": f"Module '{module}' no longer exists. All access records removed."}), 200

    # Step 3: Check if the user has access to the module
    cursor.execute("SELECT * FROM user_module_access WHERE user_id = %s AND module = %s", (user_id, module))
    access = cursor.fetchone()

    if not access:
        logging.warning(f"User {user_id} does not have access to module '{module}'.")
        cursor.close()
        conn.close()
        return jsonify({"error": "User does not have access to this module"}), 404

    # Step 4: Revoke the access
    cursor.execute("DELETE FROM user_module_access WHERE user_id = %s AND module = %s", (user_id, module))
    conn.commit()

    cursor.close()
    conn.close()

    logging.info(f"Admin revoked user {user_id}'s access to module '{module}'.")
    return jsonify({"message": "Access revoked successfully"}), 200


@app.route(f"{URL_CONTEXT}/admin/change_password", methods=["POST"])
@jwt_required
@admin_required
def admin_change_password():
    data = request.get_json()
    username = data.get("username")
    new_password = data.get("password")

    if not username or not new_password:
        logging.warning("Missing username or password for password change.")
        return jsonify({"error": "Missing username or password"}), 400

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    if not user:
        cursor.close()
        conn.close()
        logging.warning(f"Attempted to change password for non-existent user '{username}'.")
        return jsonify({"error": "User not found"}), 404

    password_hash = generate_password_hash(new_password)
    cursor.execute("UPDATE users SET password_hash = %s WHERE username = %s", (password_hash, username))
    conn.commit()
    cursor.close()
    conn.close()
    logging.info(f"Admin {request.user_id} changed password for user '{username}'.")
    return jsonify({"message": f"Password updated for user '{username}'"}), 200


# Credential API
@context_changer.route('/api/entries', methods=['GET'])
@jwt_required
def get_all_entries():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    # Get modules the user has access to
    cursor.execute("SELECT module FROM user_module_access WHERE user_id = %s", (request.user_id,))
    allowed_modules = [module['module'] for module in cursor.fetchall()]
    # Get modules the user owns
    cursor.execute("SELECT module FROM credentials WHERE user_id = %s", (request.user_id,))
    owned_modules = [module['module'] for module in cursor.fetchall()]
    # Combine and deduplicate
    all_modules = list(set(allowed_modules + owned_modules))
    if request.user_role == 'admin':
        cursor.execute("""
            SELECT c.*, u.username AS created_by
            FROM credentials c
            JOIN users u ON c.user_id = u.id
        """)
    else:
        if all_modules:
            format_strings = ','.join(['%s'] * len(all_modules))
            cursor.execute(f"""
                SELECT c.*, u.username AS created_by
                FROM credentials c
                JOIN users u ON c.user_id = u.id
                WHERE c.module IN ({format_strings})
            """, all_modules)
        else:
            cursor.execute("SELECT * FROM credentials WHERE 0")
    entries = cursor.fetchall()
    for entry in entries:
        entry['password'] = fernet.decrypt(entry['password'].encode()).decode()
    cursor.close()
    conn.close()
    logging.info(f"User {request.user_id} fetched credential entries.")
    return jsonify(entries)

@context_changer.route('/api/entry/<int:entry_id>', methods=['GET'])
@jwt_required
def get_entry(entry_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM credentials WHERE id = %s", (entry_id,))
    entry = cursor.fetchone()

    if entry:
        # Allow owner or admin, otherwise check explicit access
        if entry['user_id'] != request.user_id and request.user_role != 'admin':
            cursor.execute("SELECT module FROM user_module_access WHERE user_id = %s AND module = %s", (request.user_id, entry['module']))
            access = cursor.fetchone()
            if not access:
                logging.warning(f"User {request.user_id} unauthorized to access entry {entry_id}.")
                cursor.close()
                conn.close()
                return jsonify({"error": "Not authorized"}), 403
        entry['password'] = fernet.decrypt(entry['password'].encode()).decode()
        logging.info(f"User {request.user_id} fetched entry {entry_id}.")
        cursor.close()
        conn.close()
        return jsonify(entry)

    logging.warning(f"Entry {entry_id} not found.")
    cursor.close()
    conn.close()
    return jsonify({"error": "Entry not found"}), 404

@context_changer.route('/api/entry', methods=['POST'])
@jwt_required
def create_entry():
    data = request.get_json()
    # Backend validation for required fields
    required_fields = ['module', 'ip', 'port', 'password']
    missing = [field for field in required_fields if not data.get(field)]
    if missing:
        logging.warning(f"Entry creation failed: missing required fields: {missing}")
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400
    encrypted_password = fernet.encrypt(data['password'].encode()).decode()

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(""" 
            INSERT INTO credentials (module, ip, port, url, username, password, note, user_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data['module'], data['ip'], data['port'], data.get('url'),
            data.get('username'), encrypted_password, data.get('note'), request.user_id
        ))
        conn.commit()
        logging.info(f"User {request.user_id} created entry for module '{data['module']}'.")
        return jsonify({"message": "Entry created"}), 201
    except mysql.connector.errors.IntegrityError as e:
        # Check if it's a duplicate entry error (based on the error code)
        if e.errno == 1062:  # 1062 is the error code for duplicate entry in MySQL/MariaDB
            logging.error(f"Duplicate module error: {str(e)}")
            return jsonify({"error": "Module name already exists"}), 409
        else:
            logging.error(f"Unexpected database error: {str(e)}")
            return jsonify({"error": "An error occurred while creating the entry"}), 500
    finally:
        cursor.close()
        conn.close()

@context_changer.route('/api/entry/<int:entry_id>', methods=['PUT'])
@jwt_required
def update_entry(entry_id):
    data = request.get_json()
    # Backend validation for required fields
    required_fields = ['module', 'ip', 'port', 'password']
    missing = [field for field in required_fields if not data.get(field)]
    if missing:
        logging.warning(f"Entry update failed: missing required fields: {missing}")
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400
    encrypted_password = fernet.encrypt(data['password'].encode()).decode()

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT user_id, module FROM credentials WHERE id = %s", (entry_id,))
    entry = cursor.fetchone()

    if entry and (entry['user_id'] == request.user_id or request.user_role == 'admin'):
        old_module = entry['module']
        new_module = data['module']
        try:
            cursor.execute(""" 
                UPDATE credentials
                SET module=%s, ip=%s, port=%s, url=%s, username=%s, password=%s, note=%s
                WHERE id=%s
            """, (
                new_module, data['ip'], data['port'], data.get('url'),
                data.get('username'), encrypted_password, data.get('note'), entry_id
            ))
            # If module name changed, update user_module_access
            if old_module != new_module:
                cursor.execute("UPDATE user_module_access SET module = %s WHERE module = %s", (new_module, old_module))
            conn.commit()
            logging.info(f"User {request.user_id} updated entry {entry_id}. (Module: '{old_module}' -> '{new_module}')")
            return jsonify({"message": "Entry updated successfully"}), 200
        except mysql.connector.errors.IntegrityError as e:
            if e.errno == 1062:
                logging.error(f"Duplicate module error during update: {str(e)}")
                return jsonify({"error": "Module name already exists"}), 409
            else:
                logging.error(f"Unexpected error during update: {str(e)}")
                return jsonify({"error": "Failed to update entry"}), 500
        finally:
            cursor.close()
            conn.close()
    else:
        logging.warning(f"Unauthorized update attempt by user {request.user_id} for entry {entry_id}.")
        cursor.close()
        conn.close()
        return jsonify({"error": "Not authorized to update this entry"}), 403

    
@context_changer.route('/api/entry/<int:entry_id>', methods=['DELETE'])
@jwt_required
def delete_entry(entry_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT user_id FROM credentials WHERE id = %s", (entry_id,))
    entry = cursor.fetchone()

    if entry and (entry['user_id'] == request.user_id or request.user_role == 'admin'):
        cursor.execute("DELETE FROM credentials WHERE id = %s", (entry_id,))
        conn.commit()
        cursor.close()
        conn.close()
        logging.info(f"User {request.user_id} deleted entry {entry_id}.")
        return jsonify({"message": "Entry deleted"})
    else:
        cursor.close()
        conn.close()
        logging.warning(f"User {request.user_id} unauthorized to delete entry {entry_id}.")
        return jsonify({"error": "Not authorized"}), 403

@app.route(f"{URL_CONTEXT}/api/user_module_access", methods=["GET"])
@jwt_required
@admin_required
def get_user_module_access():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    # Only show non-admin users in the module access list
    cursor.execute("SELECT user_id, module FROM user_module_access WHERE user_id IN (SELECT id FROM users WHERE role != 'admin')")
    access = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(access), 200

@app.route(f"{URL_CONTEXT}/api/modules", methods=["GET"])
@jwt_required
@admin_required
def get_all_modules():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    # Only modules created by admin users
    cursor.execute("""
        SELECT c.module, u.username AS created_by
        FROM credentials c
        JOIN users u ON c.user_id = u.id
        WHERE u.role = 'admin'
    """)
    modules = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(modules), 200

app.register_blueprint(context_changer)

def ensure_default_admin():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id FROM users WHERE username = %s", ('admin',))
    if not cursor.fetchone():
        from werkzeug.security import generate_password_hash
        password_hash = generate_password_hash("admin@123!")
        cursor.execute("""
            INSERT INTO users (username, password_hash, role)
            VALUES (%s, %s, %s)
        """, ('admin', password_hash, 'admin'))
        conn.commit()
        logging.info("✅ Default admin user 'admin' created with password 'admin123!'.")
    else:
        logging.info("✅ Default admin user already exists.")
    cursor.close()
    conn.close()

# Call before app starts
ensure_default_admin()

if __name__ == "__main__":
    logging.info("Starting application.....")
    app.run(debug=True, host="0.0.0.0", port=32001)
