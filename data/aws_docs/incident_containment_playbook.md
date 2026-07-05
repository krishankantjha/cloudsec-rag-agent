# Cloud Security Incident Containment Playbook

This document defines standard operating procedures for isolating and containing security incidents within an AWS environment.

## Threat 1: Compromised IAM Access Keys

### Indicators of Compromise (IoC)
* Unusual geolocation or IP address in CloudTrail API calls.
* Spikes in reconnaissance API actions (`Describe*`, `List*`).
* API errors related to authorization failures.

### Containment Protocol
1. **Identify the compromised key pair:** Extract the Access Key ID from the alert or CloudTrail event logs.
2. **Deactivate the Access Key immediately:** Run the CLI command:
   ```bash
   aws iam update-access-key --access-key-id <ACCESS_KEY_ID> --status Inactive --user-name <USER_NAME>
   ```
3. **Revoke existing sessions:** Attach an explicit Deny policy to the user or role to terminate active CLI sessions.
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Deny",
         "Action": "*",
         "Resource": "*"
       }
     ]
   }
   ```
4. **Initiate Credential Rotation:** Generate new credentials after completing the investigation.

---

## Threat 2: S3 Data Exfiltration Alert

### Indicators of Compromise (IoC)
* Large data egress volume identified in S3 server access logs.
* S3 bucket policy changes that disable "Block Public Access" or allow anonymous read.
* API calls from unknown external IP ranges downloading objects.

### Containment Protocol
1. **Enable Block Public Access at the Bucket Level:**
   ```bash
   aws s3api put-public-access-block --bucket <bucket_name> --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
   ```
2. **Apply Restrictive Bucket Policy:** Temporarily attach a bucket policy that denies all access except to verified administrative roles and VPC endpoints.
3. **Audit Active IAM Roles:** Inspect active sessions/policies of the principal that initiated the downloads.
