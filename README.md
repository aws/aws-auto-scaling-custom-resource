## AWS Auto Scaling Custom Resource

Libraries, samples and tools to help AWS Customers to onboard with Custom Resource Auto Scaling.
### CFN Template 

1. CFN template that uses swagger and input parameters to launch API Gateway stack that integrates with customer's endpoint
2. Include Lambda to parse available certificates and notify customer of certificate expiry.

### Parameters

IntegrationHttpEndpoint : customer's endpoint

SNSSubscriptionEmail : email address to send client certificate expiry notifications to

### Example

```bash
aws cloudformation create-stack \
    --stack-name MyCustomResourceAPIGatewayStack \
    --template-body file:///Volumes/Unix/aws-auto-scaling-custom-resource/cloudformation/templates/custom-resource-api.yaml \ 
    --region us-west-2 \
    --capabilities CAPABILITY_NAMED_IAM CAPABILITY_IAM \
    --parameters \
        ParameterKey=SNSSubscriptionEmail,ParameterValue="amznhang@amazon.com" \
        ParameterKey=IntegrationHttpEndpoint,ParameterValue='"https://abc.com/scalableTargetDimensions/{scalableTargetDimensionId}"'
```

## License Summary

This sample code is made available under a modified MIT license. See the LICENSE file.
