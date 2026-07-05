import os
import json
import random
from flask import Flask, request, make_response
import defusedxml.ElementTree as ET
from threading import Lock

app = Flask(__name__)
DATA_FILE = os.path.join(os.path.dirname(__file__), 'employees.json')
db_lock = Lock()

# Helper list of departments and roles for data generation
DEPT_ROLES = {
    'Engineering': ['Software Engineer', 'Senior Software Engineer', 'QA Engineer', 'DevOps Engineer', 'Engineering Manager'],
    'Product': ['Product Manager', 'Associate Product Manager', 'UX Designer', 'Lead Designer'],
    'Marketing': ['Marketing Specialist', 'SEO Specialist', 'Marketing Manager'],
    'Sales': ['Sales Representative', 'Account Executive', 'Sales Director'],
    'HR': ['HR Associate', 'HR Manager', 'Recruiter'],
    'Finance': ['Accountant', 'Financial Analyst', 'Finance Manager'],
    'Support': ['Support Representative', 'Support Engineer', 'Support Lead']
}

def init_db():
    """Generates exactly 100 unique employee records if employees.json does not exist."""
    if not os.path.exists(DATA_FILE):
        first_names = [
            'John', 'Jane', 'Alice', 'Bob', 'Charlie', 'Diana', 'Ethan', 'Fiona', 'George', 'Hannah', 
            'Ian', 'Julia', 'Kevin', 'Laura', 'Michael', 'Nicole', 'Oliver', 'Patricia', 'Quincy', 
            'Rachel', 'Steven', 'Tiffany', 'Victor', 'Wendy', 'Zachary', 'Emily', 'Daniel', 'Sophia', 
            'Matthew', 'Olivia'
        ]
        last_names = [
            'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 
            'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson', 'Thomas', 'Taylor', 
            'Moore', 'Jackson', 'Martin', 'Lee', 'Perez', 'Thompson', 'White', 'Harris', 'Sanchez', 
            'Clark', 'Ramirez', 'Lewis', 'Robinson'
        ]
        
        employees = []
        random.seed(42)  # Seed for reproducible random dataset
        
        for idx in range(1, 101):
            first = random.choice(first_names)
            last = random.choice(last_names)
            dept = random.choice(list(DEPT_ROLES.keys()))
            role = random.choice(DEPT_ROLES[dept])
            salary = random.randint(50, 150) * 1000  # $50k to $150k
            
            email = f"{first.lower()}.{last.lower()}.{idx}@example.com"
            employees.append({
                'id': idx,
                'name': f"{first} {last}",
                'email': email,
                'department': dept,
                'role': role,
                'salary': salary
            })
            
        with open(DATA_FILE, 'w') as f:
            json.dump(employees, f, indent=4)

init_db()

# DB Helper Functions
def load_employees():
    with db_lock:
        if not os.path.exists(DATA_FILE):
            init_db()
        with open(DATA_FILE, 'r') as f:
            return json.load(f)

def save_employees(employees):
    with db_lock:
        with open(DATA_FILE, 'w') as f:
            json.dump(employees, f, indent=4)

# XML Serialization & Deserialization Helpers
def dict_to_xml_element(tag_name, d):
    """Converts a flat dictionary into an ET.Element representation."""
    elem = ET.Element(tag_name)
    for key, val in d.items():
        # Clean formatting for XML tags (e.g. name -> Name, id -> Id)
        tag_key = key.capitalize() if key != 'id' else 'Id'
        child = ET.SubElement(elem, tag_key)
        child.text = str(val)
    return elem

def make_xml_response(xml_element, status_code=200):
    """Wraps an XML element in a Flask response with the correct Content-Type header."""
    rough_string = ET.tostring(xml_element, encoding='utf-8')
    xml_data = b'<?xml version="1.0" encoding="utf-8"?>\n' + rough_string
    response = make_response(xml_data, status_code)
    response.headers['Content-Type'] = 'application/xml'
    return response

def error_xml(message):
    """Helper to return an error XML structure."""
    root = ET.Element('Error')
    msg = ET.SubElement(root, 'Message')
    msg.text = message
    return root

def success_xml(message):
    """Helper to return a success XML structure."""
    root = ET.Element('Success')
    msg = ET.SubElement(root, 'Message')
    msg.text = message
    return root

def parse_xml_request(data):
    """Parses incoming request XML safely using defusedxml."""
    try:
        root = ET.fromstring(data)
        parsed_dict = {}
        for child in root:
            key = child.tag.lower()
            val = child.text.strip() if child.text else ""
            if key == 'salary':
                parsed_dict[key] = int(val) if val.isdigit() else 0
            else:
                parsed_dict[key] = val
        return parsed_dict, None
    except ET.ParseError:
        return None, "Malformed XML payload."
    except Exception as e:
        return None, str(e)


