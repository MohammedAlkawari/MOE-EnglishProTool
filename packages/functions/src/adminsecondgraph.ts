import { APIGatewayProxyHandler } from 'aws-lambda';
import * as AWS from 'aws-sdk';

const dynamodb = new AWS.DynamoDB();
const tableName = process.env.tableName || 'unknown_table';

export const handler: APIGatewayProxyHandler = async (event, context) => {
  try {
    // Query DynamoDB for all items with PK = 'AGGREGATES'
    const response = await dynamodb
      .query({
        TableName: tableName,
        KeyConditionExpression: 'PK = :pk',
        ExpressionAttributeValues: {
          ':pk': { S: 'AGGREGATES' },
        },
      })
      .promise();

    // Extract the items from the response
    const aggregates = response.Items || [];

    // Function to safely get the value of a specific attribute from DynamoDB item
    const getNumberValue = (
      item: AWS.DynamoDB.AttributeMap,
      key: string,
    ): number => {
      return item[key]?.N ? +item[key].N : 0;
    };

    // Filter out items where SK = 'TOTALS' or SK = 'MOE' and then map the rest to extract the school name and avg_overall_avg
    const result = aggregates
      .filter((item: AWS.DynamoDB.AttributeMap) => 
        item.SK?.S !== 'TOTALS' && item.SK?.S !== 'MOE' // Skip items where SK = 'TOTALS' or 'MOE'
      )
      .map((item: AWS.DynamoDB.AttributeMap) => {
        const schoolName = item.SK?.S; // Extract the school name from the SK attribute
        const avgOverallAvg = getNumberValue(item, 'Avg_overall_avg');
        // Return the school name and the avg_overall_avg
        return {
          schoolName,
          avg_overall_avg: avgOverallAvg,
        };
      });

    // Return the result with CORS headers
    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Credentials': 'true',
        'Access-Control-Allow-Methods': 'GET,OPTIONS',
      },
      body: JSON.stringify(result),
    };
  } catch (error) {
    console.error('Error fetching aggregates:', error);

    // Return an error message if there's an issue
    return {
      statusCode: 500,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Credentials': 'true',
      },
      body: JSON.stringify({ error: 'Could not fetch aggregates', details: String(error) }),
    };
  }
};
