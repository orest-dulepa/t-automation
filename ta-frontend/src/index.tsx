import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { Provider } from 'react-redux';
import ReactDOM from 'react-dom';
import { ConnectedRouter } from 'connected-react-router';
import 'moment-duration-format';

import store, { history } from '@/store';

import App from '@/containers/App';

ReactDOM.render(
  <BrowserRouter>
    <Provider store={store}>
      <ConnectedRouter history={history}>
        <App />
      </ConnectedRouter>
    </Provider>
  </BrowserRouter>,
  document.getElementById('root'),
);
