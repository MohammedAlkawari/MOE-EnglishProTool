import { S3 } from 'aws-sdk';
import { APIGatewayProxyHandler } from 'aws-lambda';
import { Bucket } from 'sst/node/bucket';
import { runModel } from './utilities';
const s3 = new S3();

export const handler: APIGatewayProxyHandler = async (event) => {
  try {
    const userID = event.requestContext.authorizer!.jwt.claims.sub; // Target user ID
    const bucketName = Bucket.ExtractedTXT.bucketName; // Name of the Extracted txt S3 bucket

    // List all objects in the S3 bucket
    const objects = await s3.listObjectsV2({ Bucket: bucketName }).promise();

    let targetObjectKey: string | null = null;

    // Find the object whose name contains the userID
    for (const obj of objects.Contents || []) {
      if (obj.Key && obj.Key.includes(userID) && obj.Key.includes("Speaking")) {
        targetObjectKey = obj.Key;
        break;
      }
    }

    if (!targetObjectKey) {
      return {
        statusCode: 404,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Credentials': 'true',
          'Access-Control-Allow-Methods': 'GET,OPTIONS',
        },
        body: JSON.stringify({ message: `No object found for userID: ${userID}` }),
      };
    }

    // Retrieve the content of the target object
    const targetObject = await s3
      .getObject({ Bucket: bucketName, Key: targetObjectKey })
      .promise();

    const objectContent = targetObject.Body?.toString('utf-8') || '';
    
    return {
        statusCode: 200,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Credentials': 'true',
          'Access-Control-Allow-Methods': 'GET,OPTIONS',
        },
        body: JSON.stringify({
         objectContent
        }),
      };
  } catch (error) {
    console.error('Error:', error);
    return {
      statusCode: 500,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Credentials': 'true',
        'Access-Control-Allow-Methods': 'GET,OPTIONS',
      },
      body: JSON.stringify({ 
        message: 'Internal server error',
        details: String(error)
      }),
    };
  }
};
