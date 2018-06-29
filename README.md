## AWS Auto Scaling Custom Resource

Libraries, samples and tools to help AWS Customers to onboard with Custom Resource Auto Scaling.
### CFN Template 

1. CFN template that uses swagger and input parameters to launch API Gateway stack that integrates with customer's endpoint
2. Include Lambda to parse available certificates and notify customer of certificate expiry.

### Parameters

1. IntegrationHttpEndpoint: customer's endpoint
1. SNSSubscriptionEmail: email address to send client certificate expiry notifications to

### Outputs

1. PreProdReourceIdPrefix: Pre-prod ResourceId prefix for the resource to be registered in AWS Auto Scaling
1. ProdReourceIdPrefix: Prod ResourceId prefix for the resource to be registered in AWS Auto Scaling
1. S3BucketName: S3 bucket where cloud trails are stored

### Example

```bash
aws cloudformation create-stack \
    --stack-name CustomResourceStack \
    --template-body file:///home/user/custom-resource-api.yaml \
    --region us-west-2 \
    --capabilities CAPABILITY_NAMED_IAM CAPABILITY_IAM \
    --parameters \
        ParameterKey=SNSSubscriptionEmail,ParameterValue="your.email@id" \
        ParameterKey=IntegrationHttpEndpoint,ParameterValue='"https://abc.com/scalableTargetDimensions/{scalableTargetDimensionId}"'
```

## License Summary

This sample code is made available under a modified MIT license. See the LICENSE file.
