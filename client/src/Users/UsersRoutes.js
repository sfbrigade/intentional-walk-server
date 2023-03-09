import { Route, Routes } from "react-router-dom";

import UsersList from "./UsersList";

function UsersRoutes() {
  return (
    <Routes>
      <Route path="" element={<UsersList />} />
    </Routes>
  );
}

export default UsersRoutes;
