
This aws-auto-scaling-custom-resource repository contains templates and instructions to build, test, and remove automatic scaling for custom resources using AWS services. In this context, a *custom resource* is an object that allows you to introduce your own application or service to the automatic scaling features of AWS.  

The included AWS CloudFormation template launches a collection of AWS resources, including a new Amazon API Gateway endpoint. The API Gateway endpoint allows secure access to scalable resources in the application or service that you want automatic scaling to work with. 

Once everything is deployed and configured, you'll have the following environment in your AWS account.

![Image of Application Auto Scaling Custom Resource Environment](https://github.com/aws/aws-auto-scaling-custom-resource/blob/master/DESIGN.PNG)

You can use this repository and the deployment steps below as the starting point for your customizations. More information about this approach to custom resource auto scaling is detailed in this [blog post](https://medium.com/netflix-techblog/auto-scaling-production-services-on-titus-1f3cd49f5cd7).

If you find this information useful, feel free to spread the word about custom resource auto scaling. If you are unsure how to solve a problem, please create a GitHub issue. Also, we welcome all feedback, pull requests, and other contributions.

# Audience

* Recommended for a technical audience looking to use AWS Application Auto Scaling to configure automatic scaling for in-house applications and services.
* Assumes experience with AWS, including configuring automatic scaling with target tracking scaling policies and custom metrics. 
* Assumes fair knowledge of Amazon API Gateway, CloudWatch, Lambda, and Open API Specification (aka Swagger 2.0 specs). 

# AWS Services Used

The core AWS components used by this deployment include the following AWS services.

* [Amazon API Gateway](https://aws.amazon.com/api-gateway/) 
* [Application Auto Scaling](https://docs.aws.amazon.com/autoscaling/application/APIReference/Welcome.html) 
* [AWS CloudFormation](https://aws.amazon.com/cloudformation/)
* [AWS CloudTrail](https://aws.amazon.com/cloudtrail/) 
* [Amazon CloudWatch](https://aws.amazon.com/cloudwatch/details/) 
* [AWS Lambda](https://aws.amazon.com/lambda/) 
* [Amazon Simple Notification Service (SNS)](https://aws.amazon.com/sns/)

# Regional Availability

Custom resource auto scaling is available in Canada (Central), US West (N. California), US East (N. Virginia), US East (Ohio), US West (Oregon), South America (Sao Paulo), EU (Frankfurt), EU (Ireland), EU (London), EU (Paris), Asia Pacific (Mumbai), Asia Pacific (Seoul), Asia Pacific (Singapore), Asia Pacific (Sydney), Asia Pacific (Tokyo), and China (Beijing). 

# Prerequisites

* AWS Command Line Interface [installed](https://docs.aws.amazon.com/cli/latest/userguide/installing.html) and [configured](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html). 
* User credentials with permissions that allow you to configure automatic scaling and create the required service-linked role. For more information, see the [Application Auto Scaling User Guide](https://docs.aws.amazon.com/autoscaling/application/userguide/auth-and-access-control.html).  
* Permissions to create a stack using a CloudFormation template, plus full access permissions to resources within the stack. For more information, see the [AWS CloudFormation User Guide](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/Welcome.html). 
* Permissions to [publish metrics (PutMetricData)](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/permissions-reference-cw.html) to CloudWatch.

# Deployment Steps

Follow the step-by-step instructions in this section to build and test the custom resource auto scaling environment in your AWS account. The CloudFormation template provided with this repository creates the core AWS components from scratch. 

## 1. Build and Test Your REST Endpoint URL 

Before running the CloudFormation template, you need an HTTP/HTTPS endpoint to expose your REST resources using GET and PATCH methods. Make sure that your application conforms to the REST API specification in the [custom-resource-stack.yaml](https://github.com/aws/aws-auto-scaling-custom-resource/blob/master/cloudformation/templates/custom-resource-stack.yaml) CloudFormation template.  

Note: If you need a test environment and are familiar with Docker, a sample REST endpoint is provided as a Dockerized Apache Python CGI. For more information, see [sample-api-server](./sample-api-server/).

After you create an endpoint that contains the required REST resources, you can verify that the endpoint URL works by issuing GET and PATCH requests to it, for example: 

```
$ curl -i -X GET --header 'Accept: application/json' 'http://api.example.com/v1/scalableTargetDimensions/myservice'
```

If the endpoint is set up properly, it should return a standard 200 OK response message and a payload that represents the requested resource and its status.

The response for GET and PATCH will look something like:

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

## 2. Launch the Stack

Download the [custom-resource-stack.yaml](https://github.com/aws/aws-auto-scaling-custom-resource/blob/master/cloudformation/templates/custom-resource-stack.yaml) CloudFormation template from GitHub.

Run the following [create-stack](https://docs.aws.amazon.com/cli/latest/reference/cloudformation/create-stack.html) command, adding your details to the following parameters:

1. *SNSSubscriptionEmail*: Replace *email-address* with an email address to send certificate expiry notifications to.
2. *IntegrationHttpEndpoint*: Replace *endpoint-url* with your REST endpoint URL, for example, http://api.example.com/v1/scalableTargetDimensions/{scalableTargetDimensionId} where *{scalableTargetDimensionId}* is replaced with the dimension in your backend API, which might look something like: http://api.example.com/v1/scalableTargetDimensions/1-23456789.


Make a note of the AWS [region](https://docs.aws.amazon.com/general/latest/gr/rande.html) where you created this stack. You need it later. Note: The examples in this repository use us-west-2, but the steps will be the same if you deploy into a different region. 

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
The stack takes only a few minutes to deploy. It creates a new REST API in API Gateway with two stages: “PreProd” and “Prod”. A stage defines the path through which an API deployment is accessible. Each stage is deployed with its own client-side certificate. 

When the deployment has completed successfully, you’ll receive an email to confirm a subscription to the Amazon SNS topic created by the template. Choose the *Confirm subscription* link in the message to subscribe to emails that are sent whenever there is an expiring certificate. A Lambda function checks once a day to see if the client certificate is expiring in 7, 3, or 1 days.

## 3. Get the Resource ID and API Gateway Client Certificate IDs

To continue with the deployment steps, you need the HTTPS link (aka Resource ID) for your API Gateway endpoint. 

After the stack launches, run the [describe-stacks](https://docs.aws.amazon.com/cli/latest/reference/cloudformation/describe-stacks.html) command and copy the output. 

```
$ aws cloudformation describe-stacks --region us-west-2 --stack-name CustomResourceAPIGatewayStack  | jq '.Stacks[0]["Outputs"]'
```

This returns the following response:

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

The Resource ID has the following syntax:
`[OutputValue][identifier]`

The `OutputValue` is one of the HTTPS prefixes ("Prod" or "Preprod") from the `describe-stacks` output. 

The identifier is a string that identifies a scalable resource in your backend system (the value for *scalableTargetDimensionId* in step 1). 

**Example: Resource ID where “1-23456789” is the identifier in your backend system**

`https://example.execute-api.us-west-2.amazonaws.com/prod/scalableTargetDimensions/1-23456789`

## 4. Configure SSL/HTTPS  

To configure the SSL/HTTPS connection between the API Gateway and your backend system, you need the output values for `ProdClientCertificate` and `PreProdClientCertificate` from API Gateway.

Use the `describe-stacks` command from the previous step to get the `API Gateway Client Cert` output values. When that's done, run the following AWS CLI commands, replacing the `client-certificate-id` with your certificate values, and save the certificate output.

`aws apigateway get-client-certificate --client-certificate-id MIIDVDCCAr0CAQAweTEeMBwG...frw3tnx --output text`

`aws apigateway get-client-certificate --client-certificate-id MIIDoTCCAwqgAwIBAgIMCRkox...tt3rdw --output text`

For more information, see [Use Client-Side SSL Certificates for Authentication by the Backend](https://docs.aws.amazon.com/apigateway/latest/developerguide/getting-started-client-side-ssl-authentication.html) in the *Amazon API Gateway Developer Guide*.

## 5. Test the API Gateway Integration

The next step is to verify that the API in API Gateway is integrated with your application. The [Postman](https://www.getpostman.com/) app is a convenient testing tool for verifying this because it provides fields for adding your signing information to an HTTPS request.

Follow the instructions in [Use Postman to Call an API](https://docs.aws.amazon.com/apigateway/latest/developerguide/how-to-use-postman-to-call-api.html) to send a test request in Postman. If you want, you can convert the response to CURL using the code snippet generator to view the headers and body. 

For a GET request, the Postman CURL response will look something like:

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

## 6. Register Your Scalable Target

You will now register your resource's capacity as a scalable target with Application Auto Scaling. A scalable target is a resource that Application Auto Scaling can scale out or scale in.

Note: Be sure to use the correct permissions when registering a scalable target, so that the [service-linked role](https://docs.aws.amazon.com/autoscaling/application/userguide/application-auto-scaling-service-linked-roles.html) is automatically created. Otherwise, the scaling function will not work. 

Before you register your scalable target, you'll need to run the following command to save the Resource ID in a txt file (with no newline character at the end of the file). Provide the Resource ID from step 3. 

The command will look like this, but with your Resource ID:

```
$ echo -n "https://example.execute-api.us-west-2.amazonaws.com/prod/scalableTargetDimensions/1-23456789" > ~/custom-resource-id.txt
```

This saves the file as `custom-resource-id.txt` in your home directory. You can now use the [register-scalable-target](https://docs.aws.amazon.com/cli/latest/reference/application-autoscaling/register-scalable-target.html) command to register your scalable target:

```
$ aws application-autoscaling register-scalable-target --service-namespace custom-resource --scalable-dimension custom-resource:ResourceType:Property --resource-id file://~/custom-resource-id.txt --min-capacity 0 --max-capacity 10
```

This registers your scalable target with Application Auto Scaling, and allows it to manage capacity within the range of 0 to 10 capacity units. 

## 7. Create a Scaling Policy

In this step, you create a sample scaling policy for your custom resource that specifies how the scalable target should be scaled when CloudWatch alarms are triggered. 

For example, for target tracking, you define a target tracking scaling policy that meets your resource's specific requirements by creating a custom metric. You can define a custom metric based on any metric that changes in proportion to scaling. 

Not all metrics work for target tracking. The metric must be a valid utilization metric, and it must describe how busy your custom resource is. The value of the metric must increase or decrease in inverse proportion to the number of capacity units. That is, the value of the metric should decrease when capacity increases. 

The following cat command creates a sample metric for your scalable target in a `config.json` file in your home directory:

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

Use the following [put-scaling-policy](https://docs.aws.amazon.com/cli/latest/reference/application-autoscaling/put-scaling-policy.html) command, along with the `config.json` file you created previously, to create a scaling policy named `custom-tt-scaling-policy` that keeps the average utilization of your custom resource at 50 percent:

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

For more information about target tracking scaling policies, see [Target Tracking Scaling Policies for Application Auto Scaling ](https://docs.aws.amazon.com/autoscaling/application/userguide/application-auto-scaling-target-tracking.html) in the Application Auto Scaling documentation.

For more information about creaing custom metrics, see [Publish Custom Metrics](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/publishingMetrics.html) in the CloudWatch documentation. 

## 8. Trigger the Scaling Policy Using a Bash Script

Now you can test your scaling policy by publishing sample metric data to CloudWatch. CloudWatch alarms will trigger the scaling policy and calculate the scaling adjustment based on the metric and the target value. 

Use the following bash script to run CLI commands at the command line:

```bash
// Command to put metric data that breaches AlarmHigh
$ while sleep 3
do
  aws cloudwatch put-metric-data --metric-name MyAverageUtilizationMetric --namespace MyNamespace --value 70 --unit Percent --dimensions MyMetricDimensionName=MyMetricDimensionValue
  echo -n "."
done
```

This script publishes data points to CloudWatch to trigger the scaling policy based on live metric data. The while loop is used to perform the CLI command an unknown number of times. The "sleep 3" conditions pauses the execution for 3 seconds on each iteration. After you verify that scaling works (which is the next step in this tutorial), use the Ctrl+C keyboard shortcut to stop the script.

It may take a few minutes before your scaling policy is invoked. When the target ratio exceeds 50 percent for a sustained period of time, Application Auto Scaling notifies your custom resource to adjust capacity upward, so that the 50 percent target utilization can be maintained.

## 9. View the Scaling Actions 

In this step, you view the scaling actions that were created in response to the bash script in the previous step.

Run the [describe-scaling-activities](https://docs.aws.amazon.com/cli/latest/reference/application-autoscaling/describe-scaling-activities.html) command:

```
$ aws application-autoscaling describe-scaling-activities --service-namespace custom-resource --resource-id file://~/custom-resource-id.txt --max-results 20
```

You should eventually see output that looks like this: 
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

Note: If you are using the [sample-api-server](./sample-api-server/) that is provided in this project, you can also see the scaling events in the API log.  

## 10. Deregister a Scalable Target

To deregister a scalable target that you no longer need, use the txt file you created in step 6 and run the [deregister-scalable-target](https://docs.aws.amazon.com/cli/latest/reference/application-autoscaling/deregister-scalable-target.html) command:

```
$ aws application-autoscaling deregister-scalable-target --service-namespace custom-resource --scalable-dimension custom-resource:ResourceType:Property --resource-id file://~/custom-resource-id.txt
```

Deregistering a scalable target deletes the target tracking scaling policies and the CloudWatch alarms that Application Auto Scaling created on your behalf. 

# License Summary

This sample code is made available under a modified MIT-0 license. See the [LICENSE](https://github.com/aws/aws-auto-scaling-custom-resource/blob/master/LICENSE) file.
