import React from 'react';
import styled from 'styled-components';

const Title: React.FC = ({ children }) => <TitleStyled>{children}</TitleStyled>;

const TitleStyled = styled.h2`
  font-size: 30px;
  line-height: 35px;
  font-weight: 500;
  text-align: center;
  margin-bottom: 50px;
`;

export default Title;
