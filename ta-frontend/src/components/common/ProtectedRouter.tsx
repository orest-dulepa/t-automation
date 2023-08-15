import React from 'react';
import { useSelector } from 'react-redux';
import { Route, RouteProps, Redirect } from 'react-router';
import styled from 'styled-components';

import { selectIsUserLoggedIn, selectIsUserPending } from '@/store/selectors/user';

import GlobalLoader from '@/components/common/GlobalLoader';

const ProtectedRouter: React.FC<RouteProps> = (props) => {
  const isLoggedIn = useSelector(selectIsUserLoggedIn);
  const isPending = useSelector(selectIsUserPending);

  if (isPending) {
    return (
      <LoaderWrapperStyled>
        <GlobalLoader />
      </LoaderWrapperStyled>
    );
  }

  return isLoggedIn ? <Route {...props} /> : <Redirect to="/" />;
};

const LoaderWrapperStyled = styled.div`
  height: 100vh;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
`;

export default ProtectedRouter;
