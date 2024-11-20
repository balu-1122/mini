import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, login_required, logout_user, LoginManager, current_user
from werkzeug.utils import secure_filename

# Initialize Flask app
app = Flask(__name__, template_folder='templates')
app.secret_key = 'your_secret_key'

# Configure MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'santhosh'
app.config['MYSQL_PASSWORD'] = 'Balu@123580'
app.config['MYSQL_DB'] = 'DEMO'

# File Upload Configuration
# Define the path for the upload folder inside 'static/uploads'
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')

# Make sure the folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'doc', 'docx'}

# Initialize MySQL
mysql = MySQL(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

# User model class
class User(UserMixin):
    def __init__(self, id, name, email, password, role):
        self.id = id
        self.name = name
        self.email = email
        self.password = password
        self.role = role

# User loader callback function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    conn = mysql.connection
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    if user:
        return User(id=user[0], name=user[1], email=user[2], password=user[3], role=user[4])
    return None

# Function to check if the uploaded file is valid
def allowed_file(filename):
    """Check if a file has a valid extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')


@app.route('/')
def index():
    return render_template('index.html')

# Job posting route
@app.route('/job_posting', methods=['POST', 'GET'])
@login_required
def post_job():
    if request.method == 'POST':
        job_title = request.form.get('job_title')
        company_name = request.form.get('company_name')
        job_description = request.form.get('job_description')
        location = request.form.get('location')
        job_type = request.form.get('job_type')
        salary = request.form.get('salary')
        no_of_vacancies = int(request.form.get('no_of_vacancies'))

        conn = mysql.connection
        cursor = conn.cursor()

        cursor.execute(''' 
            INSERT INTO jobs (job_title, company_name, job_description, location, job_type, salary, no_of_vacancies, posted_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', (job_title, company_name, job_description, location, job_type, salary, no_of_vacancies, current_user.id))

        conn.commit()
        cursor.close()

        flash("Job posted successfully!", "success")
        return redirect(url_for('job_listing'))
    
    return render_template('job_posting.html')

# Job listing route
@app.route('/job_listing')
def job_listing():
    try:
        conn = mysql.connection
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, job_title, company_name, location, salary, job_description 
            FROM jobs
        """)
        jobs = cursor.fetchall()
        cursor.close()
    except Exception as e:
        flash(f"An error occurred while fetching jobs: {e}", "danger")
        jobs = []

    return render_template('job_listing.html', jobs=jobs)

