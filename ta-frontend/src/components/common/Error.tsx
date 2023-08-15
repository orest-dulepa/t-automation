import React from 'react';
import styled from 'styled-components';

const Error: React.FC = ({ children }) => <ErrorStyled>{children}</ErrorStyled>;

const ErrorStyled = styled.div`
  text-align: center;
  font-size: 14px;
  color: red;
  font-weight: 500;
  max-width: 75%;
  margin: 10px auto;
`;

export default Error;
