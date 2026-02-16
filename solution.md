# Software Architecture for AI-Based Automated Test Case Generation Integrated with CI/CD



# I. Software Architecture Style Chosen

## Microservices Architecture

---

## A. Justification Based on Granularity

### Why it is Microservices

- System is divided into independent services.
- Each service handles a specific business capability.
- Services communicate via webhooks and HTTP APIs.
- Components can be deployed independently.
- High cohesion and low coupling between modules.

### Granularity of Software Components

Each service performs one well-defined responsibility:

1. Webhook Service  
   - Receives Git commit events.  
   - Extracts metadata and changed files.

2. AI Test Generation Service  
   - Analyzes source code.  
   - Generates unit/API test cases.

3. CI/CD Execution Service  
   - Executes generated tests.  
   - Collects logs and coverage reports.

4. Dashboard Service  
   - Displays results and logs.  
   - Shows pipeline status.

5. File Processing Service  
   - Reads and parses uploaded code files.  
   - Structures data for AI processing.

Each component:
- Is independently deployable.
- Can scale independently.
- Can be modified without affecting other services.

---

## Architecture Diagram (Logical Representation)

                +------------------+
                |   Developer Push |
                +------------------+
                         |
                         v
                +------------------+
                |  Webhook Service |
                +------------------+
                         |
                         v
                +---------------------------+
                | AI Test Generation Service|
                +---------------------------+
                         |
                         v
                +------------------+
                |  CI/CD Pipeline  |
                +------------------+
                         |
                         v
                +------------------+
                |    Dashboard     |
                +------------------+

---

## B. Why Microservices is the Best Choice

### Scalability
- AI service can scale independently (CPU intensive).
- CI runners can scale horizontally.
- Dashboard and backend can scale separately.

### Maintainability
- Backend (Node.js) separated from AI (Python).
- Easier debugging and updates.
- Independent deployment of services.

### Performance
- Parallel execution of AI generation and CI/CD pipeline.
- Reduced bottlenecks.
- Faster feedback loop for developers.

### Technology Flexibility
- Python for AI processing.
- Node.js for backend.
- Flask for web UI.
- GitHub Actions or other CI tools.

### Fault Isolation
- Failure in AI module does not crash entire system.
- Better system reliability and resilience.

---

# II. Application Components

1. Webhook Handler
   - Receives commit events.
   - Triggers test generation workflow.

2. AI Test Case Generator
   - Analyzes code changes.
   - Generates automated test cases.

3. File Processing Module
   - Reads uploaded or changed files.
   - Extracts functions/classes.

4. CI/CD Integration Module
   - Runs generated tests.
   - Produces logs and coverage metrics.

5. Dashboard (Flask Web UI)
   - Upload/select files.
   - Display generated tests and results.

6. Backend Service (Node.js)
   - Manages webhook handling.
   - Coordinates AI and CI/CD services.

7. Storage Component
   - Stores uploaded files.
   - Saves generated test cases.
   - Stores logs and reports.

---
<p align="center">
  <img src="./diagram.png" alt="Diagram" style="max-width:100%;height:auto;">
</p>

# Conclusion

The project follows Microservices Architecture because it consists of loosely coupled, independently deployable services communicating through APIs and events. This ensures scalability, maintainability, performance optimization, and fault isolation in an AI-driven CI/CD system.
