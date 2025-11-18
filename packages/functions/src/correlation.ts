import { APIGatewayProxyHandler } from 'aws-lambda';
import * as AWS from 'aws-sdk';

const dynamodb = new AWS.DynamoDB();
const tableName = process.env.tableName || 'unknown_table';

export const handler: APIGatewayProxyHandler = async (event, context) => {
  try {
    // Scan the table to retrieve all records
    const response = await dynamodb
      .scan({
        TableName: tableName,
      })
      .promise();

    // Check if the scan returned any items
    if (response.Items && response.Items.length > 0) {
      // Map over the Items to convert them to a more readable format
      const records = response.Items.map(item => {
        const unmarshalledItem = AWS.DynamoDB.Converter.unmarshall(item);

        // Rename fields to match expected names
        const filteredItem = {
          examsSolved: parseInt(unmarshalledItem.numberOfExamsSolved || '0'),
          avg_overall_avg: parseFloat(unmarshalledItem.overallavg || '0'),
          readingScore: parseFloat(unmarshalledItem.readingbandscore || '0'),
          writingScore: parseFloat(unmarshalledItem.writingbandscore || '0'),
          listeningScore: parseFloat(
            unmarshalledItem.Listeningbandscore || '0',
          ),
          speakingScore: parseFloat(unmarshalledItem.speakingbandscore || '0'),
        };

        // Check if all relevant fields are 0 (skip the record if true)
        const fieldsToCheck = [
          filteredItem.avg_overall_avg,
          filteredItem.readingScore,
          filteredItem.writingScore,
          filteredItem.listeningScore,
          filteredItem.speakingScore,
        ];

        const allZero = fieldsToCheck.every(field => field === 0);

        // Skip this record if all fields are 0
        return allZero ? null : filteredItem;
      }).filter(item => item !== null); // Remove any null records from the array

      // Prepare the graph data for the 7 graphs
      const graphData = {
        avg: records.map(item => ({
          x: item.examsSolved,
          y: item.avg_overall_avg,
        })),
        readingVsListening: records.map(item => ({
          x: item.readingScore,
          y: item.listeningScore,
        })),
        readingVsWriting: records.map(item => ({
          x: item.readingScore,
          y: item.writingScore,
        })),
        readingVsSpeaking: records.map(item => ({
          x: item.readingScore,
          y: item.speakingScore,
        })),
        listeningVsWriting: records.map(item => ({
          x: item.listeningScore,
          y: item.writingScore,
        })),
        listeningVsSpeaking: records.map(item => ({
          x: item.listeningScore,
          y: item.speakingScore,
        })),
        writingVsSpeaking: records.map(item => ({
          x: item.writingScore,
          y: item.speakingScore,
        })),
      };

      // Return the data for all seven graphs
      return {
        statusCode: 200,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Credentials': 'true',
          'Access-Control-Allow-Methods': 'GET,OPTIONS',
        },
        body: JSON.stringify({
          graphData,
        }),
      };
    } else {
      // Handle case where no records are found
      return {
        statusCode: 404,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Credentials': 'true',
        },
        body: JSON.stringify({ error: 'No records found' }),
      };
    }
  } catch (error) {
    console.error('Error fetching records:', error);

    // Return an error message if there's an issue
    return {
      statusCode: 500,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Credentials': 'true',
      },
      body: JSON.stringify({ error: 'Could not fetch records', details: String(error) }),
    };
  }
};
