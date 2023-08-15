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
  otp: string;
  setOtp: OnChange;
  handleSendAnotherCodeClick: () => void;
  handleUseDifferentEmailClick: () => void;
}

const Verify: React.FC<IProps> = ({
  handleFormSubmit,
  isAuthenticatePending,
  isAuthenticateRejected,
  otp,
  setOtp,
  handleSendAnotherCodeClick,
  handleUseDifferentEmailClick,
}) => (
  <>
    <Helmet>
      <title>Sign in</title>
      <meta name="description" content="Sign in to TA" />
    </Helmet>

    <Form onSubmit={handleFormSubmit}>
      <Title>Authentication</Title>

      <SubtitleStyled>Check your email. We&apos;ve sent you a secret code</SubtitleStyled>

      <FormGroup label="code">
        <Input
          required
          autoFocus
          placeholder="Enter code"
          value={otp}
          onChange={setOtp}
        />
      </FormGroup>

      <HelpLinksStyled>
        <HelpLinkStyled onClick={handleSendAnotherCodeClick}>Send another code</HelpLinkStyled>

        <HelpDividerStyled>or</HelpDividerStyled>

        <HelpLinkStyled onClick={handleUseDifferentEmailClick}>
          Send to different email
        </HelpLinkStyled>
      </HelpLinksStyled>

      <LoginButton disabled={!otp} isLoading={isAuthenticatePending} type="submit">
        submit
      </LoginButton>

      {isAuthenticateRejected && <Error>Something went wrong :(</Error>}
    </Form>
  </>
);

const SubtitleStyled = styled.div`
  margin-top: -32px;
  margin-bottom: 50px;
  text-align: center;
`;

const HelpLinksStyled = styled.div`
  padding: 32px 0px;
  display: flex;
  justify-content: center;
`;

const HelpLinkStyled = styled.div`
  color: #f36621;
  cursor: pointer;

  &:hover {
    color: #bd450a;
    text-decoration: underline;
  }
`;

const HelpDividerStyled = styled.div`
  padding: 0px 8px;
`;

export default Verify;
