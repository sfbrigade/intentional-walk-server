import classNames from "classnames";

import "./OrderBy.scss";

function OrderBy({ children, currentValue, onChange, value }) {
  const isAscending = currentValue === value;
  const isDescending = currentValue === `-${value}`;

  function onClick() {
    if (isAscending) {
      onChange(`-${value}`);
    } else {
      onChange(value);
    }
  }

  return (
    <button
      className={classNames("order-by btn btn-link", {
        "order-by--ascending": isAscending,
        "order-by--descending": isDescending,
      })}
      onClick={onClick}
    >
      {children}
    </button>
  );
}

export default OrderBy;