# Job application route
@app.route('/apply/<int:id>', methods=['GET', 'POST'])
def apply(id):
    conn = mysql.connection
    cursor = conn.cursor()

    cursor.execute("SELECT job_title, company_name, job_description, location, job_type, salary FROM jobs WHERE id = %s", (id,))
    job = cursor.fetchone()

    if not job:
        cursor.close()
        flash("Job not found.", "danger")
        return redirect(url_for('job_listing'))
    
    cursor.close()

    if request.method == 'POST':
        applicant_name = request.form.get('name')
        applicant_email = request.form.get('email')
        applicant_phone = request.form.get('phone')
        resume_file = request.files.get('resume')

        if resume_file and allowed_file(resume_file.filename):
            filename = secure_filename(resume_file.filename)
            # Save the file inside 'static/uploads'
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            resume_file.save(file_path)

            try:
                cursor = conn.cursor()
                cursor.execute(''' 
                    INSERT INTO applications (job_id, name, email, phone, resume, user_id)
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', (id, applicant_name, applicant_email, applicant_phone, filename, current_user.id))
                conn.commit()
                cursor.close()

                return render_template('application_success.html', job_title=job[0], company_name=job[1])
            except Exception as e:
                flash(f"Error saving application: {e}", "danger")
                conn.rollback()
                cursor.close()
                return redirect(url_for('apply', id=id))

        else:
            flash("Invalid file type. Only PDF, DOC, and DOCX files are allowed.", "warning")
            return redirect(url_for('apply', id=id))

    return render_template('apply.html', job_id=id, job=job)

# User authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        conn = mysql.connection
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()

        if user and check_password_hash(user[3], password):  # Check hashed password
            # If user exists and password matches, login the user
            user_obj = User(id=user[0], name=user[1], email=user[2], password=user[3], role=user[4])
            login_user(user_obj)

            flash("Login successful!", "success")
            return redirect(url_for('index'))  # Redirect to a dashboard or home page

        else:
            flash('Invalid login credentials. Please try again.', 'danger')

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        mobile = request.form.get('mobile')

        conn = mysql.connection
        cursor = conn.cursor()

        # Hash password for security
        hashed_password = generate_password_hash(password)

        # Insert user into database without the role field
        cursor.execute(''' 
            INSERT INTO users (name, email, password, mobile)
            VALUES (%s, %s, %s, %s)
        ''', (name, email, hashed_password, mobile))

        conn.commit()
        cursor.close()

        flash("Signup successful! You can now log in.", "success")
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    user_id = current_user.id  # Current user's ID
    conn = mysql.connection
    cursor = conn.cursor()

        # Fetch applied jobs
    cursor.execute(""" 
            SELECT a.id, j.job_title, j.company_name, j.location, a.resume
            FROM applications a
            INNER JOIN jobs j ON a.job_id = j.id
            WHERE a.user_id = %s
        """, (user_id,))
    applied_jobs = cursor.fetchall()

        # Fetch posted jobs
    cursor.execute(""" 
            SELECT id, job_title, company_name, location, salary
            FROM jobs
            WHERE posted_by = %s
        """, (user_id,))
    posted_jobs = cursor.fetchall()
    cursor.close()

        # Render the dashboard template with the results
    return render_template(
            'dashboard.html',
            applied_jobs=applied_jobs,
            posted_jobs=posted_jobs
        )

   
    



@app.route('/view_applications/<int:job_id>')
@login_required
def view_applications(job_id):
    # Establish connection with the database
    conn = mysql.connection
    cursor = conn.cursor()

    try:
        # Execute query to fetch applications for the given job_id
        cursor.execute("""
            SELECT a.name, a.email, a.phone, a.resume
            FROM applications a
            WHERE a.job_id = %s
        """, (job_id,))
        applications = cursor.fetchall()  # Fetch all results as a list of tuples

        # Check if applications are found
        if applications:
            return render_template('view_applications.html', applications=applications, job_id=job_id)
        else:
            return render_template('view_not.html', job_id=job_id)

    except Exception as e:
        # Handle database errors
        flash("An error occurred while fetching applications: " + str(e), "danger")
        return redirect(url_for('job_listing'))

    finally:
        # Ensure the cursor is closed
        cursor.close()

@app.route('/view_not')
def view():
    return render_template('view_not.html')        


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))  # Redirect to the homepage or index

@app.route('/about_us')
def about_us():
    return render_template('about_us.html')

@app.route('/contact_us', methods=['GET', 'POST'])
@login_required
def contact_us():
    if request.method == 'POST':
        # Fetch form data
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        user_id = current_user.id  # Fetch logged-in user's ID

        if not name or not email or not message:
            flash("All fields are required.", "warning")
            return redirect(url_for('contact_us'))

        # Save the contact message to the database
        try:
            conn = mysql.connection
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO contact_messages (user_id, name, email, message)
                VALUES (%s, %s, %s, %s)
            """, (user_id, name, email, message))
            conn.commit()
            cursor.close()

            flash("Your message has been sent successfully!", "success")
            return redirect(url_for('index'))
        except Exception as e:
            flash(f"An error occurred: {e}", "danger")
            return redirect(url_for('contact_us'))

    return render_template('contact_us.html')  # Renders your HTML template



@app.route('/career_guidance')
def career_guidance():
    career_options = [
        "Software Development",
        "Data Science and Analytics",
        "UI/UX Design",
        "Project Management",
        "Quality Assurance",
        "DevOps Engineering"
    ]
    return render_template('career_guidance.html', options=career_options)



    # Define additional job category routes with corrections
@app.route('/software_dev', methods=['GET'])
def software_dev():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, job_title, company_name, job_description, location, job_type, salary, no_of_vacancies FROM jobs WHERE job_title IN ('software developer', 'web developer', 'software engineer')")
    jobs = cursor.fetchall()
    cursor.close()
    return render_template('software_dev.html', jobs=jobs)


@app.route('/data_science',methods=['GET'])
def data_science():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, job_title, company_name, job_description, location, job_type, salary, no_of_vacancies FROM jobs WHERE job_title IN ('data scientist', 'data analytics')")
    jobs = cursor.fetchall()
    cursor.close()
    return render_template('data_science.html', jobs=jobs)

@app.route('/u_design',methods=['GET'])
def u_design():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, job_title, company_name, job_description, location, job_type, salary, no_of_vacancies FROM jobs WHERE job_title IN ('UX', 'UI', 'UI/UX design')")
    jobs = cursor.fetchall()
    cursor.close()
    return render_template('u_design.html', jobs=jobs)

@app.route('/product_man',methods=['GET'])
def product_manager():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, job_title, company_name, job_description, location, job_type, salary, no_of_vacancies FROM jobs WHERE job_title IN ('product manager', 'product designer')")
    jobs = cursor.fetchall()
    cursor.close()
    return render_template('product_man.html', jobs=jobs)

@app.route('/customer_support',methods=['GET'])
def customer_support():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, job_title, company_name, job_description, location, job_type, salary, no_of_vacancies FROM jobs WHERE job_title IN ('customer support', 'customer care')")
    jobs = cursor.fetchall()
    cursor.close()
    return render_template('customer_support.html', jobs=jobs)

@app.route('/sales_ex',methods=['GET'])
def sales_ex():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, job_title, company_name, job_description, location, job_type, salary, no_of_vacancies FROM jobs WHERE job_title IN ('sales person', 'sales executive')")
    jobs = cursor.fetchall()
    cursor.close()
    return render_template('sales_ex.html', jobs=jobs)

@app.route('/teacher',methods=['GET'])
def teaching():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, job_title, company_name, job_description, location, job_type, salary, no_of_vacancies FROM jobs WHERE job_title IN ('tutor', 'teaching')")
    jobs = cursor.fetchall()
    cursor.close()
    return render_template('teacher.html', jobs=jobs)

@app.route('/human_res',methods=['GET'])
def human_res():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, job_title, company_name, job_description, location, job_type, salary, no_of_vacancies FROM jobs WHERE job_title = 'human resources'")
    jobs = cursor.fetchall()
    cursor.close()
    return render_template('human_res.html', jobs=jobs)

@app.route('/business_dev',methods=['GET'])
def business_dev():
    cursor= mysql.connection.cursor()
    cursor.execute("SELECT id, job_title, company_name, job_description, location, job_type, salary, no_of_vacancies FROM jobs WHERE job_title IN ('Business Development','business development manager')")
    jobs = cursor.fetchall()
    cursor.close()
    return render_template('business_dev.html', jobs=jobs)


@app.route('/search_jobs', methods=['GET'])
def search_jobs():
    search_query = request.args.get('query', '').strip()
    
    # Establish connection
    conn = mysql.connection
    cursor = conn.cursor()

    try:
        # Use parameterized query to avoid special character issues and SQL injection
        cursor.execute("""
            SELECT id, job_title, company_name, location, salary, job_description
            FROM jobs
            WHERE job_title LIKE %s OR company_name LIKE %s OR location LIKE %s OR job_type LIKE %s
        """, (f"%{search_query}%", f"%{search_query}%", f"%{search_query}%",f"%{search_query}"))
        jobs = cursor.fetchall()
    except Exception as e:
        flash(f"Error occurred while searching: {e}", "danger")
        jobs = []
    finally:
        cursor.close()

    return render_template('job_listing.html', jobs=jobs, search_query=search_query)
@app.route('/delete_job/<int:job_id>', methods=['POST'])
@login_required
def delete_job(job_id):
    try:
        conn = mysql.connection
        cursor = conn.cursor()

        # Ensure the user owns the job (for security)
        cursor.execute("SELECT id FROM jobs WHERE id = %s AND posted_by = %s", (job_id, current_user.id))
        job = cursor.fetchone()

        if not job:
            flash("Job not found or you don't have permission to delete it.", "danger")
            return redirect(url_for('dashboard'))

        # Execute delete query
        cursor.execute("DELETE FROM jobs WHERE id = %s", (job_id,))
        conn.commit()

        flash("Job deleted successfully!", "success")
    except Exception as e:
        conn.rollback()
        flash(f"An error occurred: {e}", "danger")
    finally:
        cursor.close()

    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    app.run(debug=True)
