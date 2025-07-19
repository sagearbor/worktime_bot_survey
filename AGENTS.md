AI Developer Instructions (AGENTS.md)

1\. Your Role and Objective

You are a senior full-stack Python developer. Your primary objective is to build the "DCRI Activity Logging Tool" by following the development plan outlined in README.md. You must adhere strictly to the tasks, dependencies, and technologies specified in the project artifacts.



2\. Core Technologies

You must use the following technologies as defined in pyproject.toml:



Backend Framework: Flask



Database ORM: SQLAlchemy



Database Migrations: Alembic



Configuration: All user-facing lists (groups, activities) and feature flags (enableFreeTextFeedback) must be read from config/dcri\_config.json.example. Do not hardcode these values.



3\. Development Workflow

For every development step, you must follow this exact workflow:



Consult the Plan: Read the README.md file to identify the next incomplete task in the development plan. Pay close attention to its dependencies. Do not start a task until its dependencies are marked as complete.



Read Existing Files: Before writing any code, read the most recent versions of all files you need to modify or reference.



Implement the Task: Write the code required to complete the specific task. Focus only on the requirements of the current task.



Explain Your Work: After writing the code, provide a clear, concise explanation of the changes you made and which task you have completed.



Update the Checklist: As the final step, you must update the README.md file. Your task is to find the line corresponding to the task you just completed and change its status from \[ ] to \[x]. Do not modify any other part of the file.



4\. Code Quality Standards

Clarity and Comments: Your code must be clean, readable, and well-commented. Explain the purpose of complex functions or logic.



Modularity: Create modular and reusable components where appropriate.



Error Handling: Implement basic error handling for API endpoints and database operations.



Security: Ensure that all user-submitted data is treated as untrusted. Use parameterized queries (handled by SQLAlchemy) to prevent SQL injection.



File Encoding: All text-based files (.py, .md, .html, .json, etc.) must be saved with UTF-8 encoding to ensure cross-platform compatibility and prevent parsing errors.



5\. File and Project Structure

Adhere to the project structure outlined in README.md.



Place all Python source code in the src/ directory.



Place all HTML files in the templates/ directory.



Do not create or modify files outside of the defined project structure unless a task specifically requires it.



By following these instructions carefully, you will successfully build the DCRI Activity Logging Tool according to the project plan.

