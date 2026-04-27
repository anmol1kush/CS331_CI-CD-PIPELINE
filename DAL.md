# CS 331 – Software Engineering Lab

## Assignment 8 

---

#  Part A: Data Access Layer (DAL) 

##  Introduction

The **Data Access Layer (DAL)** acts as an intermediate layer between the application logic and the database. It is responsible for:

* Performing database operations (CRUD)
* Abstracting database queries
* Ensing secure and efficient data access

In this project, DAL is implemented using **MongoDB (NoSQL database)** to manage Employee data.

---

##  Database Creation (MongoDB)

MongoDB is a **NoSQL database**, so instead of tables we use **collections** and **documents**.

###  Employee Collection Structure

```json id="q92qmq"
{
  "_id": "ObjectId",
  "name": "String",
  "email": "String",
  "phone": "String",
  "role": "ADMIN | DEVELOPER | PROGRAMMER",
  "salary": "Number",
  "hire_date": "Date",
  "status": "ACTIVE"
}
```

---

##  Data Access Layer Implementation

###  Database Connection (Node.js + Mongoose)

```js id="z7e0oz"
const mongoose = require("mongoose");

mongoose.connect("mongodb://127.0.0.1:27017/company_db", {
    useNewUrlParser: true,
    useUnifiedTopology: true,
});

mongoose.connection.on("connected", () => {
    console.log("MongoDB Connected");
});

module.exports = mongoose;
```

---

##  Employee Schema

```js id="d8f5rs"
const mongoose = require("mongoose");

const employeeSchema = new mongoose.Schema({
    name: { type: String, required: true },
    email: { type: String, unique: true },
    phone: String,
    role: {
        type: String,
        enum: ["ADMIN", "DEVELOPER", "PROGRAMMER"],
        required: true
    },
    salary: Number,
    hire_date: Date,
    status: { type: String, default: "ACTIVE" }
});

module.exports = mongoose.model("Employee", employeeSchema);
```

---

##  CRUD Operations

### 1. Insert Employee

```js id="ikscvt"
const Employee = require("./Employee");

async function addEmployee(emp) {
    const newEmp = new Employee(emp);
    await newEmp.save();
    console.log("Employee Added");
}
```

---

### 2. Get All Employees

```js id="pazwfa"
async function getEmployees() {
    const employees = await Employee.find();
    return employees;
}
```

---

### 3. Update Employee

```js id="k0gsgg"
async function updateEmployee(id, salary) {
    await Employee.findByIdAndUpdate(id, { salary: salary });
    console.log("Employee Updated");
}
```

---

### 4. Delete Employee

```js id="8p7r6l"
async function deleteEmployee(id) {
    await Employee.findByIdAndDelete(id);
    console.log("Employee Deleted");
}
```

---

##  Interaction with Application

* Application sends request → DAL
* DAL interacts with MongoDB
* Data is stored/retrieved as JSON documents
* Response sent back to application

---

#  Part B: Testing 

---

#  1. White Box Testing 

##  Definition

White Box Testing verifies the **internal logic and code structure** of the application.

---

##  White Box Test Cases

| Test Case ID | Description                      | Expected Output       |
| ------------ | -------------------------------- | --------------------- |
| WB1          | Insert employee function         | Document saved in DB  |
| WB2          | Fetch employees function         | Correct data returned |
| WB3          | Update employee salary           | Salary updated        |
| WB4          | Delete employee                  | Document deleted      |
| WB5          | Error handling (duplicate email) | Error thrown          |

---

##  Execution Example

```js id="m72qna"
addEmployee({
    name: "John",
    email: "john@example.com",
    role: "DEVELOPER",
    salary: 50000
});
```

###  Result:

* Functions executed correctly
* Logic verified
* Errors handled

---

#  2. Black Box Testing

##  Definition

Black Box Testing verifies system functionality **without knowing internal code**.

---

##  Black Box Test Cases

| Test Case ID | Input               | Expected Output  |
| ------------ | ------------------- | ---------------- |
| BB1          | Add valid employee  | Employee added   |
| BB2          | Add duplicate email | Error message    |
| BB3          | Update salary       | Salary updated   |
| BB4          | Delete employee     | Employee removed |
| BB5          | Fetch employees     | List displayed   |

---

##  Execution

* User provides input via UI/API
* System processes request
* Output displayed

---

##  Result

* System works correctly for all inputs
* Errors handled properly
* Data stored and retrieved successfully

---

# Conclusion

* MongoDB provides flexible schema using JSON documents
* DAL simplifies database interaction
* White Box Testing ensures correct internal logic
* Black Box Testing ensures proper system behavior

This improves:

* Scalability
* Maintainability
* Performance

---
