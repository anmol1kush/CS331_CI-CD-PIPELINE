# CS 331 – Software Engineering Lab

## Assignment 5 – Deployment & Component Interaction

### Project Title

**AI-Based Automated Test Case Generation Integrated with CI/CD**

---

## I. Hosting of Application Components 

### Application Components

- Frontend (Flask Web UI)
- Backend API (Node.js)
- AI Test Generator (Python – single AI container)
- Database (MongoDB)

---

### Host Site

- **Platform**: Docker (local / cloud-ready)
- **Deployment Type**: Containerized using Docker Compose
- **Hosting Environment**:
  - Can run on any Linux server / cloud VM (AWS EC2, GCP VM, Azure VM)
  - All services run as isolated Docker containers

---

### Deployment Strategy

1. Each application component is packaged into a Docker container
2. AI logic (test generation, code analysis) is deployed as **one single AI container**
3. `docker-compose.yml` is used to orchestrate all containers
4. Services communicate using Docker’s internal network
5. Ports are exposed only for frontend access
6. Environment variables are used for configuration
7. Containers are started using:
   ```bash
   docker-compose up --build -d
   ```

### Security Measures 

- Containers communicate over a private Docker network
- Only frontend port is publicly exposed
- API keys and secrets stored using environment variables
- Database access restricted to backend container only

---

## II. End User Access & System Interaction 

### How End Users Access the System

- Users access the system via a **web browser**
- Frontend runs on:

  ```
  http://localhost:5000
  ```

- Users can:
  - Upload source code files
  - Trigger AI-based test generation
  - View generated test cases and logs

---

### System Interaction Flow

1. User interacts with the Flask frontend
2. Frontend sends request to Backend API
3. Backend invokes AI Test Generator container
4. AI container generates test cases
5. Results are stored/logged
6. Response is sent back to frontend and displayed to user

---

### Pictorial Representation (Textual Diagram)

```
User
 │
 │ Browser
 ▼
Frontend (Flask UI)
 │
 │ REST API Call
 ▼
Backend API (Node.js)
 │
 │ Internal Docker Network
 ▼
AI Test Generator (Python)
 │
 │ Save / Fetch Data
 ▼
PostgreSQL Database
```

---

## III. Implementation of Components & Interaction 

### Implemented Components

- **Component 1**: Flask Frontend
- **Component 2**: AI Test Generator (Python)
- **Component 3**: Backend API (Node.js)

---

### Interaction Demonstration

- Flask frontend accepts file upload
- Backend API processes request
- AI container analyzes code and generates test cases
- Generated test cases are returned to frontend
- CI/CD pipeline can execute generated tests automatically

---

### Docker-Based Implementation

- Separate Dockerfiles for:
  - Frontend
  - Backend
  - AI Worker (single AI container)

- `docker-compose.yml` manages:
  - Service startup order
  - Networking
  - Environment variables
  - Persistent database storage

---

### Outcome

- Successful communication between frontend, backend, and AI container
- AI-generated test cases displayed on UI
- System is modular, scalable, and CI/CD ready

---

## Conclusion

The project uses Docker-based deployment with clear separation of concerns.
The AI functionality is encapsulated within a single container, ensuring simplicity, portability, and scalability while enabling smooth interaction between application components.

---
