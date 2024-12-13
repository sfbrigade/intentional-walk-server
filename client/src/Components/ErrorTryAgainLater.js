function ErrorTryAgainLater({ error, width, height }) {
  let message = "Oops! Something went wrong. Please try again later.";
  if (error?.response?.status === 422) {
    // Likely a developer-facing error
    // As we should not be allowing free-form input
    // to our APIs.
    message = `Oops! Invalid input.`;
    console.error(error.response.data);
  }
  return (
    <div style={{ width, height }}>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          height: "100%",
        }}
      >
        <span style={{ fontSize: "24px", color: "red" }}>⚠️</span>
        <span style={{ marginLeft: "8px", fontSize: "16px" }}>{message}</span>
      </div>
    </div>
  );
}

export default ErrorTryAgainLater;
