import { APIGatewayProxyHandler } from 'aws-lambda';
import * as AWS from 'aws-sdk';

const dynamodb = new AWS.DynamoDB();
const tableName = process.env.tableName || 'unknown_table';
const tableName2 = process.env.tableName2 || 'unknown_table';

export const handler: APIGatewayProxyHandler = async (event, context) => {
  try {
    const table1Response = await dynamodb
      .scan({
        TableName: tableName,
        FilterExpression: "contains(SK, :sk)",
        ExpressionAttributeValues: {
          ":sk": { S: "USER#INFO" },
        },
      })
      .promise();

    if (!table1Response.Items || table1Response.Items.length === 0) {
      return {
        statusCode: 404,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Credentials': 'true',
        },
        body: JSON.stringify({ error: 'No matching records found in Table 1' }, null, 2),
      };
    }

    const results = await Promise.all(
      table1Response.Items.map(async (item) => {
        const pk = item.PK?.S;
        const streakCounter = item.StreakCounter?.N;

        if (!pk || !streakCounter) {
          return null;
        }

        // Query Table 2 concurrently for each PK
        const table2Response = await dynamodb
          .query({
            TableName: tableName2,
            KeyConditionExpression: 'PK = :pk',
            ExpressionAttributeValues: {
              ':pk': { S: pk },
            },
          })
          .promise();

        const username =
          table2Response.Items && table2Response.Items.length > 0
            ? table2Response.Items[0].username?.S
            : null;

        // Extract overallavg from Table 2
        const overallavg =
          table2Response.Items && table2Response.Items.length > 0
            ? table2Response.Items[0].overallavg?.N
            : null;

        return {
          StreakCounter: Number(streakCounter),
          Username: username,
          OverallAvg: overallavg ? Number(overallavg) : null,
        };
      })
    );

    // Filter out any null results from the map operation
    const filteredResults = results.filter((result) => result !== null);

    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Credentials': 'true',
        'Access-Control-Allow-Methods': 'GET,OPTIONS',
      },
      body: JSON.stringify({ results: filteredResults }, null, 2),
    };
  } catch (error) {
    console.error('Error processing request:', error);

    return {
      statusCode: 500,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Credentials': 'true',
      },
      body: JSON.stringify({ error: 'Internal Server Error', details: String(error) }, null, 2),
    };
  }
};
