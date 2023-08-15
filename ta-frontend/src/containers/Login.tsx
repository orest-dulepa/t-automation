import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Redirect, Link } from 'react-router-dom';
import styled from 'styled-components';

import {
  authenticateActions,
  signInAsync,
  signUpAsync,
  verifyAsync,
} from '@/store/actions/authenticate';
import { AuthenticateSteps } from '@/store/reducers/authenticate';
import { selectIsUserLoggedIn, selectIsUserPending } from '@/store/selectors/user';
import {
  selectCurrentAuthenticateStep,
  selectIsAuthenticatePending,
  selectIsAuthenticateRejected,
  selectIsNotAllowedEmail,
} from '@/store/selectors/authenticate';

import { neverReached } from '@/utils/never-reached';

import useInput from '@/components/common/hooks/useInput';
import Anchor from '@/components/common/Anchor';

import SignIn from '@/components/Login/SignIn';
import SignUp from '@/components/Login/SignUp';
import Verify from '@/components/Login/Verify';

const Login: React.FC = () => {
  const [email, setEmail] = useInput();
  const [firstName, setFirstName] = useInput();
  const [lastName, setLastName] = useInput();
  const [otp, setOtp] = useInput();

  const isLoggedIn = useSelector(selectIsUserLoggedIn);
  const currentAuthenticateStep = useSelector(selectCurrentAuthenticateStep);
  const isAuthenticatePending = useSelector(selectIsAuthenticatePending);
  const isAuthenticateRejected = useSelector(selectIsAuthenticateRejected);
  const isNotAllowedEmail = useSelector(selectIsNotAllowedEmail);
  const isUserPending = useSelector(selectIsUserPending);

  const dispatch = useDispatch();

  useEffect(() => {
    if (otp.length === 6) {
      dispatch(verifyAsync(email, otp));
    }
  }, [otp]);

  const handleSignInSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    dispatch(signInAsync(email));
  };

  const handleSignUpSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    dispatch(signUpAsync(email, firstName, lastName));
  };

  const handleVerifySubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    dispatch(verifyAsync(email, otp));
  };

  const handleSendAnotherCodeClick = () => {
    dispatch(signInAsync(email));
  };

  const handleUseDifferentEmailClick = () => {
    dispatch(authenticateActions.reset());
  };

  const renderStep = () => {
    const isLoading = isUserPending || isAuthenticatePending;

    switch (currentAuthenticateStep) {
      case AuthenticateSteps.signIn:
        return (
          <SignIn
            handleFormSubmit={handleSignInSubmit}
            isAuthenticatePending={isLoading}
            isAuthenticateRejected={isAuthenticateRejected}
            email={email}
            setEmail={setEmail}
          />
        );
      case AuthenticateSteps.signUp:
        return (
          <SignUp
            handleFormSubmit={handleSignUpSubmit}
            isAuthenticatePending={isLoading}
            isAuthenticateRejected={isAuthenticateRejected}
            email={email}
            setEmail={setEmail}
            firstName={firstName}
            setFirstName={setFirstName}
            lastName={lastName}
            setLastName={setLastName}
            isNotAllowedEmail={isNotAllowedEmail}
          />
        );
      case AuthenticateSteps.verify:
        return (
          <Verify
            handleFormSubmit={handleVerifySubmit}
            isAuthenticatePending={isLoading}
            isAuthenticateRejected={isAuthenticateRejected}
            otp={otp}
            setOtp={setOtp}
            handleSendAnotherCodeClick={handleSendAnotherCodeClick}
            handleUseDifferentEmailClick={handleUseDifferentEmailClick}
          />
        );
      default:
        neverReached(currentAuthenticateStep);
        return null;
    }
  };

  if (isLoggedIn) return <Redirect to="/processes" />;

  return (
    <LoginContainerStyled>
      {renderStep()}

      <LoginFooterStyled>
        <LoginInfoStyled>
          Having trouble signing in?
          {' '}
          <Anchor href="mailto:support@ta.com">Contact us</Anchor>
        </LoginInfoStyled>

        <NavStyled>
          <NavLink to="/privacy-policy">privacy policy</NavLink>
          <NavLink to="/terms-of-use">terms and conditions</NavLink>
          <NavLink to="/disclaimer">disclaimer</NavLink>
        </NavStyled>
      </LoginFooterStyled>
    </LoginContainerStyled>
  );
};

const LoginContainerStyled = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 40px 0px 20px;
`;

const LoginFooterStyled = styled.div`
  margin-top: 20px;
`;

const LoginInfoStyled = styled.div`
  text-align: center;
`;

const NavStyled = styled.nav`
  display: flex;
  justify-content: center;
  margin: 12px auto;
`;

const NavLink = styled(Link)`
  text-transform: uppercase;
  color: #83839c;
  padding: 8px 16px;
  text-decoration: none;

  &:hover {
    color: #f36621;
  }
`;

export default Login;
