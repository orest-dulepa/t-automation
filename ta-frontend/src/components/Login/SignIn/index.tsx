import React from 'react';
import { Helmet } from 'react-helmet';
import styled from 'styled-components';

import { OnChange } from '@/components/common/hooks/useInput';
import FormGroup from '@/components/common/FormGroup';
import Input from '@/components/common/Input';
import Error from '@/components/common/Error';

import Form from '../common/Form';
import Title from '../common/Title';
import LoginButton from '../common/LoginButton';

interface IProps {
  handleFormSubmit: (e: React.FormEvent<HTMLFormElement>) => void;
  isAuthenticatePending: boolean;
  isAuthenticateRejected: boolean;
  email: string;
  setEmail: OnChange;
}

const SignIn: React.FC<IProps> = ({
  handleFormSubmit,
  isAuthenticatePending,
  isAuthenticateRejected,
  email,
  setEmail,
}) => (
  <>
    <Helmet>
      <title>Sign in</title>
      <meta name="description" content="Sign in to TA" />
    </Helmet>

    <Form onSubmit={handleFormSubmit}>
      <Title>
        Sign in to
        <br />
        TA
      </Title>

      <FormGroup label="email address">
        <Input
          type="email"
          required
          autoFocus
          placeholder="Enter email"
          value={email}
          onChange={setEmail}
        />
      </FormGroup>

      <AlertStyled>
        <AlertTitleStyled>New around here?</AlertTitleStyled>
        <AlertSubtitleStyled>Just enter your email to get started!</AlertSubtitleStyled>
      </AlertStyled>

      <LoginButton disabled={!email} isLoading={isAuthenticatePending} type="submit">
        submit
      </LoginButton>

      {isAuthenticateRejected && <Error>Something went wrong :(</Error>}
    </Form>
  </>
);

const AlertStyled = styled.div`
  position: relative;
  padding: 12px 20px 12px 55px;
  border: 1px solid rgba(241, 242, 246, 0.6);
  border-radius: 4px;
  margin: 45px 0px;
  background: rgba(241, 242, 246, 0.6) url('/assets/info.svg') no-repeat 10px 50%;
`;

const AlertTitleStyled = styled.div`
  font-weight: 500;
  color: rgb(52, 58, 64);
`;

const AlertSubtitleStyled = styled.div`
  color: #186a80;
`;

export default SignIn;
