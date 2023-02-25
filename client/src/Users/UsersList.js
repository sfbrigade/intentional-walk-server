import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router";
import { DateTime } from "luxon";
import numeral from "numeral";

import Api from "../Api";
import OrderBy from "../Components/OrderBy";
import Pagination from "../Components/Pagination";

import "./UsersList.scss";

function UsersList() {
  const { search } = useLocation();
  const navigate = useNavigate();
  const params = new URLSearchParams(search);

  const page = parseInt(params.get("page") ?? "1", 10);
  const [lastPage, setLastPage] = useState();

  const contest_id = params.get("contest_id") ?? "";
  const [contests, setContests] = useState();

  const order_by = params.get("order_by") ?? "name";

  const [contest, setContest] = useState();
  const [users, setUsers] = useState();

  useEffect(() => {
    let cancelled = false;
    Api.admin
      .contests()
      .then((response) => !cancelled && setContests(response.data));
    return () => (cancelled = true);
  }, []);

  useEffect(() => {
    setContest(contests?.find((c) => c.contest_id === contest_id));
  }, [contests, contest_id]);

  useEffect(() => {
    let cancelled = false;
    setUsers();
    Api.admin.users({ contest_id, order_by, page }).then((response) => {
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
  }, [contest_id, order_by, page]);

  function onChangeContest(event) {
    const newContestId = event.target.value;
    navigate(newContestId ? `?contest_id=${newContestId}` : "");
  }

  function onChangeOrder(newOrder) {
    const params = [];
    if (newOrder !== "name") {
      params.push(["order_by", newOrder]);
    }
    if (contest_id) {
      params.push(["contest_id", contest_id]);
    }
    navigate(
      params.length > 0 ? `?${new URLSearchParams(params).toString()}` : ""
    );
  }

  return (
    <div className="users-list container-fluid">
      <div className="row my-5">
        <div className="col-md">
          <h2 className="users-list__title">
            {!contest && "All users"}
            {contest &&
              `Contest: ${DateTime.fromISO(contest.start).toLocaleString(
                DateTime.DATE_MED
              )} - ${DateTime.fromISO(contest.end).toLocaleString(
                DateTime.DATE_MED
              )}`}
          </h2>
        </div>
        <div className="col-md order-md-first">
          <div className="d-flex">
            <label className="col-form-label me-2" htmlFor="contest_id">
              Contest:
            </label>
            <select
              value={contest_id}
              onChange={onChangeContest}
              className="form-select w-auto"
              id="contest_id"
            >
              <option value="">None</option>
              {contests?.map((c) => (
                <option key={c.contest_id} value={c.contest_id}>
                  {DateTime.fromISO(c.start).toLocaleString(DateTime.DATE_MED)}{" "}
                  - {DateTime.fromISO(c.end).toLocaleString(DateTime.DATE_MED)}
                </option>
              ))}
            </select>
          </div>
        </div>
        <div className="col-md"></div>
      </div>
      <div className="table-responsive">
        <table className="users-list__table table table-striped">
          <thead>
            <tr>
              <th>&nbsp;&nbsp;&nbsp;</th>
              <th>
                <OrderBy
                  value="name"
                  currentValue={order_by}
                  onChange={onChangeOrder}
                >
                  Name
                </OrderBy>
              </th>
              <th>
                <OrderBy
                  value="email"
                  currentValue={order_by}
                  onChange={onChangeOrder}
                >
                  Email
                </OrderBy>
              </th>
              <th>
                <OrderBy
                  value="age"
                  currentValue={order_by}
                  onChange={onChangeOrder}
                >
                  Age
                </OrderBy>
              </th>
              <th>
                <OrderBy
                  value="zip"
                  currentValue={order_by}
                  onChange={onChangeOrder}
                >
                  Zip
                </OrderBy>
              </th>
              <th>
                <OrderBy
                  value="created"
                  currentValue={order_by}
                  onChange={onChangeOrder}
                >
                  Sign-up Date
                </OrderBy>
              </th>
              <th>
                <OrderBy
                  value="dw_count"
                  currentValue={order_by}
                  onChange={onChangeOrder}
                >
                  Days Walked
                </OrderBy>
              </th>
              <th>
                <OrderBy
                  value="dw_steps"
                  currentValue={order_by}
                  onChange={onChangeOrder}
                >
                  Total Steps
                </OrderBy>
              </th>
              <th>
                <OrderBy
                  value="dw_distance"
                  currentValue={order_by}
                  onChange={onChangeOrder}
                >
                  Total Dist (mi)
                </OrderBy>
              </th>
            </tr>
          </thead>
          <tbody>
            {users?.map((u, i) => (
              <tr key={u.id}>
                <td>{(page - 1) * 25 + i + 1}.</td>
                <td>{u.name}</td>
                <td>{u.email}</td>
                <td>{u.age}</td>
                <td>{u.zip}</td>
                <td>
                  {DateTime.fromISO(u.created).toLocaleString(
                    DateTime.DATE_MED
                  )}
                </td>
                <td>{u.dw_count?.toLocaleString()}</td>
                <td>{u.dw_steps?.toLocaleString()}</td>
                <td>
                  {u.dw_distance &&
                    numeral(u.dw_distance / 1609).format("0,0.0")}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <Pagination
          page={page}
          lastPage={lastPage}
          otherParams={{ contest_id, order_by }}
        />
      </div>
    </div>
  );
}
export default UsersList;
