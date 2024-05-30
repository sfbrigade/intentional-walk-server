

import { useEffect, useState } from "react";
import { Chart } from "react-google-charts";
import Api from "../Api";
import Loading from "./Loader";
import ErrorTryAgainLater from "./ErrorTryAgainLater";

function Histogram({
    // query
    contest_id,
    start_date,
    end_date,
    bin_size,
    bin_count,
    bin_custom,
    field,
    path,
    // props
    options,
    width,
    height,
}) {
    const [resp, setResp] = useState({
        data: [],
        unit: "",
    })
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState()
    useEffect(() => {
        let cancelled = false;
        setLoading(true);
        setError(null);
        const fetchHistogram = async () => {
            try {
                const response = await Api.admin.histogram({
                    contest_id,
                    start_date,
                    end_date,
                    field,
                    path,
                    bin_size,
                    bin_count,
                    bin_custom,
                });
                const { data, unit } = response.data;
                if (!cancelled) {
                    setResp({
                        data: transform(data, field),
                        unit,
                        bin_size,
                    });
                }
            } catch (error) {
                !cancelled && setError(error)
            } finally {
                !cancelled && setLoading(false);
            }
        };
        fetchHistogram();
        return () => void (cancelled = true);
    }, [
        contest_id,
        start_date,
        end_date,
        bin_size,
        bin_count,
        bin_custom,
        field,
        path,
    ])
    if (error) {
        return <ErrorTryAgainLater error={error} width={width} height={height} />
    }
    if (loading) {
        return <Loading width={width} height={height} />
    }
    return (
        <>
            <h3>{pathToTitle(path, field, resp.unit)}</h3>

            {
                // The header is the first entry, the rest are 
                // the bins. This indicates that there is data. 
                (resp.data.length > 1) ? <Chart
                    // Because we have pre-binned data.
                    chartType="ColumnChart"
                    data={resp.data}
                    options={options}
                    width={width}
                    height={height}
                /> : <p>No data available.</p>}
        </>
    );
};

const transform = (data, field) => {
    // Display a cutoff for the last bin,
    // since the last bin is the upper limit.
    const lastIdx = data.length - 1;
    return [
        [capitalize(field), "Count"],
        ...data.map(
            ({ bin_start, bin_end, count }, i) => [
                // Subtract by 1 at the end since the ranges are exclusive, and we want to
                // display them as inclusive.
                (i !== lastIdx) ? `${bin_start}-${bin_end - 1}` : `>${bin_start}`,
                count,
            ])
    ]
}

const capitalize = (str) => {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

const pathToTitle = (path, field, unit) => {
    switch (path) {
        case "intentionalwalk":
            return `Intentional Walk (${unit})`;
        case "users":
            return `User ${field} (${unit})`;
        case "dailywalk":
            return `Daily Walk (${unit})`;
        case "leaderboard":
            return `Leaderboard (${unit})`;
        default:
            return `${capitalize(path)} ${field} (${unit})`;
    }
}

export default Histogram;