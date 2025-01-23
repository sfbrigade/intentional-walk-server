import { Route, Routes } from 'react-router';

import { AuthContextProvider, AuthProtected } from './AuthContext';
import Navigation from './Navigation';
import Home from './Home';
import Login from './Login';
import UsersRoutes from './Users/UsersRoutes';

function App () {
  return (
    <>
      <AuthContextProvider>
        <Navigation />
        <Routes>
          <Route path='/login' element={<Login />} />
          <Route
            path='/'
            element={
              <AuthProtected>
                <Home />
              </AuthProtected>
            }
          />
          <Route
            path='/users/*'
            element={
              <AuthProtected>
                <UsersRoutes />
              </AuthProtected>
            }
          />
        </Routes>
      </AuthContextProvider>
    </>
  );
}

export default App;
