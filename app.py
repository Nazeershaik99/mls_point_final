from flask import Flask, render_template, request, jsonify, send_file, make_response, redirect, flash, session, url_for
import pandas as pd
from sqlalchemy import create_engine
import io
from datetime import datetime, timedelta
import logging
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from pdf_generator import generate_mls_pdf
from sqlalchemy.sql import text
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
# Session will expire after 1 hour of inactivity
app.permanent_session_lifetime = timedelta(hours=1)

# ---- Logging Setup ----
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---- PostgreSQL Config ----
PG_DATABASE_CONFIG = {
    'host': 'localhost',
    'database': 'postgres',
    'user': 'postgres',
    'password': '1234',
    'port': '5432'
}
PG_DATABASE_URL = f"postgresql://{PG_DATABASE_CONFIG['user']}:{PG_DATABASE_CONFIG['password']}@{PG_DATABASE_CONFIG['host']}:{PG_DATABASE_CONFIG['port']}/{PG_DATABASE_CONFIG['database']}"
pg_engine = create_engine(PG_DATABASE_URL)

# ---- Login Credentials ----
ADMIN_CREDENTIALS = {
    'admin': 'Admin@2025'
}


# ---- Login Required Decorator ----
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Please log in to access this page', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)

    return decorated_function


# ---- Load Data ----
def load_pg_data():
    try:
        query = "SELECT * FROM mls_points"
        df = pd.read_sql_query(query, pg_engine)
        df.columns = df.columns.str.lower().str.replace(' ', '_').str.replace('.', '')
        return df
    except Exception as e:
        logger.error(f"Error loading data from Postgres: {e}")
        return pd.DataFrame()


df_pg = load_pg_data()


