import React from 'react';
import { Helmet } from 'react-helmet';
import { Switch, Route, Redirect } from 'react-router-dom';
import { createGlobalStyle } from 'styled-components';
import { normalize } from 'styled-normalize';

import store from '@/store';
import { restoreAuthenticateAsync } from '@/store/actions/authenticate';

import ProtectedRouter from '@/components/common/ProtectedRouter';

import Login from './Login';
import Processes from './Processes';
import ProcessDetails from './ProcessDetails';
import PrivacyPolicy from './PrivacyPolicy';
import TermsOfUse from './TermsOfUse';
import Disclaimer from './Disclaimer';
import NotFound from './NotFound';

const GlobalStyle = createGlobalStyle`
  ${normalize};

  * {
    box-sizing: border-box;
    font-family: 'Roboto', sans-serif;
  }

  body {
    background-color: #fbfbfb;
    font-weight: 400;
    line-height: 1.5;
    color: #212529;
    font-size: 16px;
  }
`;

store.dispatch<any>(restoreAuthenticateAsync());

const App: React.FC = () => (
  <>
    <GlobalStyle />

    <Helmet titleTemplate="%s - TA" defaultTitle="TA">
      <meta name="description" content="TA" />
    </Helmet>

    <Switch>
      <Redirect from="/" to="/login" exact />
      <Route path="/login" component={Login} exact />
      <ProtectedRouter path="/processes" component={Processes} exact />
      <ProtectedRouter path="/processes/:id" component={ProcessDetails} exact />
      <Route path="/privacy-policy" component={PrivacyPolicy} exact />
      <Route path="/terms-of-use" component={TermsOfUse} exact />
      <Route path="/disclaimer" component={Disclaimer} exact />
      <Route component={NotFound} />
    </Switch>
  </>
);

export default App;