# Flask Endpoints

@app.route('/employees', methods=['GET'])
def get_employees():
    """Retrieve all employees in XML format."""
    # Support query parameter filtering (e.g., /employees?department=Engineering)
    dept_filter = request.args.get('department')
    
    employees = load_employees()
    
    if dept_filter:
        employees = [emp for emp in employees if emp['department'].lower() == dept_filter.lower()]
        
    root = ET.Element('Employees')
    for emp in employees:
        emp_elem = dict_to_xml_element('Employee', emp)
        root.append(emp_elem)
        
    return make_xml_response(root)

@app.route('/employees/<int:employee_id>', methods=['GET'])
def get_employee(employee_id):
    """Retrieve a single employee by ID in XML format."""
    employees = load_employees()
    employee = next((emp for emp in employees if emp['id'] == employee_id), None)
    
    if not employee:
        return make_xml_response(error_xml(f"Employee with ID {employee_id} not found"), 404)
        
    root = dict_to_xml_element('Employee', employee)
    return make_xml_response(root)

@app.route('/employees', methods=['POST'])
def create_employee():
    """Create a new employee from XML payload."""
    if not request.data:
        return make_xml_response(error_xml("Empty request body. XML payload expected."), 400)
        
    parsed_data, error = parse_xml_request(request.data)
    if error:
        return make_xml_response(error_xml(error), 400)
        
    # Validation
    required_fields = ['name', 'email', 'department', 'role', 'salary']
    missing_fields = [f.capitalize() for f in required_fields if f not in parsed_data or not parsed_data[f]]
    if missing_fields:
        return make_xml_response(error_xml(f"Missing required fields: {', '.join(missing_fields)}"), 400)
        
    employees = load_employees()
    
    # Check if email is unique
    if any(emp['email'].lower() == parsed_data['email'].lower() for emp in employees):
        return make_xml_response(error_xml("Employee with this email already exists"), 409)
        
    # Generate auto-incrementing ID
    next_id = max(emp['id'] for emp in employees) + 1 if employees else 1
    
    new_employee = {
        'id': next_id,
        'name': parsed_data['name'],
        'email': parsed_data['email'],
        'department': parsed_data['department'],
        'role': parsed_data['role'],
        'salary': parsed_data['salary']
    }
    
    employees.append(new_employee)
    save_employees(employees)
    
    root = dict_to_xml_element('Employee', new_employee)
    return make_xml_response(root, 201)

@app.route('/employees/<int:employee_id>', methods=['PUT'])
def update_employee(employee_id):
    """Update an existing employee from XML payload."""
    if not request.data:
        return make_xml_response(error_xml("Empty request body. XML payload expected."), 400)
        
    parsed_data, error = parse_xml_request(request.data)
    if error:
        return make_xml_response(error_xml(error), 400)
        
    employees = load_employees()
    employee = next((emp for emp in employees if emp['id'] == employee_id), None)
    
    if not employee:
        return make_xml_response(error_xml(f"Employee with ID {employee_id} not found"), 404)
        
    # Check email uniqueness if email is being updated
    if 'email' in parsed_data and parsed_data['email'] != employee['email']:
        if any(emp['email'].lower() == parsed_data['email'].lower() for emp in employees):
            return make_xml_response(error_xml("Employee with this email already exists"), 409)
            
    # Apply updates
    for field in ['name', 'email', 'department', 'role', 'salary']:
        if field in parsed_data:
            employee[field] = parsed_data[field]
            
    save_employees(employees)
    
    root = dict_to_xml_element('Employee', employee)
    return make_xml_response(root)

@app.route('/employees/<int:employee_id>', methods=['DELETE'])
def delete_employee(employee_id):
    """Delete an employee by ID."""
    employees = load_employees()
    employee = next((emp for emp in employees if emp['id'] == employee_id), None)
    
    if not employee:
        return make_xml_response(error_xml(f"Employee with ID {employee_id} not found"), 404)
        
    employees = [emp for emp in employees if emp['id'] != employee_id]
    save_employees(employees)
    
    return make_xml_response(success_xml(f"Employee with ID {employee_id} deleted successfully"))

# Health check endpoint
@app.route('/health', methods=['GET'])
def health():
    root = ET.Element('Status')
    root.text = 'Healthy'
    return make_xml_response(root)

if __name__ == '__main__':
    # Start local server
    app.run(host='0.0.0.0', port=5000, debug=True)
