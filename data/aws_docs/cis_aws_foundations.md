# CIS AWS Foundations Benchmark Checklists

This document outlines key security compliance checks based on the Center for Internet Security (CIS) AWS Foundations Benchmark.

## Domain 1: Identity and Access Management (IAM)

### 1.16 Ensure IAM Policies Are Attached Only to Groups or Roles (Scored)
* **Risk:** Attaching policies directly to users (user-level policies) increases administrative overhead, makes it difficult to audit privileges, and increases the likelihood of accidental privilege accumulation.
* **Audit Command (CLI):**
  ```bash
  aws iam list-users --query "Users[*].UserName" --output text | xargs -I {} aws iam list-user-policies --user-name {}
  ```
* **Remediation:**
  1. Identify any policies directly attached to IAM users.
  2. Create an IAM group with the required policies or utilize an existing IAM role.
  3. Add the IAM user to the group/role.
  4. Detach the policy from the user:
     ```bash
     aws iam detach-user-policy --user-name <username> --policy-arn <policy_arn>
     ```

### 1.4 Ensure No IAM Root User Access Keys Exist (Scored)
* **Risk:** The root user account has full administrative power over all resources in the account. Access keys for root bypass MFA and cannot be limited or constrained via IAM policies.
* **Audit Command (CLI):**
  ```bash
  aws iam get-account-summary --query "SummaryMap.AccountAccessKeysPresent"
  ```
* **Remediation:**
  1. Log in to the AWS console as the root user.
  2. Go to My Security Credentials.
  3. Locate any active root access keys, deactivate them, and then delete them.

---

## Domain 2: Logging and Monitoring

### 2.1.1 Ensure CloudTrail Log File Validation is Enabled (Scored)
* **Risk:** Log file validation provides an additional layer of security by generating cryptographic hashes for CloudTrail logs. This allows you to verify that log files were not deleted, modified, or forged after CloudTrail delivered them.
* **Audit Command (CLI):**
  ```bash
  aws cloudtrail describe-trails --query "trailList[*].[Name,LogFileValidationEnabled]"
  ```
* **Remediation:**
  To enable log file validation on an existing trail:
  ```bash
  aws cloudtrail update-trail --name <trail_name> --enable-log-file-validation
  ```

### 2.1.2 Ensure CloudTrail is Enabled in All Regions (Scored)
* **Risk:** Security threats can occur in unused regions. Without multi-region CloudTrail logging, actions taken in unmonitored regions will go completely undetected.
* **Remediation:**
  Ensure the trail has `--is-multi-region-trail` set:
  ```bash
  aws cloudtrail update-trail --name <trail_name> --is-multi-region-trail
  ```
