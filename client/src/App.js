import { Route, BrowserRouter as Router, Routes } from "react-router-dom";

import "./App.css";
import { AuthContextProvider, AuthProtected } from "./AuthContext";
import Navbar from "./Navbar";
import Home from "./Home";
import Login from "./Login";
import UsersRoutes from "./Users/UsersRoutes";

function App() {
  return (
    <AuthContextProvider>
      <Router>
        <Navbar />
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/"
            element={
              <AuthProtected>
                <Home />
              </AuthProtected>
            }
          />
          <Route
            path="/users/*"
            element={
              <AuthProtected>
                <UsersRoutes />
              </AuthProtected>
            }
          />
        </Routes>
      </Router>
    </AuthContextProvider>
  );
}

export default App;
