# Getting Started with Application Auto Scaling Custom Resources

This *aws-auto-scaling-custom-resource* repository contains templates and instructions to build, test, and remove automatic scaling for custom resources by using AWS serverless functions. In this context, a *custom resource* is an object that allows you to use the automatic scaling features of Application Auto Scaling with your own application or service.

The included AWS CloudFormation template launches a collection of AWS resources, including a new Amazon API Gateway REST API. The API Gateway REST API allows secure access to scalable resources in your application or service.

When everything is deployed and configured, you'll have the following environment in your AWS account.

![Image of Application Auto Scaling Custom Resource Environment](https://github.com/aws/aws-auto-scaling-custom-resource/blob/master/DESIGN.PNG)

You can use the *aws-auto-scaling-custom-resource* repository and the following procedures as the starting point for your customizations. More information about this approach to custom resource auto scaling is detailed in this [Auto Scaling Production Services on Titus](https://medium.com/netflix-techblog/auto-scaling-production-services-on-titus-1f3cd49f5cd7).

If you encounter an issue with the CloudFormation template, or if you are unsure how to solve a problem, we want to hear about it. Please create a GitHub issue. We welcome all feedback, pull requests, and other contributions.

# Audience

* Recommended for a technical audience looking to use Application Auto Scaling to configure automatic scaling for in-house applications and services.
* Assumes experience with AWS, including configuring automatic scaling with target tracking scaling policies and custom metrics.
* Assumes knowledge of Amazon API Gateway, CloudWatch, Lambda, and Open API Specification (aka Swagger 2.0 specs).

# AWS Services Used

The AWS components used to create this serverless architecture include the following AWS services.

* [Amazon API Gateway](https://aws.amazon.com/api-gateway/) 
* [Application Auto Scaling](https://docs.aws.amazon.com/autoscaling/application/userguide/what-is-application-auto-scaling.html) 
* [AWS CloudFormation](https://aws.amazon.com/cloudformation/)
* [AWS CloudTrail](https://aws.amazon.com/cloudtrail/) 
* [Amazon CloudWatch](https://aws.amazon.com/cloudwatch/details/) 
* [AWS Lambda](https://aws.amazon.com/lambda/) 
* [Amazon Simple Notification Service (SNS)](https://aws.amazon.com/sns/)

# Regional Availability

Custom resource auto scaling is available in Canada (Central), US West (N. California), US East (N. Virginia), US East (Ohio), US West (Oregon), South America (Sao Paulo), EU (Frankfurt), EU (Ireland), EU (London), EU (Paris), Asia Pacific (Mumbai), Asia Pacific (Seoul), Asia Pacific (Singapore), Asia Pacific (Sydney), Asia Pacific (Tokyo), and China (Beijing).

# First Steps

* AWS Command Line Interface [installed](https://docs.aws.amazon.com/cli/latest/userguide/installing.html) and [configured](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html).  
* [Postman](https://www.getpostman.com/) installed.  This tool allows you to test your API endpoints and observe the responses. Postman is a convenient testing tool because it provides fields for adding your [Signature Version 4](https://docs.aws.amazon.com/general/latest/gr/signature-version-4.html) signing information to an HTTPS request.
* Make sure you have permissions to create a stack using a CloudFormation template, plus full access permissions to resources within the stack.

# Set Up the AWS Serverless Functions

This section describes how to set up and test the required serverless functions in your AWS account. 

## Step 1: Build and Test Your REST Endpoint URL 

The provided CloudFormation template defines the serverless functions that will be created. Before you launch the stack, you must verify that your backend system conforms to the REST API specification that's supported by the template.

1. Configure the GET and PATCH request methods to connect with the Amazon API Gateway. For more information on these methods, see the `CustomResourceEndpoint` section of the [custom-resource-stack.yaml](https://github.com/aws/aws-auto-scaling-custom-resource/blob/master/cloudformation/templates/custom-resource-stack.yaml) template.
1. Verify that your backend system's REST endpoint URL works by using the following command to issue GET and PATCH requests to it.

```
$ curl -i -X GET --header 'Accept: application/json' 'http://api.example.com/v1/scalableTargetDimensions/myservice'
```

If the endpoint is set up properly, it should return a standard `200 OK` response message and a payload that represents the requested resource and its status.

The following is an example GET and PATCH response.

```json
{
  "actualCapacity": 2.0,
  "desiredCapacity": 2.0,
  "dimensionName": "MyDimension",
  "resourceName": "MyService",
  "scalableTargetDimensionId": "1-23456789",
  "scalingStatus": "Successful",
  "version": "MyVersion"
}
```

Note: If you need a test environment and are familiar with Docker, a sample REST endpoint is provided as a Dockerized Apache Python CGI. For more information, see [sample-api-server](./sample-api-server/).

## Step 2: Launch the CloudFormation Stack

NOTE: You may incur AWS charges as part of this deployment. Please monitor your Free Tier usage and make sure that you understand the AWS charges involved.

1. Download the [custom-resource-stack.yaml](https://github.com/aws/aws-auto-scaling-custom-resource/blob/master/cloudformation/templates/custom-resource-stack.yaml) CloudFormation template from GitHub.
1. Run the following [create-stack](https://docs.aws.amazon.com/cli/latest/reference/cloudformation/create-stack.html) command, adding your details as follows:
- For `SNSSubscriptionEmail`, replace `email-address` with the email address where you want certificate expiry notifications to be sent.
- For `IntegrationHttpEndpoint`, replace `endpoint-url` with your REST endpoint URL. For example, http://api.example.com/v1/scalableTargetDimensions/*{scalableTargetDimensionId}* where *{scalableTargetDimensionId}*  is replaced with the dimension in your backend API. The resulting URL would look something like: http://api.example.com/v1/scalableTargetDimensions/*1-23456789*.
- (Optional) Change the [AWS Region](https://docs.aws.amazon.com/general/latest/gr/rande.html) by updating the `--region` value. The examples in this repository use `us-west-2`, but the steps are the same if you deploy into a different region. 

The following example shows a sample create-stack command.

```
$ aws cloudformation create-stack \
    --stack-name CustomResourceAPIGatewayStack \
    --template-body file://~/custom-resource-stack.yaml \
    --region us-west-2 \
    --capabilities CAPABILITY_NAMED_IAM CAPABILITY_IAM \
    --parameters \         
        ParameterKey=SNSSubscriptionEmail,ParameterValue="email-address" \
        ParameterKey=IntegrationHttpEndpoint,ParameterValue='"endpoint-url"'
```
The stack takes only a few minutes to deploy. It creates a new REST API in API Gateway with two stages: “PreProd” and “Prod”. Each stage is deployed with its own client-side certificate. With the serverless framework, you can deploy to different environments using stages. As your API evolves, these stages can be helpful for testing and development.

When the deployment has completed successfully, you receive an email to confirm a subscription to the Amazon SNS topic created by the template. Choose the **Confirm subscription** link in the message to subscribe to emails that are sent whenever there is an expiring certificate. A Lambda function checks once a day to see if the client certificate is expiring in 7, 3, or 1 days.

The following is the full list of created resources:

- AWS::ApiGateway::RestApi
- AWS::ApiGateway::Stage 
- AWS::ApiGateway::ClientCertificate
- AWS::ApiGateway::Deployment
- AWS::ApiGateway::Account
- AWS::Lambda::Function
- AWS::SNS::Topic
- AWS::IAM::Role (A service role to grant Lambda permission to call API Gateway and SNS)
- AWS::IAM::Role (A CloudWatch role required for certificate expiry checks)
- AWS::Events::Rule (A CloudWatch rule required for certificate expiry checks)
- AWS::Lambda::Permission (The permissions for CloudWatch to invoke the Lambda function)
- AWS::CloudTrail::Trail
- AWS::S3::Bucket (An S3 bucket to receive the log files for CloudTrail)
- AWS::S3::BucketPolicy (The S3 bucket policy that grants access only to the created CloudTrail)

## Step 3: Gather the Stack's Output

To continue with these steps, you need the HTTPS prefixes of your new REST API in API Gateway and, optionally, the IDs of the client certificates from the stack. To do this, run the following [describe-stacks](https://docs.aws.amazon.com/cli/latest/reference/cloudformation/describe-stacks.html) command and copy the output. 

```
$ aws cloudformation describe-stacks --region us-west-2 --stack-name CustomResourceAPIGatewayStack  | jq '.Stacks[0]["Outputs"]'
```

This returns a response similar to the following example.

```json
[
  {
    "Description": "Application Auto Scaling Resource ID prefix for Preprod",
    "OutputValue": "https://example.execute-api.us-west-2.amazonaws.com/preprod/scalableTargetDimensions/",
    "OutputKey": "PreProdResourceIdPrefix"
  },
  {
    "OutputValue": "customresourceapigatewaystack-s3bucket-ha8id2l1wpo6",
    "OutputKey": "S3BucketName"
  },
  {
    "Description": "Application Auto Scaling Resource ID prefix for Prod",
    "OutputValue": "https://example.execute-api.us-west-2.amazonaws.com/prod/scalableTargetDimensions/",
    "OutputKey": "ProdResourceIdPrefix"
  },
{
   "Description": "API Gateway Client Cert",
    "OutputKey": "PreProdClientCertificate",
    "OutputValue": "MIIDoTCCAwqgAwIBAgIMCRkox...tt3rdw"
  },
  {
    "Description": "API Gateway Client Cert",
    "OutputKey": "ProdClientCertificate",
    "OutputValue": "MIIDVDCCAr0CAQAweTEeMBwG...frw3tnx"
  }
]
```

## Step 4: (Optional) Configure Backend Authentication

By default, client-side SSL certificates are used to authenticate the API Gateway API when it connects to your backend system. You can also use the certificates' public keys in the backend to verify that HTTP requests to your backend system are from API Gateway.

To extract the PEM-encoded public key of the SSL certificate, run the following AWS CLI commands, replacing the `client-certificate-id` with the values for `ProdClientCertificate` and `PreProdClientCertificate` from the stack output. 

```
aws apigateway get-client-certificate \
--client-certificate-id MIIDVDCCAr0CAQAweTEeMBwG...frw3tnx \
--output text
aws apigateway get-client-certificate \
--client-certificate-id MIIDoTCCAwqgAwIBAgIMCRkox...tt3rdw \
--output text
```

The output can be used to configure your backend system to verify the client SSL certificate. For more information, see [Generate and Configure an SSL Certificate for Backend Authentication](https://docs.aws.amazon.com/apigateway/latest/developerguide/getting-started-client-side-ssl-authentication.html) in the *Amazon API Gateway Developer Guide*.

## Step 5: Test the Endpoint Integration

The next step is to verify that the API Gateway API is integrated with your backend system.

1. Create the string that identifies the path to the custom resource through the API Gateway (the Resource ID). The Resource ID has the following syntax: `[OutputValue][identifier]`. 
   - The `OutputValue` is one of the HTTPS prefixes ("Prod" or "Preprod") from the `describe-stacks` output.   
   - The identifier is a string that identifies a scalable resource in your backend system (the value for *scalableTargetDimensionId* from step 1). 
Example showing “1-23456789” as the identifier in your backend system:
`https://example.execute-api.us-west-2.amazonaws.com/prod/scalableTargetDimensions/1-23456789`
1. Follow the instructions in [Use Postman to Call an API](https://docs.aws.amazon.com/apigateway/latest/developerguide/how-to-use-postman-to-call-api.html) to send a test request in Postman. If you prefer to view the headers and body, you can convert the response to CURL by using the Postman code snippet generator. 

The following example shows the Postman CURL response to a GET request.

``` 
curl -X GET \ https://example.execute-api.us-west-2.amazonaws.com/prod/scalableTargetDimensions/1-23456789 \
  -H 'Authorization: AWS4-HMAC-SHA256 Credential=example/20180704/us-west-2/execute-api/aws4_request, SignedHeaders=content-type;host;x-amz-date;x-amz-security-token, Signature=SIGNATURE' \
  -H 'Cache-Control: no-cache' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -H 'Host: example.execute-api.us-west-2.amazonaws.com' \
  -H 'Postman-Token: POSTMANTOKEN' \
  -H 'X-Amz-Date: 20180704T023500Z' \
  -H 'X-Amz-Security-Token: SESSIONTOKEN'
{
  "actualCapacity": 2.0,
  "desiredCapacity": 2.0,
  "dimensionName": "MyDimension",
  "resourceName": "MyService",
  "scalableTargetDimensionId": "1-23456789",
  "scalingStatus": "Successful",
  "version": "MyVersion"
}
```

# Configure Automatic Scaling

This section describes how to define the scaling policy that Application Auto Scaling uses to scale your application resources.

## Prerequisites

Before you begin, verify that you have completed all of the steps in the procedure above. Also verify that you have the permissions that allow you to configure automatic scaling and create the required service-linked role. For details on the required permissions, see the [Authentication and Access Control](https://docs.aws.amazon.com/autoscaling/application/userguide/auth-and-access-control.html) topic in the *Application Auto Scaling User Guide*. Be sure to use the correct permissions when registering a scalable target, so that the service-linked role is automatically created. Otherwise, the scaling function will not work. 

You must also have permissions to [publish metrics (PutMetricData)](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/permissions-reference-cw.html) to CloudWatch.

## Step 1: Register Your Scalable Target

Register your resource as a scalable target with Application Auto Scaling. A scalable target is a resource that Application Auto Scaling can scale out or scale in.

To get started, run the following command to save your Resource ID in a txt file (with no newline character at the end of the file).

The command will look like the following example, but with your Resource ID.

```
$ echo -n "https://example.execute-api.us-west-2.amazonaws.com/prod/scalableTargetDimensions/1-23456789" > ~/custom-resource-id.txt
```

Running the command saves the file as `custom-resource-id.txt` in your home directory. You can now use the [register-scalable-target](https://docs.aws.amazon.com/cli/latest/reference/application-autoscaling/register-scalable-target.html) command to register your scalable target, as shown in the following example.

```
$ aws application-autoscaling register-scalable-target \
--service-namespace custom-resource \
--scalable-dimension custom-resource:ResourceType:Property \
--resource-id file://~/custom-resource-id.txt \
--min-capacity 0 --max-capacity 10
```

This registers your scalable target with Application Auto Scaling, and allows it to manage capacity within the range of 0 to 10 capacity units. 

## Step 2: Create a Target Tracking Scaling Policy

Create a scaling policy for your custom resource that specifies how the scalable target should be scaled when CloudWatch alarms are triggered. 

For target tracking, you can define a scaling policy that meets your resource's specific requirements by creating a custom metric. You can define your custom metric based on any metric that changes in proportion to scaling. 

However, not all metrics work for target tracking. The metric must be a valid utilization metric, and it must describe how busy your custom resource is. The value of the metric must increase or decrease in inverse proportion to the number of capacity units. That is, the value of the metric should decrease when capacity increases and increase when capacity decreases. 

The following `cat` command creates a sample metric for your scalable target in a `config.json` file in your home directory:

```
$ cat ~/config.json
{
   "TargetValue":50,
   "CustomizedMetricSpecification":{
      "MetricName":"MyAverageUtilizationMetric",
      "Namespace":"MyNamespace",
      "Dimensions":[
         {
            "Name":"MyMetricDimensionName",
            "Value":"MyMetricDimensionValue"
         }
      ],
      "Statistic":"Average",
      "Unit":"Percent"
   }
}
```

Use the following [put-scaling-policy](https://docs.aws.amazon.com/cli/latest/reference/application-autoscaling/put-scaling-policy.html) command, along with the `config.json` file that you created previously, to create a scaling policy named `custom-tt-scaling-policy` that keeps the average utilization of your custom resource at 50 percent:

```
$ aws application-autoscaling put-scaling-policy \
--policy-name custom-tt-scaling-policy \
--policy-type TargetTrackingScaling \
--service-namespace custom-resource \
--scalable-dimension custom-resource:ResourceType:Property \
--resource-id file://~/custom-resource-id.txt \
--target-tracking-scaling-policy-configuration file://~/config.json
{
   "Alarms": [
        {
            "AlarmName": "TargetTracking-https://example.execute-api.us-west-2.amazonaws.com/prod/scalableTargetDimensions/1-23456789-AlarmHigh-b9d32d65-78bb-4d01-8931-d67d10f87052",
            "AlarmARN": "arn:aws:cloudwatch:us-west-2:544955126770:alarm:TargetTracking-https://example.execute-api.us-west-2.amazonaws.com/prod/scalableTargetDimensions/1-23456789-AlarmHigh-b9d32d65-78bb-4d01-8931-d67d10f87052"
        },
        {
            "AlarmName": "TargetTracking-https://example.execute-api.us-west-2.amazonaws.com/prod/scalableTargetDimensions/1-23456789-AlarmLow-a9f90ec7-dccd-4a66-83ea-26bf3f0134dc",
            "AlarmARN": "arn:aws:cloudwatch:us-west-2:544955126770:alarm:TargetTracking-https://example.execute-api.us-west-2.amazonaws.com/prod/scalableTargetDimensions/1-23456789-AlarmLow-a9f90ec7-dccd-4a66-83ea-26bf3f0134dc"
        }
    ],
    "PolicyARN": "arn:aws:autoscaling:us-west-2:544955126770:scalingPolicy:ac852aff-b04f-427d-a80a-3e7ef31d492d:resource/custom-resource/https://example.execute-api.us-west-2.amazonaws.com/prod/scalableTargetDimensions/1-23456789:policyName/custom-tt-scaling-policy"
}
```

This creates two alarms: one for scaling out and one for scaling in. It also returns the Amazon Resource Name (ARN) of the policy that is registered with CloudWatch, which CloudWatch uses to invoke scaling whenever the metric is in breach. 

For more information about creating target tracking scaling policies, see [Target Tracking Scaling Policies](https://docs.aws.amazon.com/autoscaling/application/userguide/application-auto-scaling-target-tracking.html) in the Application Auto Scaling documentation.

For more information about creating custom metrics, see [Publish Custom Metrics](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/publishingMetrics.html) in the CloudWatch documentation. 

## Step 3: Trigger the Scaling Policy Using a Bash Script

Test your scaling policy by publishing sample metric data to CloudWatch. CloudWatch alarms trigger the scaling policy and calculate the scaling adjustment based on the metric and the target value. 

Run the following bash script at the command line:

```bash
// Command to put metric data that breaches AlarmHigh
$ while sleep 3
do
  aws cloudwatch put-metric-data \
  --metric-name MyAverageUtilizationMetric \
  --namespace MyNamespace --value 70 \
  --unit Percent \
  --dimensions MyMetricDimensionName=MyMetricDimensionValue
  echo -n "."
done
```

This script publishes data points to CloudWatch to trigger the scaling policy based on live metric data. The `while` loop is used to perform the CLI command an unknown number of times. The `sleep 3` conditions pauses the execution for 3 seconds on each iteration. After you verify that scaling works (which is the next step in this procedure), press Ctrl+C to stop the script.

It may take a few minutes before your scaling policy is invoked. When the target ratio exceeds 50 percent for a sustained period of time, Application Auto Scaling notifies your custom resource to adjust capacity upward, so that the 50 percent target utilization can be maintained.

## Step 4: View the Scaling Activities 

View the scaling activities that were created in response to the bash script in the previous step.

Run the [describe-scaling-activities](https://docs.aws.amazon.com/cli/latest/reference/application-autoscaling/describe-scaling-activities.html) command, as shown in the following example.

```
$ aws application-autoscaling describe-scaling-activities \
--service-namespace custom-resource \
--resource-id file://~/custom-resource-id.txt \
--max-results 20
```

You should eventually see output similar to the following example.
```JSON
{
    "ScalingActivities": [
        {
            "ScalableDimension": "custom-resource:ResourceType:Property",
            "Description": "Setting desired capacity to 6.",
            "ResourceId": "https://example.execute-api.us-west-2.amazonaws.com/prod/scalableTargetDimensions/1-23456789",
            "ActivityId": "2fca0873-3e4d-4c05-a83d-40c6394e6b9b",
            "StartTime": 1530744698.087,
            "ServiceNamespace": "custom-resource",
            "EndTime": 1530744730.766,
            "Cause": "monitor alarm TargetTracking-https://example.execute-api.us-west-2.amazonaws.com/prod/scalableTargetDimensions/1-23456789-AlarmHigh-b9d32d65-78bb-4d01-8931-d67d10f87052 in state ALARM triggered policy custom-tt-scaling-policy",
            "StatusMessage": "Successfully set desired capacity to 6. Change successfully fulfilled by custom-resource.",
            "StatusCode": "Successful"
        }
    ]
}
```

Note: If you are using the [sample-api-server](./sample-api-server/) that is provided in this project, you can also see the scaling activities in the API log.
## Step 5: Deregister the Scalable Target

To deregister a scalable target that you no longer need, use the same txt file that you specified to register the scalable target and run the [deregister-scalable-target](https://docs.aws.amazon.com/cli/latest/reference/application-autoscaling/deregister-scalable-target.html) command:

```
$ aws application-autoscaling deregister-scalable-target \
--service-namespace custom-resource \
--scalable-dimension custom-resource:ResourceType:Property \
--resource-id file://~/custom-resource-id.txt
```

Deregistering a scalable target deletes the scaling policy and the CloudWatch alarms that Application Auto Scaling created on your behalf. 

# Documentation

The [Application Auto Scaling User Guide](https://docs.aws.amazon.com/autoscaling/application/userguide/what-is-application-auto-scaling.html) provides in-depth guidance about the Application Auto Scaling service. 

# License Summary

This sample code is made available under a modified MIT-0 license. See the [LICENSE](https://github.com/aws/aws-auto-scaling-custom-resource/blob/master/LICENSE) file.
