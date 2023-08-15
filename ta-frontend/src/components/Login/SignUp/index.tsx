import React from 'react';
import { Helmet } from 'react-helmet';

import { OnChange } from '@/components/common/hooks/useInput';
import Anchor from '@/components/common/Anchor';
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
  firstName: string;
  setFirstName: OnChange;
  lastName: string;
  setLastName: OnChange;
  isNotAllowedEmail: boolean;
}

const SignUp: React.FC<IProps> = ({
  handleFormSubmit,
  isAuthenticatePending,
  isAuthenticateRejected,
  email,
  setEmail,
  firstName,
  setFirstName,
  lastName,
  setLastName,
  isNotAllowedEmail,
}) => (
  <>
    <Helmet>
      <title>Sign up</title>
      <meta name="description" content="Sign up to TA" />
    </Helmet>

    <Form onSubmit={handleFormSubmit}>
      <Title>Become a Bot Manager</Title>

      <FormGroup label="first name">
        <Input
          required
          autoFocus
          placeholder="Enter first name"
          value={firstName}
          onChange={setFirstName}
        />
      </FormGroup>

      <FormGroup label="last name">
        <Input
          required
          placeholder="Enter last name"
          value={lastName}
          onChange={setLastName}
        />
      </FormGroup>

      <FormGroup label="email address">
        <Input
          type="email"
          required
          readOnly
          placeholder="Enter email"
          value={email}
          onChange={setEmail}
        />
      </FormGroup>

      <LoginButton
        disabled={!email || !firstName || !lastName}
        isLoading={isAuthenticatePending}
        type="submit"
      >
        submit
      </LoginButton>

      {isAuthenticateRejected && (
        <Error>
          {isNotAllowedEmail ? (
            <>
              Looks like you&apos;re new around here.
            </>
          ) : (
            'Something went wrong :('
          )}
        </Error>
      )}
    </Form>
  </>
);

export default SignUp;
