import React from 'react';
import styled from 'styled-components';

import Button, { IProps } from '@/components/common/Button';

const LoginButton: React.FC<IProps> = (props) => (
  <WrapperStyled>
    <LoginButtonStyled {...props} />
  </WrapperStyled>
);

const WrapperStyled = styled.div`
  display: flex;
  justify-content: center;
`;

const LoginButtonStyled = styled(Button)`
  text-transform: uppercase;
  font-weight: 500;
  border-radius: 50px;
  padding: 18px 68px;

  &:disabled {
    background-color: #ebedf2;
    border-color: #ebedf2;
  }
`;

export default LoginButton;
