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
  > **⚠️ Note**: In case the policy is not already pushed to your account, follow these steps to create it manually.

- **Role**: Create an IAM role in your AWS account.  
  **Role Name**: `GovCICDDeployRole`  
  Attach the `GovCICDDeployPolicy` policy to this role.
#### 4. Create an Environment
- Set up deployment environments in CodeCatalyst:
  - Environment Name (e.g., `Production`, `Staging`)
  - Environment Type (Prod or Non-Prod)
  - Assign the default IAM role created above `GovCICDDeployRole` 

> **⚠️ Note**: In case the workflow is not shown create or modify the YAML workflow in CodeCatalyst with the following:
>
> - **Compute Type**: e.g., EC2  
> - **Trigger Configuration**: Automatically deploy on repository changes  
> - **Action Configurations**:
>   - Deployment scripts  
>   - Containers (if used)  
>   - IAM role  
>   - AWS account ID  
>   - Deployment stage (Dev, Prod)  
>
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
├── QuestionScript                   # Scripts and data files related to handling questions
│   ├── AdditionalQuestions.json     # Additional question set in JSON format
│   ├── challengesDynamoFiller.py    # Script to populate DynamoDB with challenge-related data
│   ├── dynamodbFiller.py            # Script to populate DynamoDB with general data
│   ├── questions.json               # Main set of questions in JSON format
│   └── questionsNew.json            # Updated or alternate version of questions
├── README.md                        # Project overview and instructions
├── aws                              # AWS-related files and dependencies
│   ├── README.md                    # AWS setup or usage documentation
│   ├── THIRD_PARTY_LICENSES         # Licenses for third-party AWS tools or libraries
│   ├── dist                         # Compiled/built AWS-related files
│   └── install                      # AWS CLI or SDK installation resources
├── awscliv2.zip                     # AWS CLI v2 installer
├── db.dbml                          # Database schema in DBML format (for visual modeling)
├── docs                             # Project documentation
│   ├── 01-context.md                # Project background and context
│   ├── 02-deployment-architecture.md # System and deployment architecture details
│   ├── 03-api-defenition.md         # API definitions and endpoints
│   ├── 04-db-schema.md              # Explanation of database schema
│   ├── 05-frontend-guidelines.md    # Guidelines for frontend development
│   ├── GovCICDDeployPolicy.json     # CI/CD deployment policy for government environments
│   └── diagrams                     # Architecture and other visual diagrams
├── gen-ai-moe-challenge             # Placeholder or directory for the Gen-AI challenge
├── package-lock.json                # Auto-generated dependency lock file (npm or pnpm)
├── package.json                     # Node.js project config and dependency list
├── packages                         # Monorepo packages
│   ├── core                         # Core/shared utilities or services
│   ├── db-migrations                # Database migration scripts
│   ├── frontend                     # Frontend source code
│   └── functions                    # Backend serverless functions
├── pnpm-workspace.yaml              # pnpm monorepo workspace configuration
├── sst.config.ts                    # SST (Serverless Stack Toolkit) config for infra-as-code
├── stacks                           # Infrastructure as code using SST
│   ├── ApiStack.ts                  # Defines API Gateway and related resources
│   ├── AuthStack.ts                 # Auth-related infrastructure (e.g., Cognito)
│   ├── DBStack.ts                   # Database resources (e.g., DynamoDB)
│   ├── FrontendStack.ts             # Hosting setup for frontend (e.g., S3/CloudFront)
│   ├── GrammarToolStack.ts          # Specific infra for a grammar tool feature
│   ├── StorageStack.ts              # File storage-related infra (e.g., S3 buckets)
│   └── devops                       # DevOps-related scripts or stack definitions
├── structure.txt                    # Text representation of project structure (likely this file)
└── tsconfig.json                    # TypeScript compiler configuration

13 directories, 29 files 
```

---

## 📬 Contact

For access-related inquiries or technical support, please contact the Technical Team under the Innovation & Advanced Technology Directorate at iGA (Information & eGovernment Authority) via:
innovation.support@iga.gov.bh
