## ***AWS User Group Documentation***

This document describes the purpose, scope, and permissions of each AWS IAM user group used in the project. It follows the same structural style as the existing `api.md` documentation and is intended to clearly define responsibilities and access boundaries for team members.

---

## **What a User Group is**

A user group is a collection of IAM users that share the same set of permissions through attached policies.

A user group is defined as:  
{`group_name`, `attached_policies`, `intended_role`}

- `group_name` identifies the functional role of the user group.  
- `attached_policies` are AWS managed or custom inline policies that define what resources users can access.  
- `intended_role` explains what responsibilities members of the group have in the system architecture.

This structure allows permissions to be managed consistently and securely across the project.

---

## **How Access is Organized**

Access is divided into three major functional categories:

1. **API and UI Management**  
2. **Data Product and Infrastructure**  
3. **Data Transformation and Processing**

Each category maps to a specific IAM group with policies aligned to that role’s operational needs.

---

## **What Users in Each Group Should Do**

- Users authenticate through AWS IAM and inherit permissions from their assigned group.  
- Each group is scoped to a specific layer of the system (API/UI, data storage & search, or transformation pipelines).  
- Users should only perform actions relevant to their group’s responsibility (principle of least privilege).  
- Cross-service access (for example, Lambda → S3 or API Gateway → Lambda) is controlled through attached policies.

---

## **User Groups and Permissions**

---

## **334s25_API_UI**

### **Purpose**
This group manages the application front end and API layer, including deployment, routing, authentication, and monitoring. Members are responsible for maintaining the user-facing interface and API endpoints.

### **Primary Responsibilities**
- Deploy and manage API Gateway endpoints  
- Manage Amplify-hosted UI  
- Configure DNS and certificates  
- Manage Lambda functions used by the API  
- Configure authentication with Cognito  
- Monitor usage with CloudTrail  

### **Attached Policies**

| Policy Name | Type | Description |
|-------------|------|-------------|
| AdministratorAccess-Amplify | AWS Managed | Full access to Amplify for UI deployment |
| AmazonAPIGatewayAdministrator | AWS Managed | Manage API Gateway endpoints |
| AmazonRoute53FullAccess | AWS Managed | DNS configuration |
| AWSCertificateManagerFullAccess | AWS Managed | SSL/TLS certificate management |
| AWSCloudFormationFullAccess | AWS Managed | Infrastructure as code management |
| AWSLambda_FullAccess | AWS Managed | Full Lambda function control |
| cloudtrail_full | Customer Inline | Logging and audit trail access |
| full_cognito | Customer Inline | Authentication and user pool management |
| API_UI_FullAccessCS334S25 | Customer Inline | Project-specific API/UI permissions |

### **Intended Users**
Frontend developers, API developers, and system administrators responsible for deployment and authentication.

---

## **334s25_Data_Product**

### **Purpose**
This group manages the data storage, indexing, search, and backend infrastructure that supports the application. Members work primarily with databases, storage systems, and networking.

### **Primary Responsibilities**
- Manage RDS and Aurora databases  
- Manage S3 buckets and object storage  
- Configure OpenSearch clusters  
- Manage VPC and EC2 resources  
- Handle secrets and credentials  
- Control event-driven services (EventBridge, Lambda triggers)  

### **Attached Policies**

| Policy Name | Type | Description |
|-------------|------|-------------|
| AmazonAuroraDSQLConsoleFullAccess | AWS Managed | Aurora console access |
| AmazonAuroraDSQLFullAccess | AWS Managed | Full Aurora database access |
| AmazonOpenSearchServiceFullAccess | AWS Managed | OpenSearch cluster management |
| AmazonRDSDataFullAccess | AWS Managed | RDS data access |
| AmazonRDSFullAccess | AWS Managed | RDS infrastructure management |
| AmazonS3FullAccess | AWS Managed | Full S3 bucket access |
| AmazonS3ObjectLambdaExecutionRolePolicy | AWS Managed | S3 Object Lambda execution |
| AmazonVPCFullAccess | AWS Managed | Network configuration |
| CloudWatchOpenSearchDashboardsFullAccess | AWS Managed | Monitoring and dashboards |
| SecretsManagerReadWrite | AWS Managed | Secrets and credentials storage |
| api_full | Customer Inline | Full API backend integration access |
| AuroraRDSFullAccessCS334S25 | Customer Inline | Project-specific RDS permissions |
| EC2_access_policy | Customer Inline | EC2 compute access |
| EventBridge_access_policy | Customer Inline | EventBridge integration |
| Lambda_access_policy | Customer Inline | Lambda service control |
| OpenSearchServerlessFullAccessCS334S25 | Customer Inline | Serverless OpenSearch access |
| ROUTE_53_access_policy | Customer Inline | DNS routing for backend |

### **Intended Users**
Backend engineers, database administrators, and infrastructure engineers.

---

## **334s25_Data_Transformation**

### **Purpose**
This group supports data preprocessing, ETL (Extract, Transform, Load) pipelines, and transformation workflows. Members handle raw data ingestion and preparation before it is used by the API or analytics systems.

### **Primary Responsibilities**
- Read and write transformed data to S3  
- Execute transformation pipelines  
- Support batch processing jobs  
- Maintain transformation scripts and workflows  

### **Attached Policies**

| Policy Name | Type | Description |
|-------------|------|-------------|
| Transformation_S3_policy_access | Customer Inline | Access to S3 buckets for transformation pipelines |

### **Intended Users**
Data engineers and analysts responsible for cleaning, transforming, and preparing datasets.

---

## **Check Permission Overlaps Between Groups**

- **API/UI vs Data Product**:  
  Overlap occurs mainly in Lambda and Route53 policies where API services interact with backend resources.

- **Data Product vs Data Transformation**:  
  Both groups interact with S3, but Data Product manages infrastructure while Data Transformation focuses on pipeline usage.

- **API/UI vs Data Transformation**:  
  Minimal overlap; responsibilities are logically separated.

---

## **Additional Notes**

- All groups follow the principle of least privilege, with project-specific inline policies supplementing AWS managed policies.  
- Sensitive credentials are stored in AWS Secrets Manager and accessed only by authorized groups.  
- Logging and monitoring are centralized through CloudTrail and CloudWatch.  
- Group membership should reflect functional role, not individual preference.

---

## **Summary**

- **334s25_API_UI** → UI, API, authentication, deployment  
- **334s25_Data_Product** → Databases, storage, search, infrastructure  
- **334s25_Data_Transformation** → ETL and data processing pipelines  

This structure ensures separation of concerns, security, and maintainability across the AWS environment.
