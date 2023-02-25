import { Link } from "react-router-dom";

import { useAuthContext } from "./AuthContext";

function Home() {
  const { user } = useAuthContext();
  return (
    <>
      {!user && (
        <div class="container d-flex h-100 justify-content-center">
          <div class="row h-100 mt-5">
            <h1>
              Please <a href="/admin/login">Login</a> to view the page
            </h1>
          </div>
        </div>
      )}
    </>
  );
}
export default Home;
