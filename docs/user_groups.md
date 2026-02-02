## ***AWS User Group Documentation***

This document describes the purpose, scope, and permissions of each AWS IAM user group used in the project. It is intended to clearly define responsibilities and access boundaries for team members.

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
