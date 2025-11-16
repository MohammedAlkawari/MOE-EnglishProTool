import { useNavigate, useParams } from 'react-router-dom';
import { Layout } from '../Layout';
import { ConfirmFullTestStart } from '../components/ConfirmFullTestStart';
import useWebSocket, { ReadyState } from 'react-use-websocket';
import { setCachedFeedback, useSocketUrl } from '../utilities';
import { useState } from 'react';
import { ListeningQuestionsPage } from './ListeningQuestionsPage';
import { ReadingQuestionsPage } from './ReadingQuestionsPage';
import { SpeakingQuestionsPage } from './SpeakingQuestionsPage';
import { Spinner } from '../components/Spinner';
import { WritingQuestionsPage } from './WritingQuestionsPage';
import { IntermediatePage } from '../components/IntermediatePage';
import { ToastContainer, toast } from 'react-toastify';
import {
  ListeningSection,
  ReadingSection,
  SpeakingSection,
  WritingAnswer,
  WritingSection,
  getQuestionResponse,
  startFullTestResponse,
  submitFullTestResponse,
} from '../../../functions/src/utilities/fullTestUtilities';

// Everything in this pages depends on this.
type StateType =
  | startFullTestResponse
  | getQuestionResponse
  | submitFullTestResponse
  | null;

