import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router";
import { DateTime } from "luxon";
import numeral from "numeral";

import Api from "../Api";
import BarChart from "../Components/BarChart";
import IntensityMap from "../Components/IntensityMap";
import OrderBy from "../Components/OrderBy";
import Pagination from "../Components/Pagination";

import "./UsersList.scss";

function UsersList() {
  const { search } = useLocation();
  const navigate = useNavigate();
  const params = new URLSearchParams(search);

  const page = parseInt(params.get("page") ?? "1", 10);
  const [lastPage, setLastPage] = useState();

  const is_tester = params.get("is_tester") === "true";

  const contest_id = params.get("contest_id") ?? "";
  const [contests, setContests] = useState();

  const order_by = params.get("order_by") ?? "name";

  const query = params.get("query") ?? "";
  const [newQuery, setNewQuery] = useState(query);
  const [queryDebounceTimerId, setQueryDebounceTimerId] = useState();

  const [contest, setContest] = useState();
  const [users, setUsers] = useState();

  const [map, setMap] = useState();
  const [usersByZip, setUsersByZip] = useState();
  const [usersByZipActive, setUsersByZipActive] = useState();
  const [usersByZipMedianSteps, setUsersByZipMedianSteps] = useState();
  const [selectedFeature, setSelectedFeature] = useState();

  useEffect(() => {
    let cancelled = false;
    Api.admin
      .contests()
      .then((response) => !cancelled && setContests(response.data));
    Api.static
      .map()
      .then((response) => !cancelled && setMap(response.data?.features));
    return () => (cancelled = true);
  }, []);

  useEffect(() => {
    setContest(contests?.find((c) => c.contest_id === contest_id));
  }, [contests, contest_id]);

  useEffect(() => {
    let cancelled = false;
    setUsers();
    Api.admin
      .users({ contest_id, is_tester, order_by, query, page })
      .then((response) => {
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
  }, [contest_id, is_tester, order_by, query, page]);

  useEffect(() => {
    let cancelled = false;
    if (contest_id) {
      setUsersByZip();
      setUsersByZipActive();
      setUsersByZipMedianSteps();
      Api.admin
        .usersByZip({ contest_id, is_tester })
        .then((response) => !cancelled && setUsersByZip(response.data));
      Api.admin
        .usersByZipActive({ contest_id, is_tester })
        .then((response) => !cancelled && setUsersByZipActive(response.data));
      Api.admin
        .usersByZipMedianSteps({ contest_id, is_tester })
        .then(
          (response) => !cancelled && setUsersByZipMedianSteps(response.data)
        );
    }
    return () => (cancelled = true);
  }, [contest_id, is_tester]);

  function onChange(contest_id, is_tester, order_by, query) {
    const params = [];
    if (contest_id) {
      params.push(["contest_id", contest_id]);
    }
    if (is_tester) {
      params.push(["is_tester", "true"]);
    }
    if (order_by !== "name") {
      params.push(["order_by", order_by]);
    }
    if (query) {
      params.push(["query", query]);
    }
    navigate(
      params.length > 0 ? `?${new URLSearchParams(params).toString()}` : ""
    );
  }

  function onChangeContest(event) {
    onChange(event.target.value, is_tester, order_by, query);
  }

  function onChangeShow(event) {
    onChange(contest_id, event.target.value === "true", order_by, query);
  }

  function onChangeOrder(newOrderBy) {
    onChange(contest_id, is_tester, newOrderBy, query);
  }

  function onChangeQuery(event) {
    if (queryDebounceTimerId) {
      clearTimeout(queryDebounceTimerId);
    }
    setNewQuery(event.target.value);
    setQueryDebounceTimerId(
      setTimeout(
        () => onChange(contest_id, is_tester, order_by, event.target.value),
        300
      )
    );
  }

  function onMouseOverZip(feature) {
    setSelectedFeature(feature);
  }

  let totalUsers;
  let totalUsersData;
  let totalNewUsers;
  if (usersByZip) {
    totalUsers = Object.values(usersByZip.total).reduce((a, b) => a + b, 0);
    totalNewUsers = Object.values(usersByZip.new).reduce((a, b) => a + b, 0);
    totalUsersData = [
      { label: "Prev", value: totalUsers - totalNewUsers },
      { label: "New", value: totalNewUsers },
    ];
  }

  let totalActiveUsers;
  let totalActiveUsersData;
  let totalNewActiveUsers;
  if (usersByZipActive) {
    totalActiveUsers = Object.values(usersByZipActive.total).reduce(
      (a, b) => a + b,
      0
    );
    totalNewActiveUsers = Object.values(usersByZipActive.new).reduce(
      (a, b) => a + b,
      0
    );
    totalActiveUsersData = [
      { label: "Prev", value: totalActiveUsers - totalNewActiveUsers },
      { label: "New", value: totalNewActiveUsers },
    ];
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
              className="form-select w-auto me-3"
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
            <label className="col-form-label me-2" htmlFor="is_tester">
              Show:
            </label>
            <select
              value={is_tester}
              onChange={onChangeShow}
              className="form-select w-auto"
              id="is_tester"
            >
              <option value={false}>Users</option>
              <option value={true}>Testers</option>
            </select>
          </div>
        </div>
        <div className="col-md">
          <div className="d-flex justify-content-end">
            {contest && (
              <a
                href={`/api/export/users?contest_id=${contest.contest_id}&is_tester=${is_tester}`}
                className="btn btn-outline-primary"
              >
                Download as CSV
              </a>
            )}
          </div>
        </div>
      </div>
      {contest && (
        <>
          <div className="row mb-5">
            <div className="col-lg-3 offset-lg-2">
              <IntensityMap
                data={usersByZip?.total}
                map={map}
                onMouseOver={onMouseOverZip}
                minColor="#eeeeee"
                maxColor="#702b84"
                width={380}
                height={300}
              />
              <h5 className="text-center">Users by Zip</h5>
            </div>
            <div className="col-lg-2">
              <h4>
                {!selectedFeature && "San Franciso"}
                {selectedFeature &&
                  `${selectedFeature.properties.neighborhood} (${selectedFeature.id})`}
              </h4>
              <dl className="users-list__map-legend">
                <dt>Total Users:</dt>
                <dd>
                  {usersByZip && (
                    <>
                      {!selectedFeature && (
                        <>
                          {totalUsers}&nbsp;<span>(</span>
                          {totalNewUsers}
                          <span>&nbsp;new)</span>
                        </>
                      )}
                      {selectedFeature && (
                        <>
                          {usersByZip.total[selectedFeature.id] ?? "0"}&nbsp;
                          <span>(</span>
                          {usersByZip.new[selectedFeature.id] ?? "0"}
                          <span>&nbsp;new)</span>
                        </>
                      )}
                    </>
                  )}
                </dd>
                <br />
                <dt>Active Users:</dt>
                <dd>
                  {usersByZipActive && (
                    <>
                      {!selectedFeature && (
                        <>
                          {totalActiveUsers}&nbsp;<span>(</span>
                          {totalNewActiveUsers}
                          <span>&nbsp;new)</span>
                        </>
                      )}
                      {selectedFeature && (
                        <>
                          {usersByZipActive.total[selectedFeature.id] ?? "0"}
                          &nbsp;<span>(</span>
                          {usersByZipActive.new[selectedFeature.id] ?? "0"}
                          <span>&nbsp;new)</span>
                        </>
                      )}
                    </>
                  )}
                </dd>
                <br />
                <dt>Median Steps:</dt>
                <dd>
                  {usersByZipMedianSteps &&
                    !selectedFeature &&
                    numeral(usersByZipMedianSteps.all).format("0,0")}
                  {usersByZipMedianSteps &&
                    selectedFeature &&
                    numeral(usersByZipMedianSteps[selectedFeature.id]).format(
                      "0,0"
                    )}
                </dd>
              </dl>
            </div>
            <div className="col-lg-3">
              <IntensityMap
                data={usersByZipMedianSteps}
                map={map}
                onMouseOver={onMouseOverZip}
                minColor="#eeeeee"
                maxColor="#2b388f"
                width={380}
                height={300}
              />
              <h5 className="text-center">Median Steps by Zip</h5>
            </div>
          </div>
          <div className="row mb-5">
            <div className="col-lg-3 offset-lg-2 d-flex flex-column align-items-center">
              <h4 className="text-center">
                Total Users (<b>{totalUsers}</b>)
              </h4>
              {totalUsersData && (
                <BarChart
                  data={totalUsersData}
                  width={300}
                  height={300}
                  minColor="#eeeeee"
                  maxColor="#702b84"
                />
              )}
            </div>
            <div className="col-lg-3 offset-lg-2 d-flex flex-column justify-content-center">
              <h4 className="text-center">
                Total Active Users (<b>{totalActiveUsers}</b>)
                {totalActiveUsersData && (
                  <BarChart
                    data={totalActiveUsersData}
                    width={300}
                    height={300}
                    minColor="#eeeeee"
                    maxColor="#2b388f"
                  />
                )}
              </h4>
            </div>
          </div>
        </>
      )}
      <div className="table-responsive">
        <table className="users-list__table table table-striped">
          <thead>
            <tr>
              <td colSpan={9}>
                <div className="d-flex">
                  <div className="d-flex">
                    <label className="col-form-label me-2" htmlFor="search">
                      Search:
                    </label>
                    <input
                      type="text"
                      placeholder="Name or Email..."
                      value={newQuery}
                      onChange={onChangeQuery}
                      className="form-control w-auto"
                    />
                  </div>
                </div>
              </td>
            </tr>
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
              {contest && (
                <th>
                  <OrderBy
                    value="is_new"
                    currentValue={order_by}
                    onChange={onChangeOrder}
                  >
                    Is new?
                  </OrderBy>
                </th>
              )}
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
                {contest && <td>{u.is_new ? "Yes" : "No"}</td>}
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
          otherParams={{ contest_id, order_by, is_tester, query }}
        />
      </div>
    </div>
  );
}
export default UsersList;
