import React from 'react';
import styled from 'styled-components';

interface IProps extends React.FormHTMLAttributes<HTMLFormElement> {}

const Form: React.FC<IProps> = ({ children, ...rest }) => (
  <FormStyled {...rest}>
    <LogoStyled src="/assets/logo.svg" />
    {children}
  </FormStyled>
);

const LogoStyled = styled.img`
  display: block;
  width: 72px;
  height: 72px;
  margin: 0px auto 50px;
`;

const FormStyled = styled.form`
  padding: 47px 30px 57px;
  width: 450px;
  box-shadow: 0 0.5rem 1rem rgba(25, 46, 67, 0.15);
  border-radius: 4px;
  background-color: #fff;
`;

export default Form;
