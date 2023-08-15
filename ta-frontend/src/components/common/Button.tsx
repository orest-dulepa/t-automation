import React from 'react';
import styled from 'styled-components';

export interface IProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  isLoading?: boolean;
}

const Button: React.FC<IProps> = (props) => {
  const {
    isLoading,
    disabled,
    children,
    ...rest
  } = props;

  return (
    <ButtonStyled {...rest} disabled={disabled || isLoading}>
      {isLoading ? 'Loading...' : children}
    </ButtonStyled>
  );
};

const ButtonStyled = styled.button`
  display: inline-block;
  font-weight: 400;
  color: #fff;
  background-color: #f36621;
  text-align: center;
  vertical-align: middle;
  user-select: none;
  border: 1px solid #f36621;
  padding: 0.375rem 0.75rem;
  font-size: 1rem;
  line-height: 1.5;
  border-radius: 3px;
  cursor: pointer;
  outline: none;
  transition: color 0.15s ease-in-out, background-color 0.15s ease-in-out,
    border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;

  &:not(:disabled):hover {
    color: #fff;
    background-color: #e2520c;
    border-color: #d54e0c;
  }

  &:not(:disabled):focus {
    color: #fff;
    background-color: #e2520c;
    border-color: #d54e0c;
    box-shadow: 0 0 0 0.2rem rgba(245, 125, 66, 0.5);
  }

  &:disabled {
    opacity: 0.65;
    cursor: not-allowed;
    background-color: #f36621;
    border-color: #f36621;
  }
`;

export default Button;
