const { createProxyMiddleware } = require("http-proxy-middleware");

module.exports = function (app) {
  app.use(
    ["/admin", "/api", "/static/home", "/static/admin"],
    createProxyMiddleware({
      target: "http://127.0.0.1:8000",
      changeOrigin: true,
    })
  );
};
