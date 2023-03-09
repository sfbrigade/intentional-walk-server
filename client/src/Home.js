import { useEffect, useState } from "react";
import numeral from "numeral";

import "./Home.scss";
import Api from "./Api";

function Home() {
  const [data, setData] = useState();

  useEffect(() => {
    let cancelled = false;
    Api.admin.home().then((response) => !cancelled && setData(response.data));
    return () => (cancelled = true);
  }, []);

  return (
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
  );
}
export default Home;
