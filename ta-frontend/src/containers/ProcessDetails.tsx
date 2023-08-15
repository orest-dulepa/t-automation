import React, { useEffect } from 'react';
import { RouteComponentProps } from 'react-router-dom';
import { Helmet } from 'react-helmet';
import { useDispatch, useSelector } from 'react-redux';
import styled from 'styled-components';

import {
  processDetailsActions,
  loadProcessDetails,
  downloadArtifactAsync,
} from '@/store/actions/process-details';

import {
  selectProcessDetails,
  selectIsProcessDetailsPending,
  selectIsProcessDetailsRejected,
  selectIsArtifactDownloading,
  selectProcessDetailsErrorMsg,
} from '@/store/selectors/process-details';

import Sidebar from '@/components/common/Sidebar';
import LogoutRow from '@/components/common/LogoutRow';
import GlobalLoader from '@/components/common/GlobalLoader';

import Error from '@/components/ProcessDetails/Error';
import Process from '@/components/ProcessDetails/Process';

interface IProps extends RouteComponentProps<{ id: string }> {}

const ProcessDetails: React.FC<IProps> = ({ match }) => {
  const { id } = match.params;

  const processDetails = useSelector(selectProcessDetails);
  const isProcessDetailsPending = useSelector(selectIsProcessDetailsPending);
  const isProcessDetailsRejected = useSelector(selectIsProcessDetailsRejected);
  const isArtifactDownloading = useSelector(selectIsArtifactDownloading);
  const processDetailsErrorMsg = useSelector(selectProcessDetailsErrorMsg);

  const dispatch = useDispatch();

  useEffect(() => {
    dispatch(loadProcessDetails(id));

    return () => {
      dispatch(processDetailsActions.reset());
    };
  }, []);

  const downloadArtifact = (key: string) => () => {
    dispatch(downloadArtifactAsync(key));
  };

  const renderBody = () => {
    switch (true) {
      case isProcessDetailsPending: {
        return (
          <InfoWrapper>
            <GlobalLoader />
          </InfoWrapper>
        );
      }
      case isProcessDetailsRejected: {
        return (
          <InfoWrapper>
            <Error errorMsg={processDetailsErrorMsg} />
          </InfoWrapper>
        );
      }
      default: {
        if (!processDetails) return null;
        return (
          <Process
            downloadArtifact={downloadArtifact}
            processDetails={processDetails}
            isArtifactDownloading={isArtifactDownloading}
          />
        );
      }
    }
  };

  return (
    <>
      <Helmet>
        <title>
          Details #
          {id}
        </title>
      </Helmet>

      <ProcessWrapperStyled>
        <Sidebar />

        <ProcessesContentStyled>
          <LogoutRow />

          {renderBody()}
        </ProcessesContentStyled>
      </ProcessWrapperStyled>
    </>
  );
};

const ProcessWrapperStyled = styled.div`
  display: flex;
  min-height: 100vh;
`;

const ProcessesContentStyled = styled.div`
  width: calc(100% - 72px);
  padding: 0px 25px;
`;

const InfoWrapper = styled.div`
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
`;

export default ProcessDetails;
