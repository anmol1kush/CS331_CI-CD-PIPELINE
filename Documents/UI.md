# User Interface Design and Implementation

## I. Choice of User Interface

For the project **“AI-Based Automated Test Case Generation Integrated with CI/CD”**, the chosen user interface is a **Menu-Based Graphical Web Interface** implemented using **React.js for the frontend** and **Node.js with Express.js for the backend**.

### Type of UI Selected

**Menu-Based Graphical Web Interface**

This interface allows users to interact with the system through graphical components such as:

* Buttons
* File upload fields
* Dashboard panels
* Navigation menus
* Result display sections

Instead of typing commands, users interact with the system through visual components in a web browser.

---

# Justification for Choosing React + Node UI

## 1. User Friendly Interface

React provides an interactive and responsive UI where users can easily upload files, trigger AI processing, and view results.

## 2. Real-Time Interaction

React allows dynamic UI updates without refreshing the page. When test cases are generated, results can immediately appear on the dashboard.

## 3. Scalability

Using **React + Node.js microservice architecture** allows the system to scale easily when more users or CI/CD processes are added.

## 4. Integration with CI/CD

The backend built with **Node.js and Express.js** can handle:

* GitHub Webhooks
* Test generation requests
* Communication with AI modules
* Logging and dashboard data

## 5. Modern Web Development

React is widely used in industry, making the system easier to maintain and extend.

---

# System Architecture for UI


User (Browser)
│
▼
React Frontend
│
REST API Requests
│
▼
Node.js + Express Backend
│
▼
AI Test Generation Engine (Python Worker)
│
▼
CI/CD Pipeline (GitHub Actions)


---

# UI Components Implemented

The React frontend consists of several UI components.

| Component            | Description                                         |
| -------------------- | --------------------------------------------------- |
| Navigation Bar       | Allows navigation between dashboard and upload page |
| File Upload Form     | Allows developers to upload source code             |
| Sample File Selector | Allows selecting example files                      |
| Generate Test Button | Triggers AI test case generation                    |
| Results Panel        | Displays generated test cases                       |
| Logs Section         | Shows execution logs and CI/CD results              |

---

# User Interaction with the System

## Step 1

The user opens the web application in a browser.


http://localhost:5173


## Step 2

The dashboard appears with options to upload a file.

## Step 3

The user selects a source code file.

Example:


login_service.js


## Step 4

The user clicks **Generate Test Cases**.

## Step 5

The request is sent to the **Node.js backend API**.

## Step 6

The backend calls the **AI module to generate test cases**.

## Step 7

The generated tests and logs are displayed on the **UI dashboard**.