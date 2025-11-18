import { APIGatewayProxyHandler } from 'aws-lambda';
import * as AWS from 'aws-sdk';

const dynamodb = new AWS.DynamoDB();
const tableName = process.env.tableName || 'unknown_table'; // Table 1
const tableName2 = process.env.tableName2 || 'unknown_table2'; // Table 2

export const handler: APIGatewayProxyHandler = async (event, context) => {
  try {
    // ============================
    // Step 1: Fetch Top 3 Overall Avg
    // ============================
    const topByOverallAvgResponse = await dynamodb
      .scan({
        TableName: tableName,
        ProjectionExpression: 'username, SK, overallavg',
      })
      .promise();

    const topByOverallAvg = (topByOverallAvgResponse.Items || [])
      .map(item => ({
        username: item.username?.S,
        school: item.SK?.S,
        overallAvg: item.overallavg?.N ? parseFloat(item.overallavg.N) : 0,
      }))
      .sort((a, b) => b.overallAvg - a.overallAvg)
      .slice(0, 3);

    // ============================
    // Step 2: Fetch Top 3 Exams Solved
    // ============================
    const topByExamsSolvedResponse = await dynamodb
      .scan({
        TableName: tableName,
        ProjectionExpression: 'username, SK, numberOfExamsSolved',
      })
      .promise();

    const topByExamsSolved = (topByExamsSolvedResponse.Items || [])
      .map(item => ({
        username: item.username?.S,
        school: item.SK?.S,
        numberOfExamsSolved: item.numberOfExamsSolved?.N
          ? parseInt(item.numberOfExamsSolved.N, 10)
          : 0,
      }))
      .sort((a, b) => b.numberOfExamsSolved - a.numberOfExamsSolved)
      .slice(0, 3);

    // ============================
    // Step 3: Fetch Top 3 Streak Users from Table 2
    // ============================
    const streakResponse = await dynamodb
      .scan({
        TableName: tableName2,
        ProjectionExpression: 'PK, StreakCounter',
      })
      .promise();

    const topStreakUsers = (streakResponse.Items || [])
      .map(item => ({
        PK: item.PK?.S,
        streakCounter: item.StreakCounter?.N
          ? parseInt(item.StreakCounter.N, 10)
          : 0,
      }))
      .sort((a, b) => b.streakCounter - a.streakCounter) // Sort by highest streak first
      .slice(0, 3); // Get top 3 users

    // ============================
    // Step 4: Query Table 1 for User Details (PK Only)
    // ============================
    const topStreakUserDetails = [];
    for (const streakUser of topStreakUsers) {
      if (streakUser.PK) {
        const userResponse = await dynamodb
          .query({
            TableName: tableName,
            KeyConditionExpression: 'PK = :pk',
            ExpressionAttributeValues: {
              ':pk': { S: streakUser.PK },
            },
            ProjectionExpression: 'username, SK', // Fetch username and school
          })
          .promise();

        const user = userResponse.Items?.[0];
        if (user) {
          topStreakUserDetails.push({
            PK: streakUser.PK,
            streakCounter: streakUser.streakCounter,
            username: user.username?.S,
            school: user.SK?.S,
          });
        }
      }
    }

    // ============================
    // Step 5: Return Combined Results
    // ============================
    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Credentials': 'true',
        'Access-Control-Allow-Methods': 'GET,OPTIONS',
      },
      body: JSON.stringify({
        topByOverallAvg,
        topByExamsSolved,
        topByHighestStreak: topStreakUserDetails, // Return top 3 streak users
      }),
    };
  } catch (error) {
    console.error('Error fetching data:', error);

    return {
      statusCode: 500,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Credentials': 'true',
      },
      body: JSON.stringify({ error: 'Could not fetch data', details: String(error) }),
    };
  }
};
