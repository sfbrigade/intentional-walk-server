import classNames from "classnames";
import { Link } from "react-router";

function Pagination({ page, lastPage, otherParams = {} }) {
  function onClick() {
    window.scrollTo(0, 0);
  }
  return (
    <nav>
      <ul className="pagination justify-content-center">
        <li className={classNames("page-item", { disabled: page === 1 })}>
          {page > 2 && (
            <Link
              to={`?${new URLSearchParams({ ...otherParams, page: page - 1 })}`}
              onClick={onClick}
              className="page-link"
            >
              Prev
            </Link>
          )}
          {page === 2 && (
            <Link
              to={`?${new URLSearchParams(otherParams)}`}
              onClick={onClick}
              className="page-link"
            >
              Prev
            </Link>
          )}
          {page === 1 && <span className="page-link">Prev</span>}
        </li>
        {page > 1 && (
          <li className="page-item">
            <Link
              to={`?${new URLSearchParams(otherParams)}`}
              onClick={onClick}
              className="page-link"
            >
              1
            </Link>
          </li>
        )}
        {page - 3 >= 2 && (
          <li className="page-item disabled">
            <span className="page-link">&hellip;</span>
          </li>
        )}
        {page === 4 && (
          <li className="page-item">
            <Link
              to={`?${new URLSearchParams({ ...otherParams, page: 2 })}`}
              onClick={onClick}
              className="page-link"
            >
              2
            </Link>
          </li>
        )}
        {page > 2 && (
          <li className="page-item">
            <Link
              to={`?${new URLSearchParams({ ...otherParams, page: page - 1 })}`}
              onClick={onClick}
              className="page-link"
            >
              {page - 1}
            </Link>
          </li>
        )}
        <li className="page-item active" aria-current="page">
          <span className="page-link">{page}</span>
        </li>
        {page < lastPage && (
          <li className="page-item">
            <Link
              to={`?${new URLSearchParams({ ...otherParams, page: page + 1 })}`}
              onClick={onClick}
              className="page-link"
            >
              {page + 1}
            </Link>
          </li>
        )}
        {page + 2 === lastPage - 1 && (
          <li className="page-item">
            <Link
              to={`?${new URLSearchParams({ ...otherParams, page: page + 2 })}`}
              onClick={onClick}
              className="page-link"
            >
              {page + 2}
            </Link>
          </li>
        )}
        {lastPage - (page + 1) > 2 && (
          <li className="page-item disabled">
            <span className="page-link">&hellip;</span>
          </li>
        )}
        {page < lastPage - 1 && (
          <li className="page-item">
            <Link
              to={`?${new URLSearchParams({ ...otherParams, page: lastPage })}`}
              onClick={onClick}
              className="page-link"
            >
              {lastPage}
            </Link>
          </li>
        )}
        <li
          className={classNames("page-item", { disabled: page === lastPage })}
        >
          {page < lastPage && (
            <Link
              to={`?${new URLSearchParams({ ...otherParams, page: page + 1 })}`}
              onClick={onClick}
              className="page-link"
            >
              Next
            </Link>
          )}
          {page === lastPage && <span className="page-link">Next</span>}
        </li>
      </ul>
    </nav>
  );
}
export default Pagination;
