import React from 'react';
import styled from 'styled-components';

const RadioAndCheckboxGroup: React.FC = (children) => <RadioAndCheckboxGroupStyled {...children} />;

const RadioAndCheckboxGroupStyled = styled.div`
  display: flex;
  align-items: center;
`;

export default RadioAndCheckboxGroup;