export const FullTestPage = () => {
  let out;

  const [state, setState] = useState<StateType>(null);
  const { testId } = useParams();
  const [isLoading, setIsloading] = useState(false);

  const socketUrl = useSocketUrl() ?? '';
  const navigate = useNavigate();
  console.log('State', { state, testId });

  const { sendJsonMessage, readyState } = useWebSocket(socketUrl, {
    onOpen: event => console.log('WebSocket opened successfully', event),
    onClose: event => console.log('WebSocket closed', event),
    onError: error => console.error('WebSocket error:', error),
    ////// Handle incoming messages //////
    onMessage: e => {
      console.log('Incoming WebSocket message:', e);
      try {
        const response = JSON.parse(e.data);
        console.log('Parsed message:', response);

        /* For some reason if answers are graded, we get notifications */
        if (typeof response === 'string') {
          console.log('String response:', response);
          setIsloading(false);
        } else if ('error' in response) {
          console.error('Received error from server:', response.error);
          toast.error(`Error: ${response.error}`);
          
          if (response.error === 'Section is already submitted') {
            sendJsonMessage({
              action: 'fullTestGetQuestion',
              testId: testId,
            });
            console.log('Sent getQuestion message after section already submitted');
            setIsloading(true);
          } else if (response.error === 'The test is finished') {
            navigate('/');
          }
          setIsloading(false);
        } else if ('testID' in response) {
          console.log('Received testID, navigating to test:', response.testID);
          setState(response);
          toast.dismiss();
          setIsloading(false);
          // Navigate after state is set
          setTimeout(() => {
            navigate(`/full-test/${response.testID}`);
          }, 100);
        } else if ('data' in response) {
          console.log('Received data response:', response);
          setState(response);
          toast.dismiss();
          setIsloading(false);
        } else if ('fullItem' in response) {
          console.log('Received fullItem (feedback):', response);
          toast.success('Test completed! Loading feedback...');
          setCachedFeedback(response, testId as string);
          setTimeout(() => {
            navigate(`/feedback/${testId}`);
          }, 1000);
        } else {
          console.warn('Unexpected payload structure:', response);
          setIsloading(false);
        }
      } catch (error) {
        console.error('Error processing WebSocket message:', error);
        setIsloading(false);
      }

      // Message timeout fallback
      setTimeout(() => {
        if (isLoading) {
          console.warn('Message processing timeout, stopping loading state');
          setIsloading(false);
        }
      }, 10000);
    },
    shouldReconnect: () => true,
  });

  ////// Sign in and Connection //////
  if (readyState !== ReadyState.OPEN)
    return (
      <Layout>
        <Spinner
          message={
            socketUrl === ''
              ? 'You have to sign in first'
              : connectionStatus[readyState]
          }
        />
      </Layout>
    );

    ////// Start test, Submit and Question pages //////
  // Test was not started
  if (!testId) {
    const startTest = () => {
      console.log('Starting test...');
      try {
        sendJsonMessage({ action: 'fullTestStart' });
        console.log('WebSocket message sent successfully');
        toast.info('Loading your test...');
      } catch (error) {
        console.error('Error starting test:', error);
        toast.error('Failed to start test. Please try again.');
      }
    };

    out = (
      <Layout>
        <ConfirmFullTestStart onConfirm={() => startTest()} />
      </Layout>
    );
  }

  // Test was started
  else {
    // No current state
    if (!state) {
      if (!isLoading) {
        sendJsonMessage({
          action: 'fullTestGetQuestion',
          testId: testId,
        });
        console.log('Sent message');
        toast.info('Loading your test...');
        setIsloading(true);
      }

      out = (
        <Layout>
          <Spinner message="Loading..." />
        </Layout>
      );
    }

    // There's a state available
    else {
      // console.log('executed w/', state.data?.question);
      const submitAnswers = (answers: any) => {
        console.log('Submitting', { answers });
        sendJsonMessage({
          action: 'fullTestSubmit',
          testId: testId,
          data: {
            type: state.type, // listening, reading, writing, speaking
            answer: answers, // this will be based on the section answer schema
          },
        });
        toast.info('Submitting...');
      };
      const autoSaveAnswers = (answers: any) => {
        console.log('Saving', { answers });
        sendJsonMessage({
          action: 'fullTestAutoSave',
          testId: testId,
          data: {
            type: state.type, // listening, reading, writing, speaking
            answer: answers, // this will be based on the section answer schema
          },
        });
        toast.info('Your answer is getting saved...');
      };

      if (state.data === 'Submitted') {
        const continueTest = () => {
          sendJsonMessage({
            action: 'fullTestGetQuestion',
            testId: testId,
          });
          console.log('Sent message');
          setIsloading(true);
          toast.info(`Loading ${state.type}...`);
        };

        out = (
          <Layout>
            <IntermediatePage
              type={state.type}
              status={state.data}
              onContinue={continueTest}
            />
          </Layout>
        );
      }

      // Question was returned
      else if ('fullItem' in state) {
        return JSON.stringify(state);
      } else {
        const time = Number(testId.slice(0, testId.indexOf('-')));
        // Defensive type check: ensure state.data is an object before using 'in' operator
        const savedAnswers =
          typeof state.data === 'object' && state.data !== null && 'answer' in state.data
            ? state.data.answer?.answer
            : undefined;

        switch (state.type) {
          case 'listening':
            out = (
              <ListeningQuestionsPage
                listeningSection={state.data.question as ListeningSection}
                submitAnswers={submitAnswers}
                autoSaveAnswers={autoSaveAnswers}
                savedAnswers={savedAnswers}
                time={time}
              />
            );
            break;

          case 'reading':
            out = (
              <ReadingQuestionsPage
                readingSection={state.data.question as ReadingSection}
                submitAnswers={submitAnswers}
                autoSaveAnswers={autoSaveAnswers}
                savedAnswers={savedAnswers}
                time={time}
              />
            );
            break;

          case 'writing':
            out = (
              <WritingQuestionsPage
                writingSection={state.data.question as WritingSection}
                submitAnswers={submitAnswers}
                autoSaveAnswers={autoSaveAnswers}
                savedAnswers={savedAnswers as WritingAnswer['answer']}
                time={time}
              />
            );
            break;

          case 'speaking':
            out = (
              <SpeakingQuestionsPage
                speakingSection={state.data.question as SpeakingSection}
                submitAnswers={submitAnswers}
              />
            );
            break;
        }
      }
    }
  }

  return (
    <>
      {out}
      <ToastContainer pauseOnHover={false} />
    </>
  );
};

const connectionStatus = {
  [ReadyState.CONNECTING]: "We're trying to connect to the server...",
  [ReadyState.OPEN]: 'Open',
  [ReadyState.CLOSING]:
    'Failed to connect to the server.  Please try again later',
  [ReadyState.CLOSED]:
    'Failed to connect to the server.  Please try again later',
  [ReadyState.UNINSTANTIATED]: 'Uninstantiated',
};
