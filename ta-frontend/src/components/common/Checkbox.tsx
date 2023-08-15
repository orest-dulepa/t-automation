import React from 'react';
import styled from 'styled-components';

interface IProps extends React.InputHTMLAttributes<HTMLInputElement> {}

const Checkbox: React.FC<IProps> = (props) => <CheckboxStyled {...props} />;

const CheckboxStyled = styled.input`
  -webkit-appearance: none;
  -moz-appearance: none;
  appearance: none;
  outline: none;
  cursor: pointer;
  
  &:after,
  &:checked:after {
    position: relative;
    top: 1px;
    box-sizing: border-box;
    width: 16px;
    height: 16px;
    border-radius: 2px;
    background-color: transparent;
    content: '✓';
    color: white;
    display: inline-block;
    visibility: visible;
    margin: 0 20px;
    padding-left: 1px;
    border: 1px solid #444;
    line-height: 16px;
  }
  
  &:checked:after {
    background-color: #f36621;
  }
`;

export default Checkbox;