# ---- Login Routes ----
@app.route('/login', methods=['GET', 'POST'])
def login():
    # If user is already logged in, redirect to main page
    if 'username' in session:
        return redirect(url_for('index'))

    # Handle login form submission
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Check credentials
        if username in ADMIN_CREDENTIALS and ADMIN_CREDENTIALS[username] == password:
            session.permanent = True  # Make the session permanent
            session['username'] = username
            session['login_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            logger.info(f"User '{username}' logged in successfully")
            flash('Login successful! Welcome to MLS Point Locator System.', 'success')

            # Redirect to the originally requested page or default to index
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            logger.warning(f"Failed login attempt for username: '{username}'")
            flash('Invalid username or password. Please try again.', 'danger')

    current_time = "2025-08-06 11:16:11"  # Use the provided timestamp
    return render_template('login.html', current_time=current_time)


@app.route('/logout')
def logout():
    username = session.pop('username', None)
    if username:
        logger.info(f"User '{username}' logged out")
        flash('You have been logged out successfully.', 'success')
    return redirect(url_for('login'))


# ---- Main Routes ----
@app.route('/')
@login_required
def index():
    return render_template('index.html',
                           current_user=session.get('username', 'Guest'),
                           current_time="2025-08-06 11:16:11")


@app.route('/dashboard')
@login_required
def dashboard():
    try:
        districts = sorted(df_pg['district_name'].dropna().unique())
        return render_template(
            'index1.html',
            districts=districts,
            current_time='2025-08-06 11:16:11',
            current_user=session.get('username', 'JPKrishna28')
        )
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return str(e), 500


@app.route('/get_filtered_data', methods=['POST'])
@login_required
def get_filtered_data():
    try:
        selected_district = request.form.get('district_name', 'All')
        selected_mandal = request.form.get('mandal_name', 'All')

        filtered_df = df_pg.copy()
        if selected_district != "All":
            filtered_df = filtered_df[filtered_df['district_name'] == selected_district]
        if selected_mandal != "All":
            filtered_df = filtered_df[filtered_df['mandal_name'] == selected_mandal]

        display_columns = [
            "mls_point_code",
            "mls_point_name",
            "mandal_name",
            "district_name",
            "mls_point_incharge_name",
            "storage_capacity_mts",
            "phone_number",
        ]

        records = filtered_df[display_columns].to_dict('records')
        return jsonify({'success': True, 'data': records})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/districts')
@login_required
def get_districts():
    try:
        districts = sorted(df_pg['district_name'].dropna().unique())
        return jsonify(districts)
    except Exception as e:
        logger.error(f"Error getting districts: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/mandals/<district>')
@login_required
def get_mandals(district):
    try:
        mandals = sorted(df_pg[df_pg['district_name'] == district]['mandal_name'].dropna().unique())
        return jsonify(mandals)
    except Exception as e:
        logger.error(f"Error getting mandals: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/mls_points/<district>/<mandal>')
@login_required
def get_mls_points(district, mandal):
    try:
        logger.info(f"Fetching MLS points for district: {district}, mandal: {mandal}")

        # Log the dataframe columns
        logger.info(f"Available columns: {df_pg.columns.tolist()}")

        # Filter the dataframe
        filtered_df = df_pg[
            (df_pg['district_name'] == district) &
            (df_pg['mandal_name'] == mandal)
            ]

        # Log the number of points found
        logger.info(f"Found {len(filtered_df)} points for {district}/{mandal}")

        if filtered_df.empty:
            return jsonify([])

        # Select required columns
        columns_to_include = [
            'mls_point_code',
            'mls_point_name',
            'district_name',
            'mandal_name',
            'mls_point_latitude',
            'mls_point_longitude',
            'mls_point_incharge_name',
            'storage_capacity_in_mts',
            'phone_number'
        ]

        # Get available columns
        available_columns = [col for col in columns_to_include if col in filtered_df.columns]

        # Convert to records
        points = filtered_df[available_columns].to_dict('records')

        # Log sample data
        if points:
            logger.info(f"Sample point data: {points[0]}")

        return jsonify(points)

    except Exception as e:
        logger.error(f"Error getting MLS points: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/user')
@login_required
def get_user():
    return jsonify({
        "username": session.get('username', 'JPKrishna28'),
        "timestamp": "2025-08-06 11:16:11"
    })


@app.route('/api/search_mls/<search_term>')
@login_required
def search_mls(search_term):
    try:
        logger.info(f"Searching for MLS point: {search_term}")
        # Convert search_term to string to ensure contains() works properly
        filtered_df = df_pg[df_pg['mls_point_code'].astype(str).str.contains(search_term, case=False)]

        if filtered_df.empty:
            return jsonify([])

        # Select all relevant columns to ensure data is available for the view details
        display_columns = [
            'mls_point_code',
            'mls_point_name',
            'district_name',
            'district_code',
            'mandal_name',
            'mandal_code',
            'mls_point_latitude',
            'mls_point_longitude',
            'mls_point_incharge_name',
            'phone_number',  # Changed from mobile_no to match column names
            'deo_name',
            'deo_phone_number',  # Changed to match column names
            'storage_capacity_mts'  # Changed from storage_capacity_in_mts to match column names
        ]

        # Get only the columns that exist in the dataframe
        available_columns = [col for col in display_columns if col in filtered_df.columns]

        points = filtered_df[available_columns].to_dict('records')
        logger.info(f"Found {len(points)} points matching '{search_term}'")

        return jsonify(points)
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/view_details/<mls_code>')
@login_required
def view_details(mls_code):
    try:
        logger.info(f"Viewing details for MLS code: {mls_code}")
        # Filter by mls_point_code as string to ensure correct matching
        record_df = df_pg[df_pg['mls_point_code'].astype(str) == str(mls_code)]

        if record_df.empty:
            logger.error(f"No record found for MLS code: {mls_code}")
            return f"Error: No record found for MLS code {mls_code}", 404

        # Convert the first record to a dictionary
        details = record_df.iloc[0].to_dict()

        # Make sure all necessary keys exist (even if empty)
        required_keys = [
            'mls_point_code', 'mls_point_name', 'district_name', 'district_code',
            'mandal_code', 'mandal_name', 'mls_point_address', 'mls_point_latitude',
            'mls_point_longitude', 'mls_point_incharge_cfms_id', 'mls_point_incharge_name',
            'designation', 'phone_number', 'deo_cfms_id', 'deo_name',
            'deo_phone_number', 'storage_capacity_mts', 'godown_area_sqft',
            'mls_point_ownership', 'weighbridge_available', 'cc_cameras_installed',
            'hamalies_working', 'stage2_vehicles_registered', 'gps_installed_on_all_vehicles',
            'camera_vendor'
        ]

        for key in required_keys:
            if key not in details:
                details[key] = ""

        logger.info(f"Details fetched successfully for MLS code: {mls_code}")
        return render_template('details.html',
                               info=details,
                               current_user=session.get('username', 'JPKrishna28'),
                               current_time="2025-08-06 11:16:11")
    except Exception as e:
        logger.error(f"Error in view_details: {str(e)}")
        return f"Error: {str(e)}", 500


@app.route('/api/download_pdf/<mls_code>')
@login_required
def download_pdf(mls_code):
    try:
        logger.info(f"Generating PDF for MLS code: {mls_code}")

        # Get the MLS data from database
        record_df = df_pg[df_pg['mls_point_code'].astype(str) == str(mls_code)]

        if record_df.empty:
            logger.error(f"No record found for MLS code: {mls_code}")
            return f"Error: No record found for MLS code {mls_code}", 404

        # Convert the first record to a dictionary
        mls_data = record_df.iloc[0].to_dict()

        # Add current date and time
        mls_data['generated_date'] = "2025-08-06 11:16:11"
        mls_data['generated_by'] = session.get('username', 'JPKrishna28')

        # Log data to help debug
        logger.info(f"Generating PDF with data keys: {list(mls_data.keys())}")

        try:
            # Generate PDF
            pdf_data = generate_mls_pdf(mls_data)

            # Create response
            response = make_response(pdf_data)
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'attachment; filename=MLS_Point_{mls_code}.pdf'

            logger.info(f"PDF generated successfully for MLS code: {mls_code}")
            return response
        except Exception as pdf_error:
            logger.error(f"PDF generation error: {str(pdf_error)}")
            return f"Error generating PDF: {str(pdf_error)}", 500

    except Exception as e:
        logger.error(f"Error in download_pdf route: {str(e)}")
        return f"Error in download_pdf route: {str(e)}", 500


@app.route('/edit_details/<mls_code>')
@login_required
def edit_details(mls_code):
    try:
        logger.info(f"Editing details for MLS code: {mls_code}")
        # Filter by mls_point_code as string to ensure correct matching
        record_df = df_pg[df_pg['mls_point_code'].astype(str) == str(mls_code)]

        if record_df.empty:
            logger.error(f"No record found for MLS code: {mls_code}")
            return f"Error: No record found for MLS code {mls_code}", 404

        # Convert the first record to a dictionary
        details = record_df.iloc[0].to_dict()

        # Debug log
        logger.info(f"Retrieved columns for editing: {list(details.keys())}")

        # Make sure all necessary keys exist (even if empty)
        required_keys = [
            'mls_point_code', 'mls_point_name', 'district_name', 'district_code',
            'mandal_code', 'mandal_name', 'mls_point_address', 'mls_point_latitude',
            'mls_point_longitude', 'mls_point_incharge_cfms_id', 'mls_point_incharge_name',
            'designation', 'phone_number', 'aadhaar_number', 'deo_cfms_id', 'deo_name',
            'deo_aadhaar_number', 'deo_phone_number', 'storage_capacity_mts', 'godown_area_sqft',
            'mls_point_ownership', 'rented_type', 'weighbridge_available', 'cc_cameras_installed',
            'cameras_working', 'camera_vendor', 'hamalies_working', 'stage2_vehicles_registered',
            'gps_installed_on_all_vehicles', 'nominee_incharge_name', 'nominee_phone_number',
            'nominee_incharge_cfms_id'
        ]

        for key in required_keys:
            if key not in details:
                details[key] = ""

        logger.info(f"Details fetched for editing for MLS code: {mls_code}")
        return render_template('edit_details.html',
                               info=details,
                               current_time="2025-08-06 11:16:11",
                               current_user=session.get('username', 'JPKrishna28'))
    except Exception as e:
        logger.error(f"Error in edit_details: {str(e)}")
        return f"Error: {str(e)}", 500


@app.route('/update_details/<mls_code>', methods=['POST'])
@login_required
def update_details(mls_code):
    try:
        logger.info(f"Updating details for MLS code: {mls_code}")

        # Check if the MLS code exists
        record_df = df_pg[df_pg['mls_point_code'].astype(str) == str(mls_code)]

        if record_df.empty:
            logger.error(f"No record found for MLS code: {mls_code}")
            flash(f"Error: No record found for MLS code {mls_code}", "error")
            return redirect(f'/edit_details/{mls_code}')

        # Get form data
        form_data = request.form.to_dict()

        # Log what we're updating
        logger.info(f"Received form data with keys: {list(form_data.keys())}")

        try:
            # Method 2: Use SQLAlchemy ORM-style update
            from sqlalchemy import Table, MetaData, Column
            from sqlalchemy.sql import update

            metadata = MetaData()
            mls_table = Table('mls_points', metadata, autoload_with=pg_engine)

            # Prepare update values
            update_values = {}
            for key, value in form_data.items():
                if key in df_pg.columns:
                    update_values[key] = value

            # Create update statement
            stmt = update(mls_table).where(
                mls_table.c.mls_point_code == mls_code
            ).values(**update_values)

            # Execute the update
            with pg_engine.begin() as conn:
                conn.execute(stmt)

            # Update the dataframe as well to keep it in sync
            record_idx = record_df.index[0]
            for key, value in form_data.items():
                if key in df_pg.columns:
                    df_pg.at[record_idx, key] = value

            logger.info(f"Successfully updated database record for MLS code: {mls_code}")
            flash("MLS Point details updated successfully!", "success")

        except Exception as db_error:
            logger.error(f"Database update error: {str(db_error)}")
            flash(f"Warning: Database reported an error but data may have been updated: {str(db_error)}", "warning")

        # Redirect to the view page
        return redirect(f'/view_details/{mls_code}')

    except Exception as e:
        logger.error(f"Error in update_details: {str(e)}")
        flash(f"Error updating details: {str(e)}", "error")
        return redirect(f'/edit_details/{mls_code}')


if __name__ == '__main__':
    app.run(debug=True)