import React from 'react';
import styled from 'styled-components';

interface IProps extends React.InputHTMLAttributes<HTMLInputElement> {}

const Radio: React.FC<IProps> = (props) => <RadioStyled {...props} />;

const RadioStyled = styled.input`
  -webkit-appearance: none;
  -moz-appearance: none;
  appearance: none;
  outline: none;
  cursor: pointer;
  
  &:after,
  &:checked:after {
    position: relative;
    top: 2px;
    width: 12px;
    height: 12px;
    border-radius: 12px;
    background-color: transparent;
    content: '';
    display: inline-block;
    visibility: visible;
    margin: 0 20px;
    border: 1px solid #444;
  }
  
  &:checked:after {
    background-color: #f36621;
  }
`;

export default Radio;
