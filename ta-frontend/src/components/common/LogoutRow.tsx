import React from 'react';
import { useDispatch } from 'react-redux';
import styled from 'styled-components';

import { logoutAsync } from '@/store/actions/authenticate';

import Button from '@/components/common/Button';

const LogoutRow: React.FC = () => {
  const dispatch = useDispatch();

  const handleLogoutClick = () => {
    dispatch(logoutAsync());
  };

  return (
    <LogoutRowStyled>
      <LogoutButton onClick={handleLogoutClick}>Logout</LogoutButton>
    </LogoutRowStyled>
  );
};

const LogoutRowStyled = styled.div`
  height: 52px;
  display: flex;
  align-items: flex-end;
  justify-content: flex-end;
`;

const LogoutButton = styled(Button)`
  font-size: 14px;
`;

export default LogoutRow;
