import axios from "axios";

const instance = axios.create({
  headers: {
    Accept: "application/json",
  },
});

instance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response.status === 401) {
      window.location = "/admin/login";
    }
    return Promise.reject(error);
  }
);

function parseLinkHeader(response) {
  const link = response.headers?.link;
  if (link) {
    const linkRe = /<([^>]+)>; rel="([^"]+)"/g;
    const urls = {};
    let m;
    while ((m = linkRe.exec(link)) !== null) {
      let url = m[1];
      urls[m[2]] = url;
    }
    return urls;
  }
  return null;
}

const Api = {
  parseLinkHeader,
  admin: {
    me() {
      return instance.get("/api/admin/me");
    },
    home() {
      return instance.get("/api/admin/home");
    },
    homeUsersDaily({ contest_id, start_date, end_date }) {
      return instance.get("/api/admin/home/users/daily", {
        params: { contest_id, start_date, end_date },
      });
    },
    homeUsersCumulative({ contest_id, start_date, end_date }) {
      return instance.get("/api/admin/home/users/cumulative", {
        params: { contest_id, start_date, end_date },
      });
    },
    homeStepsDaily({ contest_id, start_date, end_date }) {
      return instance.get("/api/admin/home/steps/daily", {
        params: { contest_id, start_date, end_date },
      });
    },
    homeStepsCumulative({ contest_id, start_date, end_date }) {
      return instance.get("/api/admin/home/steps/cumulative", {
        params: { contest_id, start_date, end_date },
      });
    },
    homeDistanceDaily({ contest_id, start_date, end_date }) {
      return instance.get("/api/admin/home/distance/daily", {
        params: { contest_id, start_date, end_date },
      });
    },
    homeDistanceCumulative({ contest_id, start_date, end_date }) {
      return instance.get("/api/admin/home/distance/cumulative", {
        params: { contest_id, start_date, end_date },
      });
    },
    homeUsersByAgeGroup({ contest_id, age_min, age_max }) {
      return instance.get("/api/admin/users/age/between", {
        params: { contest_id, age_min, age_max }
      });
    },
    homeUsersByAgeGroupDates({ start_date, end_date, age_min, age_max }) {
      return instance.get("/api/admin/users/age/between/dates", {
        params: { start_date, end_date, age_min, age_max }
      });
    },
    contests() {
      return instance.get("/api/admin/contests");
    },
    users({ contest_id, is_tester, order_by, query, page }) {
      return instance.get("/api/admin/users", {
        params: { contest_id, is_tester, order_by, query, page },
      });
    },
    usersByZip({ contest_id, is_tester }) {
      return instance.get("/api/admin/users/zip", {
        params: { contest_id, is_tester },
      });
    },
    usersByZipActive({ contest_id, is_tester }) {
      return instance.get("/api/admin/users/zip/active", {
        params: { contest_id, is_tester },
      });
    },
    usersByZipMedianSteps({ contest_id, is_tester }) {
      return instance.get("/api/admin/users/zip/steps", {
        params: { contest_id, is_tester },
      });
    },
  },
  static: {
    map() {
      return instance.get("/static/home/SanFrancisco.Neighborhoods.json");
    },
  },
};

export default Api;
