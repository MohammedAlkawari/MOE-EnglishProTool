import { APIGatewayProxyHandler } from 'aws-lambda';
import * as AWS from 'aws-sdk';

const dynamodb = new AWS.DynamoDB();
const tableName = process.env.tableName || 'unknown_table';

export const handler: APIGatewayProxyHandler = async (event, context) => {
  try {
    // Query DynamoDB for items where PK = 'AGGREGATES' and SK = 'TOTALS'
    const response = await dynamodb
      .query({
        TableName: tableName,
        KeyConditionExpression: 'PK = :pk and SK = :sk',
        ExpressionAttributeValues: {
          ':pk': { S: 'AGGREGATES' },
          ':sk': { S: 'TOTALS' },
        },
      })
      .promise();

    // Check if the query returned any items
    if (response.Items && response.Items.length > 0) {
      const item = response.Items[0]; // Since there's only one aggregate entry with PK 'AGGREGATES' and SK 'TOTALS'

      // Extract values from the item and convert them to numbers, with fallback to 0 if undefined
      const studentCount = item.student_count?.N ? +item.student_count.N : 0;
      const avgOverallAvg = item.Avg_overall_avg?.N
        ? +item.Avg_overall_avg.N
        : 0;
      const avgReadingScore = item.avg_reading_score?.N
        ? +item.avg_reading_score.N
        : 0;
      const avgListeningScore = item.avg_listening_score?.N
        ? +item.avg_listening_score.N
        : 0;
      const avgSpeakingScore = item.avg_speaking_score?.N
        ? +item.avg_speaking_score.N
        : 0;
      const avgWritingScore = item.avg_writing_score?.N
        ? +item.avg_writing_score.N
        : 0;

      // Return the result with the aggregate values in the response body
      return {
        statusCode: 200,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Credentials': 'true',
          'Access-Control-Allow-Methods': 'GET,OPTIONS',
        },
        body: JSON.stringify({
          student_count: studentCount,
          avg_overall_avg: avgOverallAvg,
          avg_reading_score: avgReadingScore,
          avg_listening_score: avgListeningScore,
          avg_speaking_score: avgSpeakingScore,
          avg_writing_score: avgWritingScore,
        }),
      };
    } else {
      // Handle case where no aggregates are found
      return {
        statusCode: 404,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Credentials': 'true',
        },
        body: JSON.stringify({ error: 'Aggregates not found' }),
      };
    }
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
