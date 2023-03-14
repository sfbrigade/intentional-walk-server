import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router";
import { Chart } from "react-google-charts";
import numeral from "numeral";

import "./Home.scss";
import Api from "./Api";

function Home() {
  const { search } = useLocation();
  const navigate = useNavigate();
  const params = new URLSearchParams(search);

  const start_date = params.get("start_date") ?? "";
  const end_date = params.get("end_date") ?? "";

  const [newStartDate, setNewStartDate] = useState(start_date);
  const [newEndDate, setNewEndDate] = useState(end_date);

  const [data, setData] = useState();

  const [usersDaily, setUsersDaily] = useState();
  const [usersCumulative, setUsersCumulative] = useState();
  const [stepsDaily, setStepsDaily] = useState();

  useEffect(() => {
    let cancelled = false;
    Api.admin.home().then((response) => !cancelled && setData(response.data));
  }, []);

  useEffect(() => {
    let cancelled = false;
    Api.admin
      .usersDaily({ start_date, end_date })
      .then(
        (response) =>
          !cancelled &&
          setUsersDaily(response.data.map((r) => [new Date([r[0]]), r[1]]))
      );
    Api.admin
      .usersCumulative({ start_date, end_date })
      .then(
        (response) =>
          !cancelled &&
          setUsersCumulative(response.data.map((r) => [new Date([r[0]]), r[1]]))
      );
    Api.admin
      .homeStepsDaily({ start_date, end_date })
      .then(
        (response) =>
          !cancelled &&
          setStepsDaily(response.data.map((r) => [new Date([r[0]]), r[1]]))
      );
    return () => (cancelled = true);
  }, [start_date, end_date]);

  function onChangeStartDate(event) {
    setNewStartDate(event.target.value);
  }

  function onChangeEndDate(event) {
    setNewEndDate(event.target.value);
  }

  function onUpdateGraphs() {
    const params = [];
    if (newStartDate) {
      params.push(["start_date", newStartDate]);
    }
    if (newEndDate) {
      params.push(["end_date", newEndDate]);
    }
    navigate(
      params.length > 0 ? `?${new URLSearchParams(params).toString()}` : ""
    );
  }

  return (
    <>
      <div className="home container text-center my-5">
        <h1>
          <span className="home__users">
            {data?.accounts_count
              ? numeral(data.accounts_count).format("0,0")
              : "__________"}{" "}
            users
          </span>{" "}
          have walked&nbsp;
          <span className="home__steps">
            {data?.accounts_steps
              ? numeral(data.accounts_steps / 1000000).format("0,0.0")
              : "__________"}{" "}
            million steps
          </span>{" "}
          /&nbsp;
          <span className="home__distance">
            {data?.accounts_distance
              ? numeral(data.accounts_distance / 1609).format("0,0.0")
              : "__________"}{" "}
            miles
          </span>{" "}
          so far...
        </h1>
      </div>
      <div className="container-fluid">
        <div className="bg-light py-4">
          <h2 className="text-center">Overall Trends</h2>
          <div className="d-flex justify-content-center">
            <label className="col-form-label me-2" htmlFor="start_date">
              Start Date:
            </label>
            <input
              value={newStartDate}
              onChange={onChangeStartDate}
              id="start_date"
              type="date"
              className="form-control w-auto me-3"
            />
            <label className="col-form-label me-2" htmlFor="end_date">
              End Date:
            </label>
            <input
              value={newEndDate}
              onChange={onChangeEndDate}
              id="end_date"
              type="date"
              className="form-control w-auto me-3"
            />
            <button
              onClick={onUpdateGraphs}
              type="button"
              className="btn btn-secondary"
            >
              Update Graphs
            </button>
          </div>
        </div>
        <div className="row my-5">
          <div className="col-lg-6 text-center">
            <h3>Signups (per day)</h3>
            {usersDaily && (
              <Chart
                chartType="ColumnChart"
                data={usersDaily}
                options={{
                  legend: { position: "none" },
                  bar: { groupWidth: "95%" },
                  vAxis: {
                    title: "Daily signups",
                    viewWindow: { min: 0 },
                  },
                  colors: ["#E59866"],
                }}
                width="100%"
                height="400px"
              />
            )}
          </div>
          <div className="col-lg-6 text-center">
            <h3>Signups (total)</h3>
            {usersCumulative && (
              <Chart
                chartType="LineChart"
                data={usersCumulative}
                options={{
                  legend: { position: "none" },
                  bar: { groupWidth: "95%" },
                  vAxis: {
                    title: "Total signups",
                    viewWindow: { min: 0 },
                  },
                  colors: ["#E59866"],
                }}
                width="100%"
                height="400px"
              />
            )}
          </div>
        </div>
        <div className="row my-5">
          <div className="col-lg-6 text-center">
            <h3>Steps (per day)</h3>
            {stepsDaily && (
              <Chart
                chartType="ColumnChart"
                data={stepsDaily}
                options={{
                  legend: { position: "none" },
                  bar: { groupWidth: "95%" },
                  vAxis: {
                    title: "Steps",
                    viewWindow: { min: 0 },
                  },
                  colors: ["#2ECC71"],
                }}
                width="100%"
                height="400px"
              />
            )}
          </div>
          <div className="col-lg-6 text-center">
            <h3>Steps (total)</h3>
          </div>
        </div>
        <div className="row my-5">
          <div className="col-lg-6 text-center">
            <h3>Miles (per day)</h3>
          </div>
          <div className="col-lg-6 text-center">
            <h3>Miles (total)</h3>
          </div>
        </div>
      </div>
    </>
  );
}
export default Home;
