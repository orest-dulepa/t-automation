import {
  createStore,
  applyMiddleware,
  compose,
  combineReducers,
} from 'redux';
import thunk from 'redux-thunk';
import { connectRouter, routerMiddleware } from 'connected-react-router';
import { createBrowserHistory } from 'history';

import MainApi from '@/api/MainApi';
import MainApiProtected from '@/api/MainApiProtected';

import { AuthenticateActions } from './actions/authenticate';
import { UserActions } from './actions/user';
import { AvailableProcessesActions } from './actions/available-processes';
import { RegularProcessesActions, ScheduledProcessesActions } from './actions/scheduled-processes';
import { StartProcessActions } from './actions/start-process';
import { ActiveProcessesActions } from './actions/active-processes';
import { FinishedProcessesActions } from './actions/finished-processes';
import { FiltersActions } from './actions/filters';
import { ProcessDetailsActions } from './actions/process-details';
import { CancelScheduledProcessActions } from './actions/cancel-scheduled-process';

import authenticateReducer from './reducers/authenticate';
import userReducer from './reducers/user';
import availableProcessesReducer from './reducers/available-processes';
import scheduledProcessesReducer from './reducers/scheduled-processes';
import cancelScheduledProcessReducer from './reducers/cancel-scheduled-process';
import regularProcessesReducer from './reducers/regular-processes';
import removeRegularProcessReducer from './reducers/remove-regular-process';
import startProcessReducer from './reducers/start-process';
import activeProcessesReducer from './reducers/active-processes';
import finishedProcessesReducer from './reducers/finished-processes';
import filtersReducer from './reducers/filters';
import processDetailsReducer from './reducers/process-details';
import {RemoveRegularProcessActions} from "@/store/actions/remove-regular-process";

export const history = createBrowserHistory();

export const api = {
  mainApi: MainApi.getInstance(),
  mainApiProtected: MainApiProtected.getInstance(),
};

const rootReducer = combineReducers({
  router: connectRouter(history),
  authenticateReducer,
  userReducer,
  availableProcessesReducer,
  scheduledProcessesReducer,
  cancelScheduledProcessReducer,
  regularProcessesReducer,
  removeRegularProcessReducer,
  startProcessReducer,
  activeProcessesReducer,
  finishedProcessesReducer,
  filtersReducer,
  processDetailsReducer,
});

const composeEnhancers = window.__REDUX_DEVTOOLS_EXTENSION_COMPOSE__ || compose;

const enhancer = composeEnhancers(
  applyMiddleware(routerMiddleware(history), thunk.withExtraArgument(api)),
);

export type State = ReturnType<typeof rootReducer>;
export type Actions =
  | AuthenticateActions
  | UserActions
  | AvailableProcessesActions
  | ScheduledProcessesActions
  | CancelScheduledProcessActions
  | RegularProcessesActions
  | RemoveRegularProcessActions
  | StartProcessActions
  | ActiveProcessesActions
  | FinishedProcessesActions
  | FiltersActions
  | ProcessDetailsActions;

export default createStore(rootReducer, enhancer);
