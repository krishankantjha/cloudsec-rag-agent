# IAM Privilege Escalation Vector Analysis

This guide describes how overly permissive IAM policies can be abused by malicious actors to escalate their privileges to administrator levels, and how to defend against these vulnerabilities.

## Vector 1: CreateNewPolicyVersion (iam:CreatePolicyVersion)

### Scenario
An attacker has compromised an IAM principal that is allowed to edit a customer-managed policy they are already attached to, or a policy attached to a role they can assume.

* **Risky Permission Set:**
  ```json
  {
    "Effect": "Allow",
    "Action": "iam:CreatePolicyVersion",
    "Resource": "arn:aws:iam::123456789012:policy/TargetEditablePolicy"
  }
  ```

### Exploitation Flow
1. The attacker creates a new version of the policy containing full administrator rights:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": "*",
         "Resource": "*"
       }
     ]
   }
   ```
2. By specifying `--set-as-default` during creation, the policy version becomes active immediately.
   ```bash
   aws iam create-policy-version --policy-arn <policy_arn> --policy-document file://admin-policy.json --set-as-default
   ```

### Remediation
* Limit access to `iam:CreatePolicyVersion` strictly to security administrators.
* Never allow wildcard (`*`) access in the policy resources for this action.
* Enforce policy change management reviews before updates are published.

---

## Vector 2: Role PassRole (iam:PassRole & iam:CreateFunction / ec2:RunInstances)

### Scenario
An attacker can pass an existing highly privileged IAM role (e.g., administrator or service role) to an AWS resource like an EC2 instance or a Lambda function, and then trigger that resource to run arbitrary code under the context of that role.

* **Risky Permission Set:**
  ```json
  {
    "Effect": "Allow",
    "Action": [
      "iam:PassRole",
      "lambda:CreateFunction",
      "lambda:CreateEventSourceMapping"
    ],
    "Resource": "*"
  }
  ```

### Exploitation Flow
1. The attacker creates a Lambda function containing malicious script (e.g., exfiltrating credentials).
2. The attacker passes a high-privilege IAM service role to the Lambda function.
3. The attacker invokes the Lambda function, executing code with the high-privilege credentials.

### Remediation
* **Apply Least Privilege to PassRole:** Restrict `iam:PassRole` resource parameters to specific target role ARNs.
* **Enforce Service Boundaries:** Apply IAM Permissions Boundaries to restrict maximum permissions the passed role can hold.
