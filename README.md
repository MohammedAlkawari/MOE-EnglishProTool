# English Proficiency Tool - IELTS Exam Training Website

This repository contains the codebase for **LINGUI**, a web application developed for the **Bahrain Ministry of Education** to help students improve their English proficiency and prepare for the **IELTS (International English Language Testing System)** exam.

---

## 🚀 Key Features

- **IELTS Exam Simulation**  
  Users can take simulated IELTS exams to assess and enhance their English proficiency.

- **Personalized Feedback**  
  Leveraging Generative AI, users receive detailed performance feedback, highlighting strengths and areas for improvement.

- **Motivational Gamification**  
  Daily streaks encourage consistent practice. Users can compete on leaderboards by maintaining streaks through daily learning activities.

- **Streak Milestone Rewards**  
  Email notifications are sent when users reach significant streak milestones, boosting motivation.

- **Admin Dashboard**  
  A dedicated interface for admins to manage the platform and its content effectively.

- **Data Visualization**  
  Visual dashboards provide insights into user performance across Bahrain and per school, along with system performance metrics.

- **Exam Upload & Processing**  
  Admins can upload new IELTS content which is then processed using AI.

- **AI-Powered Content Formatting**  
  Uploaded content is processed via Amazon Textract and Generative AI, converting it into an editable format for review and approval.

---

## 🛠 Technologies Used

- **Frontend**: React  
- **Backend**: Node.js, Python  
- **Database**: DynamoDB  
- **AI/ML**: Amazon Bedrock (Titan model), Amazon Textract  
- **Email Service**: Amazon Simple Notification Service (SNS)  
- **CI/CD**: Amazon CodeCatalyst

---

## 🔄 CI/CD Setup

The system uses **Amazon CodeCatalyst** for automated builds and deployments, reducing manual errors and streamlining development.

### Repository Setup

1. Access the iGA private GitHub repository for the English proficiency tool.
2. Fork the repository to your GitHub account.
3. Locate the `.env` file in the root directory and modify it with your AWS configuration (e.g., `AWS_ACCOUNT_ID`).
4. Save the changes. The repository is now ready for deployment.

---

### CI/CD Pipeline Setup (Amazon CodeCatalyst)

#### 1. Create the Project
- Create a new project in Amazon CodeCatalyst.

#### 2. Link Repository
- Link your GitHub repository to the CodeCatalyst project as a source repository.

#### 3. IAM Setup
- **Policy**: Create a policy using the JSON file located in the `/doc` folder of this repository.  
  **Policy Name**: `GovCICDDeployPolicy`
- **Role**: Create an IAM role in your AWS account and attach the `GovCICDDeployPolicy` to it.

#### 4. Create an Environment
- Set up deployment environments in CodeCatalyst:
  - Environment Name (e.g., `Production`, `Staging`)
  - Environment Type (Prod or Non-Prod)
  - Assign the default IAM role created above

#### 5. Configure Workflow
Create or modify the YAML workflow in CodeCatalyst with the following:

- **Compute Type**: e.g., EC2  
- **Trigger Configuration**: Automatically deploy on repository changes  
- **Action Configurations**:
  - Deployment scripts
  - Containers (if used)
  - IAM role
  - AWS account ID
  - Deployment stage (Dev, Prod)

> This setup allows for seamless, secure, and consistent deployment of infrastructure and application code.

---

## ⚙️ Deployment Configurations

- The system uses **Infrastructure as Code (IaC)** with a minimal config approach.
- All configurations are centralized in the `.env` file for ease of management.
- Before deploying, check the **availability of the Gen-AI model** in your AWS region.

### Important:
If the model is unavailable in your region:
- Modify the model ID at  
  `REPO-ROOT/packages/functions/src/utilities.ts` (line 58)  
  to match a supported region’s model ID.

---

## 📁 Repository Structure

```plaintext
├── .env                          # Environment configuration
├── /packages/functions/         # Lambda functions and backend logic
├── /frontend/                   # React frontend application
├── /doc/                        # Documentation including IAM policy JSON
└── workflow.yaml                # CI/CD pipeline definition
