import React, { useEffect } from 'react';
import { Provider, useDispatch } from 'react-redux';
import { createStore, combineReducers, applyMiddleware } from 'redux';
import KeplerGl from '@kepler.gl/components';
import { addDataToMap } from '@kepler.gl/actions';
import keplerGlReducer from '@kepler.gl/reducers';
import { enhanceReduxMiddleware } from '@kepler.gl/reducers';

// Create Redux store with kepler.gl reducer
const reducers = combineReducers({
  keplerGl: keplerGlReducer
});

const middlewares = enhanceReduxMiddleware([]);
const store = createStore(reducers, {}, applyMiddleware(...middlewares));

// Inner component that dispatches data
function KeplerMapContent({ datasets, config, mapboxToken }) {
  const dispatch = useDispatch();

  useEffect(() => {
    if (datasets && datasets.length > 0) {
      dispatch(
        addDataToMap({
          datasets,
          config: config || {},
          options: {
            centerMap: true,
            readOnly: false
          }
        })
      );
    }
  }, [datasets, config, dispatch]);

  return (
    <KeplerGl
      id="map"
      mapboxApiAccessToken={mapboxToken || ''}
      width={window.innerWidth}
      height={window.innerHeight}
    />
  );
}

// Main component with Provider
export default function KeplerMap({ datasets, config, mapboxToken }) {
  return (
    <Provider store={store}>
      <KeplerMapContent datasets={datasets} config={config} mapboxToken={mapboxToken} />
    </Provider>
  );
}
