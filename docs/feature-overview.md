# FAICt – Feature Overview

## Project Overview
FAICt is a web-based fact-checking application designed to help users evaluate the credibility of information. The application combines evidence retrieval, AI-powered analysis, and a user-friendly interface to provide credibility verdicts, confidence scores, explanations, and supporting sources.

## Core Features

### 1. Claim Submission
Users can submit statements or claims directly through the web interface for fact-checking.

### 2. AI-Powered Analysis
The application processes submitted claims alongside supporting evidence to generate credibility assessments. The current implementation uses placeholder analysis, with OpenAI API integration planned.

### 3. Evidence Retrieval
FAICt is designed to retrieve relevant fact-checking sources through an external API. Google Fact Check API integration is a planned development task.

### 4. Credibility Verdict and Confidence Score
The results page displays a credibility verdict and a confidence score to help users interpret the analysis.

### 5. Supporting Evidence and Explanations
Users can review explanations and supporting source information to better understand how a verdict was reached.

### 6. Submission History
Submitted claims and analysis results are stored in a local SQLite database using Flask-SQLAlchemy, allowing previous submissions to be retrieved.

### 7. User Interface
The frontend uses HTML, Jinja templates, Tailwind CSS, and limited JavaScript. The interface is being developed to match the team's design mockups.

### 8. Backend Integration
Flask connects the claim submission process, evidence retrieval service, AI analysis service, database, and results interface.

### 9. Environment Configuration
The project supports environment-based configuration using `.env` and `.env.example` files.

### 10. Automated Testing
PyTest is used to validate application functionality. The skeleton includes an example test, with additional component tests planned.

## Future Development Priorities
- Integrate the Google Fact Check API.
- Implement real AI-powered claim analysis.
- Continue refining the frontend interface.
- Expand automated testing.
- Verify that all components work together correctly.
- Develop additional prototype features identified in the team's earlier project presentation.

## Documentation Update
Updated the FAICt feature descriptions to reflect the current application architecture, implemented skeleton functionality, and planned development priorities.