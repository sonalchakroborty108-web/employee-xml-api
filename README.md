# Employee XML CRUD API

A production-ready, lightweight REST API built with Flask that handles requests and responses exclusively in XML format. It features automatic generation of 100 employee records, local file-based JSON persistence, secure XML parsing using `defusedxml`, and is configured for instant deployment to Render.

## Features

- 🌐 **XML-Only Endpoints**: All requests (POST, PUT) accept XML, and all responses return valid XML.
- 👥 **100 Auto-Generated Employees**: On first run, if the data file is missing, the application automatically generates 100 realistic employee records.
- 💾 **File-Based Persistence**: No database configuration required. Data is persisted to a local `employees.json` file.
- 🔒 **Security**: Uses `defusedxml` to prevent XML External Entity (XXE) injection and expansion attacks.
- 🚀 **Render Ready**: Includes `render.yaml` for free hosting.

---

## Endpoints

| Method | Endpoint | Description | Request Body (XML) | Response Body (XML) |
|---|---|---|---|---|
| **GET** | `/employees` | List all employees | None | List of all `<Employee>` entries |
| **GET** | `/employees/<id>` | Get a single employee | None | Single `<Employee>` detail |
| **POST** | `/employees` | Create a new employee | `<Employee>` (exclude ID) | Created `<Employee>` with new ID |
| **PUT** | `/employees/<id>` | Update an employee | `<Employee>` (fields to update) | Updated `<Employee>` |
| **DELETE** | `/employees/<id>` | Delete an employee | None | Success confirmation message |

---

## Example XML Formats

### 1. Single Employee
```xml
<Employee>
    <Id>1</Id>
    <Name>Alice Smith</Name>
    <Email>alice.smith@example.com</Email>
    <Department>Engineering</Department>
    <Role>Senior Software Engineer</Role>
    <Salary>95000</Salary>
</Employee>
```

### 2. Error Response
```xml
<Error>
    <Message>Employee not found</Message>
</Error>
```

### 3. Success Response
```xml
<Success>
    <Message>Employee deleted successfully</Message>
</Success>
```

---

## Running Locally

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Flask app**:
   ```bash
   python app.py
   ```
   The application will start on `http://127.0.0.1:5000/`.
   On the first request or startup, it will automatically generate `employees.json` with 100 records if the file doesn't already exist.

---

## Deploying to Render

1. Create a new GitHub repository and push this project's files.
2. Log in to [Render](https://render.com/).
3. Click **New +** and select **Blueprint**.
4. Connect your GitHub repository.
5. Render will automatically detect the `render.yaml` and configure the service for you!
