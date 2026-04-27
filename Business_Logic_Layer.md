# AI-Based Automated Test Case Generation Integrated with CI/CD

## Business Logic Layer (BLL) Assignment

---

#  Introduction

A **Business Logic Layer (BLL)** is responsible for implementing the core functionality and rules of an application. In this project, the BLL acts as a bridge between:

* **Presentation Layer** → Flask UI (`webapp.py`)
* **Backend API / Dashboard** → Node.js (`Backend/src/app.js`)
* **Processing Layer** → Python AI engine (`app.py`, `stage0_compile.py`)

The BLL ensures that:

* Code is analyzed correctly
* Test cases are generated logically
* CI/CD results are validated and processed

---

#  Core Functional Modules in Business Logic Layer

##  1. Code Processing Module

**File:** `stage0_compile.py`

### Function:

* Reads submitted code (uploaded or from repo)
* Checks for syntax/compile errors
* Prepares code for AI processing

### Interaction with UI:

* User uploads file via Flask UI (`webapp.py`)
* UI sends file → `process_submission()`
* BLL processes file and returns result

---

## 2. AI Test Case Generation Module

**File:** `app.py`

### Function:

* Sends code to AI model
* Generates:

  * Unit test cases
  * Edge cases
  * Error detection insights

### Interaction with UI:

* UI triggers AI processing
* Output is displayed on dashboard

---

##  3. CI/CD Integration Module

**File:** GitHub Actions Workflow

### Function:

* Triggered on GitHub push
* Runs:

  * AI test generator
  * Build check
  * Test execution

### Interaction:

* Pipeline result → sent to backend API
* Backend updates dashboard

---

##  4. Test Execution Module

**File:** `runTests.js` (Node)

### Function:

* Reads generated test cases
* Executes them on code
* Produces:

  * Pass/Fail results
  * Logs

### Interaction with UI:

* Results stored in backend
* UI displays test outcomes

---

##  5. Dashboard & Result Module

**File:** `Backend/src/app.js`

### Function:

* Receives pipeline results via API
* Stores logs/results
* Sends data to frontend dashboard

### Interaction with UI:

* Displays:

  * Success/Failure
  * Error logs
  * Execution status

---

# Interaction Flow (BLL + UI)

```text
User (UI - Flask)
      ↓
Upload Code / Select Sample
      ↓
BLL → Code Processing
      ↓
BLL → AI Test Generation
      ↓
CI/CD Pipeline Runs Tests
      ↓
Backend API Stores Result
      ↓
UI Dashboard Displays Output
```

---

#  Business Rules Implementation

The system follows several business rules:

###  1. Code Validation Rule

* Code must be syntactically correct before testing
* If compile error → pipeline stops

###  2. Test Generation Rule

* AI generates tests only for modified files
* Includes:

  * Normal cases
  * Edge cases
  * Invalid inputs

###  3. Execution Rule

* If any test fails → pipeline marked as failed
* If all tests pass → success

###  4. Dashboard Rule

* Every pipeline run must:

  * Store logs
  * Show status (success/failure)

---

#  Validation Logic

Validation ensures correct input before processing.

###  Implemented Validations:

#### 1. File Validation

* Only valid code files accepted
* Empty files rejected

#### 2. Syntax Validation

* Python: `py_compile`
* Node: `npm run build`

#### 3. Test Output Validation

* Checks:

  * Failed tests
  * Runtime errors

#### 4. API Validation

* Backend ensures:

  * Required fields exist (`status`, `logs`)
  * Proper JSON format

---

# Data Transformation

Data transformation ensures compatibility between layers.

###  1. Code → AI Input

* Raw code converted into structured prompt

###  2. AI Output → Test Format

Example:

```json
{
  "input": "2+2",
  "expected": 4
}
```

Converted into executable test scripts

---

###  3. Test Results → Dashboard Format

Raw output:

```
Test 1 Passed
Test 2 Failed
```

Transformed into:

```json
{
  "status": "failed",
  "passed": 1,
  "failed": 1
}
```

---

###  4. API Response Transformation

Backend converts:

* Logs → readable format
* Status → UI-friendly labels

---

#  Conclusion

The Business Logic Layer in this project:

* Handles AI-based test generation
* Ensures proper validation and execution
* Integrates with CI/CD pipeline
* Provides structured results to the dashboard

This architecture ensures:

* Automation
* Reliability
* Scalability

---
