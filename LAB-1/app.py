import json
import os
from flask import Flask, render_template, request, redirect, url_for, flash, g
import time
import logging
from logging.handlers import RotatingFileHandler

# OpenTelemetry Imports
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes


# Flask App Initialization
app = Flask(__name__)
app.secret_key = 'secret'
COURSE_FILE = 'course_catalog.json'  # File to store Course data
TELEMETRY_FILE = 'telemetry_data.json'  # File to store Telemetry data

# Set up the TracerProvider with the resource
trace.set_tracer_provider(
    TracerProvider(
        resource=Resource.create({ResourceAttributes.SERVICE_NAME: "CourseCatalog_App"})
    )
)
jaeger_exporter = JaegerExporter(
    agent_host_name="localhost",
    agent_port=6831,
)
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(jaeger_exporter))
tracer = trace.get_tracer(__name__)


# Telemetry Data Storage
telemetry_data = {
    "route_requests": {},
    "route_processing_time": {},
    "errors": {}
}


# Initialize Tracer Provider
# trace.set_tracer_provider(TracerProvider())
# tracer = trace.get_tracer(__name__)
logging_exporter = ConsoleSpanExporter()
span_processor = BatchSpanProcessor(logging_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# Instrumenting Flask with OpenTelemetry
FlaskInstrumentor().instrument_app(app)

# Structured Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    filename="request_log.json",
    filemode="a"
)



#logging Setup
# logging.basicConfig(level=logging.INFO, filename="request_log.log", filemode="a")


# Logging Configuration
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

# Custom JSON Formatter for logging
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'message': record.getMessage(),
            'logger_name': record.name,
            'path': record.pathname,
        }
        return json.dumps(log_record)


# File logging with rotation
file_handler = RotatingFileHandler('application.log', maxBytes=5 * 1024 * 1024, backupCount=2)
file_handler.setFormatter(JsonFormatter())

# Basic logging configuration
logging.basicConfig(level=logging.DEBUG)
handler = logging.StreamHandler()
logger = logging.getLogger('JsonLogger')

handler.setFormatter(JsonFormatter())
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)
logger.addHandler(handler)


# Utility Functions
def load_courses():
    """Load courses from the JSON file."""
    with tracer.start_as_current_span("load_courses") as span:
        if not os.path.exists(COURSE_FILE):
            span.set_attribute("Error in Finding courses")
            return []  # Return an empty list if the file doesn't exist
        with open(COURSE_FILE, 'r') as file:
            courses = json.load(file)
            span.set_attribute("course found = ", len(courses))
            return courses


def save_courses(data):
    with tracer.start_as_current_span("save_courses") as span:
        """Save new course data to the JSON file."""
        span.set_attribute("course.name", data["name"])
        span.set_attribute("course.code", data["code"])
        courses = load_courses()  # Load existing courses
        courses.append(data)  # Append the new course
        with open(COURSE_FILE, 'w') as file:
            json.dump(courses, file, indent=4)
    logger.info(f"Course added: {data['name']} (Code: {data['code']})")

def save_telemetry():
    """Save telemetry data to the JSON file."""
    with open(TELEMETRY_FILE, 'w') as file:
        json.dump(telemetry_data, file, indent=4)


# Telemetry Utility
@app.before_request
def before_request():
    """Track the start time and increment request count for the route."""
    g.start_time = time.time()
    route = request.endpoint
    telemetry_data["route_requests"].setdefault(route, 0)
    telemetry_data["route_requests"][route] += 1
    logger.info(f"Processing request for route: {route}")

@app.after_request
def after_request(response):
    """Track the processing time for the route."""
    route = request.endpoint
    processing_time = time.time() - g.start_time
    telemetry_data["route_processing_time"].setdefault(route, 0)
    telemetry_data["route_processing_time"][route] += processing_time
    logger.info(f"Route '{route}' processed in {processing_time:.4f} seconds")
    save_telemetry()
    return response

def log_error(error_message):
    """Log an error message."""
    telemetry_data["errors"].setdefault(error_message, 0)
    telemetry_data["errors"][error_message] += 1
    logger.error(error_message)
    save_telemetry()

# Routes
@app.route('/')
def index():
    with tracer.start_as_current_span("render_index_page", attributes={"user_ip": request.remote_addr}) as span:
        span.set_attribute("http.method", request.method)
        span.set_attribute("client.ip", request.remote_addr)
        logger.info("Rendering index page")
        logging.info("User Accessed the Index page.")
        return render_template('index.html')

@app.route('/catalog')
def course_catalog():
    with tracer.start_as_current_span("render_course_catalog", attributes={"user_ip": request.remote_addr}) as span:
        span.set_attribute("http.method", request.method)
        span.set_attribute("client.ip", request.remote_addr)
        courses = load_courses()
        span.set_attribute("course.count", len(courses))
        courses = load_courses()
        logger.info("Rendering course catalog page")
        logging.info("User Accessed the course_catalog page.")
        return render_template('course_catalog.html', courses=courses)

@app.route('/addCourse', methods=['GET', 'POST'])
def add_course():
    with tracer.start_as_current_span("handle_add_course_form", attributes={"user_ip": request.remote_addr, "request_method": request.method}) as span:
        if request.method == 'POST':
            span.set_attribute("http.method", request.method)
            span.set_attribute("client.ip", request.remote_addr)
            logging.info("User request to add new Course.")

            # Collecting form data
            required_fields = {
                "code": request.form['code'],
                "name": request.form['name'],
                "instructor": request.form['instructor'],
                "semester": request.form['semester'],
                "schedule": request.form['schedule'],
                "classroom": request.form['classroom'],
                "grading": request.form['grading'],
                "description": request.form['description']
            }

            # Check for missing fields
            missing_fields = [field for field, value in required_fields.items() if not value]

            if missing_fields:
                if len(missing_fields) <= 3:
                    flash(f"The following fields are required: {', '.join(missing_fields)}", "danger")
                else:
                    flash("All fields are required!", "danger")

                logging.warning("User failed to add Course:- Form submission error: Missing fields")
                app.logger.error(f"Form submission error: Missing fields: {', '.join(missing_fields)}")
                logging.info("User is Redirected to course_catalog page.")
                return redirect(url_for('add_course'))
            
            # If all fields are provided, save the course
            new_course = {
                **required_fields,
                "Prerequisites": request.form['prerequisites']  # Optional field
            }

            # Save data and give feedback
            save_courses(new_course)
            flash("Course added successfully!", "success")
            logging.info("User added Course " + new_course['code'] + ".")
            logging.info("User Accessed the course_catalog page.")
            return redirect(url_for('course_catalog'))

        logging.info("User Accessed the add_course page.")
        return render_template('add_course.html')

@app.route('/course/<code>')
def course_details(code):
    with tracer.start_as_current_span("render_course_details", attributes={"user_ip": request.remote_addr, "course_code": code})as span:
        span.set_attribute("http.method", request.method)
        span.set_attribute("client.ip", request.remote_addr)
        span.set_attribute("course.code", code)
        courses = load_courses()
        course = next((course for course in courses if course['code'] == code), None)
    if not course:
        error_message = f"No course found for the code '{code}'."
        span.set_attribute("error.message", error_message)
        span.set_attribute("course.exists", False)
        flash(f"No course found with code '{code}'.", "error")
        logging.info("User Accessed the course_catalog page.")
        return redirect(url_for('course_catalog'))
    logging.info("User Accessed the course_details code: " + code + " page.")
    return render_template('course_details.html', course=course)

if __name__ == '__main__':
    app.run(debug=True)
    # app.run(host="0.0.0.0", debug=True)
