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
    contests() {
      return instance.get("/api/admin/contests");
    },
    users({ contest_id, page }) {
      return instance.get("/api/admin/users", { params: { contest_id, page } });
    },
  },
};

export default Api;
