import { useEffect } from "react";
import { Link } from "react-router-dom";

import Api from "./Api";
import "./Navigation.scss";
import { useAuthContext } from "./AuthContext";

function Navigation() {
  const { user, setUser } = useAuthContext();

  useEffect(() => {
    Api.admin
      .me()
      .then((response) => {
        if (response.status === 204) {
          setUser(null);
        } else {
          setUser(response.data);
        }
      })
      .catch(() => setUser(null));
  }, [setUser]);

  return (
    <nav
      className="navigation navbar navbar-expand-md navbar-light bg-light"
      aria-label="Navigation"
    >
      <div className="container-fluid">
        <Link className="navbar-brand" to="/">
          Intentional Walk
        </Link>
        <button
          className="navbar-toggler"
          type="button"
          aria-controls="navbar"
          aria-expanded="false"
          aria-label="Toggle navigation"
        >
          <span className="navbar-toggler-icon"></span>
        </button>
        <div className="navigation__links collapse navbar-collapse" id="navbar">
          <ul className="navbar-nav mb-2 mb-md-0">
            <li className="nav-item">
              <Link className="nav-link" to="/">
                Home
              </Link>
            </li>
            {user && (
              <>
                <li className="nav-item">
                  <Link className="nav-link" to="/users">
                    Users
                  </Link>
                </li>
                <li className="nav-item">
                  <a className="nav-link" href="/admin/logout">
                    Log out
                  </a>
                </li>
              </>
            )}
            {!user && (
              <>
                <li className="nav-item">
                  <Link className="nav-link" to="/login">
                    Log in
                  </Link>
                </li>
              </>
            )}
          </ul>
        </div>
      </div>
    </nav>
  );
}
export default Navigation;
