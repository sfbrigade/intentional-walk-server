import { useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router';

import { useAuthContext } from './AuthContext';

function Login () {
  const authContext = useAuthContext();
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    if (authContext.user) {
      navigate(location.state?.from || '/', { replace: true });
    }
  }, [authContext.user, location, navigate]);

  return (
    <div className='container d-flex h-100 justify-content-center'>
      <div className='row h-100 mt-5'>
        <h1>
          Please <a href='/admin/login'>Login</a> to view the page
        </h1>
      </div>
    </div>
  );
}
export default Login;
