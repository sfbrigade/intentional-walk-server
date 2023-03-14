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
    homeStepsDaily({ start_date, end_date }) {
      return instance.get("/api/admin/home/steps/daily", {
        params: { start_date, end_date },
      });
    },
    homeStepsCumulative({ start_date, end_date }) {
      return instance.get("/api/admin/home/steps/cumulative", {
        params: { start_date, end_date },
      });
    },
    homeDistanceDaily({ start_date, end_date }) {
      return instance.get("/api/admin/home/distance/daily", {
        params: { start_date, end_date },
      });
    },
    homeDistanceCumulative({ start_date, end_date }) {
      return instance.get("/api/admin/home/distance/cumulative", {
        params: { start_date, end_date },
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
    usersDaily({ start_date, end_date }) {
      return instance.get("/api/admin/users/daily", {
        params: { start_date, end_date },
      });
    },
    usersCumulative({ start_date, end_date }) {
      return instance.get("/api/admin/users/cumulative", {
        params: { start_date, end_date },
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
