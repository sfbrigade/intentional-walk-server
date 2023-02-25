import { useEffect, useState } from "react";
import { useLocation } from "react-router";
import { DateTime } from "luxon";

import Api from "../Api";
import Pagination from "../Components/Pagination";

import "./UsersList.scss";

function UsersList() {
  const { search } = useLocation();
  const params = new URLSearchParams(search);

  const page = parseInt(params.get("page") ?? "1", 10);
  const [lastPage, setLastPage] = useState();

  const [users, setUsers] = useState();

  useEffect(() => {
    let cancelled = false;
    Api.admin.users({ page }).then((response) => {
      if (cancelled) {
        return;
      }
      setUsers(response.data);
      const linkHeader = Api.parseLinkHeader(response);
      let newLastPage = page;
      if (linkHeader?.last) {
        const match = linkHeader.last.match(/page=(\d+)/);
        newLastPage = parseInt(match[1], 10);
      } else if (linkHeader?.next) {
        newLastPage = page + 1;
      }
      setLastPage(newLastPage);
    });
    return () => (cancelled = true);
  }, [page]);

  return (
    <div className="users-list container-fluid">
      <div className="row my-5">
        <div className="col"></div>
        <div className="col">
          <h2 className="users-list__title">All users</h2>
        </div>
        <div className="col"></div>
      </div>
      <div className="table-responsive">
        <table className="users-list__table table table-striped">
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Age</th>
              <th>Zip</th>
              <th>Sign up Date</th>
              <th>Daily Walks</th>
              <th>Total Steps</th>
              <th>Total Dist (mi)</th>
            </tr>
          </thead>
          <tbody>
            {!users && (
              <tr>
                <td colSpan={8}>Loading...</td>
              </tr>
            )}
            {users?.map((u) => (
              <tr key={u.id}>
                <td>{u.name}</td>
                <td>{u.email}</td>
                <td>{u.age}</td>
                <td>{u.zip}</td>
                <td>{DateTime.fromISO(u.created).toLocaleString(DateTime.DATE_MED)}</td>
                <td></td>
                <td></td>
                <td></td>
              </tr>
            ))}
          </tbody>
        </table>
        <Pagination page={page} lastPage={lastPage} />
      </div>
    </div>
  );
}
export default UsersList;
