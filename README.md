# AI-Based Automated Test Case Generation Integrated with CI/CD

## 📌 Project Overview

This project implements an **AI-driven automated test case generation system** integrated with a **CI/CD pipeline**.  
The system is **event-driven**, where **code commits automatically trigger AI-based test generation and CI/CD execution**.

A **read-only frontend dashboard** is provided to visualize:
- Commit activity
- Test results
- Execution logs

The project demonstrates modern **Software Engineering principles**, **DevOps practices**, and **AI-assisted automation**.

---

## 🎯 Objectives

- Automate test case generation using AI  
- Trigger CI/CD pipelines automatically on code commits  
- Reduce manual testing effort  
- Provide real-time visibility into commits, test results, and logs  
- Demonstrate scalable and modular system design  

---

## 📊 Requirement Analysis

### 🔹 Functional Requirements

- The system shall detect code commits automatically.
- The system shall trigger a webhook on every commit.
- The system shall generate unit and API test cases using AI.
- The system shall execute generated tests via a CI/CD pipeline.
- The system shall store test results, logs, and coverage data.
- The system shall display commit analytics on the dashboard.
- The system shall display test results and logs on the dashboard.

---

### 🔹 Non-Functional Requirements

- **Automation:** No manual intervention for test generation  
- **Scalability:** Handle multiple commits and contributors  
- **Reliability:** Ensure accurate test execution and logging  
- **Maintainability:** Modular and clean codebase  
- **Security:** Restricted dashboard access for authorized users  

---

## 🔄 System Flow (Detailed)

### Step-by-Step Flow

#### 1. Code Commit
- Developer pushes code to the Git repository.

#### 2. Webhook Trigger
- GitHub automatically sends a webhook event to the backend.

#### 3. Backend Orchestration
- Node.js backend parses commit data and changed files.
- Commit metadata is stored in the database.

#### 4. AI Test Case Generation
- AI analyzes code changes.
- Unit and API test cases are generated automatically.

#### 5. CI/CD Pipeline Execution
- GitHub Actions pipeline is triggered.
- Project is built and generated tests are executed.

#### 6. Result Storage
- Test results, logs, and coverage reports are stored in the database.

#### 7. Dashboard Visualization
- Frontend dashboard displays:
  - Who committed code
  - Number of commits per user
  - Test pass/fail status
  - Logs and coverage trends

---
## 🔁 Flow Summary

1. **Developer Commit/Push** → A developer pushes code changes to the GitHub repository.  
2. **Webhook Triggered** → GitHub sends a webhook event to the backend automatically.  
3. **Backend Orchestration** → Node.js backend extracts commit + changed file metadata and stores it in the database.  
4. **AI Test Generation** → AI analyzes the changes and generates **unit + API test cases** automatically.  
5. **CI/CD Execution** → GitHub Actions pipeline builds the project and runs the generated tests.  
6. **Results Stored** → Test results, logs, and coverage reports are saved in the database.  
7. **Dashboard Updated** → Frontend dashboard shows commit analytics, test status, logs, and coverage trends.

---

## 📌 Use Case Diagram

![Use Case Diagram](./use_case_diagram.png)


